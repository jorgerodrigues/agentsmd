import argparse
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys


SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS = SKILL_DIR / "assets"
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
USE_TOKENS = "Use the theme's tokens instead."
OWN_STYLE = [
    (re.compile(r"#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|oklab|lab|lch)\("), f"sets a color value of its own. {USE_TOKENS}"),
    (re.compile(r"font-family\s*:"), f"sets a font family of its own. {USE_TOKENS}"),
    (re.compile(r"font-size\s*:\s*[0-9.]+(?:px|rem|em|pt)"), f"sets a font size of its own. {USE_TOKENS}"),
    (
        re.compile(r"border-(?:top|right|bottom|left|(?:inline|block)-(?:start|end))(?:-(?:color|style|width))?\s*:"),
        "puts a border on one side of a box. Use tone, a full border or a status icon instead.",
    ),
]


class CodeBlocks(HTMLParser):
    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.line_offsets = [0] + [match.end() for match in re.finditer("\n", page)]
        self.blocks = []
        self.pre_depth = 0
        self.current = None
        self.feed(page)
        self.close()
        if self.current is not None:
            raise ValueError("A code snippet has no closing </code> tag.")

    def source_offset(self):
        line, column = self.getpos()
        return self.line_offsets[line - 1] + column

    def handle_starttag(self, tag, attrs):
        if self.current is not None:
            if tag != "span":
                raise ValueError("Escape HTML inside code snippets before applying the theme.")
            return
        if tag == "pre":
            self.pre_depth += 1
        elif tag == "code" and self.pre_depth:
            classes = (dict(attrs).get("class") or "").split()
            language = next((name.removeprefix("language-") for name in classes if name.startswith("language-")), None)
            if language:
                self.current = {"start": self.source_offset() + len(self.get_starttag_text()), "language": language.lower(), "parts": []}

    def handle_data(self, data):
        if self.current is not None:
            self.current["parts"].append(data)

    def handle_comment(self, data):
        if self.current is not None:
            raise ValueError("Escape HTML inside code snippets before applying the theme.")

    def handle_endtag(self, tag):
        if tag == "code" and self.current is not None:
            self.current["end"] = self.source_offset()
            self.current["source"] = "".join(self.current.pop("parts"))
            self.blocks.append(self.current)
            self.current = None
        elif tag == "pre":
            self.pre_depth = max(0, self.pre_depth - 1)


def highlight_pages(pages):
    blocks_by_page = [CodeBlocks(page).blocks for page in pages]
    snippets = [block for blocks in blocks_by_page for block in blocks]
    if not snippets:
        return pages, [0] * len(pages)
    if not (SKILL_DIR / "node_modules" / "shiki" / "package.json").is_file():
        raise ValueError(
            f"Syntax highlighting needs Shiki. Run npm ci --prefix '{SKILL_DIR}' --ignore-scripts --no-audit --no-fund, then run this command again."
        )
    try:
        result = subprocess.run(
            ["node", str(SKILL_DIR / "scripts" / "highlight.mjs")],
            input=json.dumps([{"source": block["source"], "language": block["language"]} for block in snippets]),
            capture_output=True, text=True,
        )
    except FileNotFoundError as error:
        raise ValueError("Syntax highlighting needs Node.js 20 or later on PATH.") from error
    if result.returncode:
        raise ValueError(f"Syntax highlighting failed: {result.stderr.strip()}")
    highlighted = json.loads(result.stdout)
    for warning in highlighted["warnings"]:
        print(f"warning: {warning}", file=sys.stderr)
    output = []
    counts = []
    cursor = 0
    for page, blocks in zip(pages, blocks_by_page):
        replacements = highlighted["snippets"][cursor:cursor + len(blocks)]
        for block, replacement in reversed(list(zip(blocks, replacements))):
            page = page[:block["start"]] + replacement["html"] + page[block["end"]:]
        output.append(page)
        counts.append(sum(replacement["highlighted"] for replacement in replacements))
        cursor += len(blocks)
    return output, counts


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
    for pattern, warning in OWN_STYLE:
        if any(pattern.search(source) for source in sources):
            found.append(warning)
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
    parser = argparse.ArgumentParser(description="Apply the HTML theme, insert icons, and highlight code with Shiki.")
    parser.add_argument("pages", nargs="+", type=Path, metavar="PAGE", help="HTML file to update in place.")
    parser.add_argument(
        "--web-fonts",
        action="store_true",
        help="Link Mona Sans and Geist Mono from Google Fonts, for pages opened on other computers.",
    )
    args = parser.parse_args()

    try:
        prepared = []
        for path in args.pages:
            with path.open(newline="") as source:
                page, names = apply(source.read(), args.web_fonts)
            prepared.append((path, page, names))
        pages, counts = highlight_pages([page for _, page, _ in prepared])
        for (path, _, names), page, count in zip(prepared, pages, counts):
            with path.open("w", newline="") as target:
                target.write(page)
            icons = f"{len(names)} icons ({', '.join(names)})" if names else "no icons"
            fonts = "web fonts linked" if args.web_fonts else "installed fonts only"
            print(f"{path}: applied the theme with {icons}, {fonts}, {count} highlighted code blocks.")
            for warning in own_style_warnings(page):
                print(f"{path}: warning: the page {warning}", file=sys.stderr)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
