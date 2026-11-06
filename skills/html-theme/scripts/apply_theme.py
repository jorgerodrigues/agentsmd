import argparse
from pathlib import Path
import re
import sys


ASSETS = Path(__file__).resolve().parent.parent / "assets"
MARKER = "<!-- html-theme -->"
THEME_START = "<!-- html-theme:start -->"
THEME_END = "<!-- html-theme:end -->"
ICONS_START = "<!-- html-theme-icons:start -->"
ICONS_END = "<!-- html-theme-icons:end -->"
WEB_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Geist+Mono:wght@400;500;600&family=Mona+Sans:ital,wght@0,200..900;1,200..900&display=swap">\n'
)

THEME_BLOCK = re.compile(re.escape(THEME_START) + r".*?" + re.escape(THEME_END), re.S)
ICONS_BLOCK = re.compile(r"\n?" + re.escape(ICONS_START) + r".*?" + re.escape(ICONS_END), re.S)
ICON_REF = re.compile(r'href="#i-([a-z0-9-]+)"')
SYMBOL = re.compile(r'<symbol id="i-([a-z0-9-]+)".*?</symbol>', re.S)
BODY_OPEN = re.compile(r"<body\b[^>]*>", re.I)
STYLE_BLOCK = re.compile(r"<style\b[^>]*>(.*?)</style>", re.S | re.I)
STYLE_ATTR = re.compile(r'\sstyle="([^"]*)"', re.I)
OWN_STYLE = [
    (re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab|lab|lch)\("), "a color value"),
    (re.compile(r"font-family\s*:"), "a font family"),
    (re.compile(r"font-size\s*:\s*[0-9.]+(?:px|rem|em|pt)"), "a font size"),
]


def theme_block(web_fonts):
    css = (ASSETS / "theme.css").read_text()
    fonts = WEB_FONTS if web_fonts else ""
    return f"{THEME_START}\n{fonts}<style>\n{css}</style>\n{THEME_END}"


def icons_block(names, symbols):
    body = "\n".join(symbols[name] for name in names)
    return (
        f"\n{ICONS_START}\n"
        '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">\n'
        f"{body}\n</svg>\n{ICONS_END}"
    )


def own_style_warnings(page):
    page = THEME_BLOCK.sub("", page)
    page = ICONS_BLOCK.sub("", page)
    sources = STYLE_BLOCK.findall(page) + STYLE_ATTR.findall(page)
    found = []
    for pattern, what in OWN_STYLE:
        if any(pattern.search(source) for source in sources):
            found.append(what)
    return found


def apply(page, web_fonts):
    symbols = {match.group(1): match.group(0) for match in SYMBOL.finditer((ASSETS / "icons.svg").read_text())}
    page = ICONS_BLOCK.sub("", page)

    names = list(dict.fromkeys(ICON_REF.findall(page)))
    unknown = [name for name in names if name not in symbols]
    if unknown:
        raise ValueError(
            f"Unknown icons: {', '.join(unknown)}. The theme has: {', '.join(sorted(symbols))}."
        )

    if THEME_BLOCK.search(page):
        page = THEME_BLOCK.sub(lambda _: theme_block(web_fonts), page, count=1)
    elif MARKER in page:
        page = page.replace(MARKER, theme_block(web_fonts), 1)
    else:
        raise ValueError(f"Add {MARKER} inside <head>, then run this again.")

    if names:
        body = BODY_OPEN.search(page)
        if body is None:
            raise ValueError("The page uses icons but has no <body> tag to hold them.")
        page = page[: body.end()] + icons_block(names, symbols) + page[body.end() :]
    return page, names


def main():
    parser = argparse.ArgumentParser(description="Insert the html-theme stylesheet and the icons a page uses.")
    parser.add_argument("pages", nargs="+", type=Path, metavar="PAGE", help="HTML file to update in place.")
    parser.add_argument(
        "--web-fonts",
        action="store_true",
        help="Link Mona Sans and Geist Mono from Google Fonts, for pages opened on other computers.",
    )
    args = parser.parse_args()

    try:
        for path in args.pages:
            page, names = apply(path.read_text(), args.web_fonts)
            path.write_text(page)
            icons = f"{len(names)} icons ({', '.join(names)})" if names else "no icons"
            fonts = "web fonts linked" if args.web_fonts else "installed fonts only"
            print(f"{path}: applied the theme with {icons}, {fonts}.")
            for what in own_style_warnings(page):
                print(f"{path}: warning: the page sets {what} of its own. Use the theme's tokens instead.", file=sys.stderr)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
