---
name: html-theme
description: The house theme for HTML pages. Use it whenever you write or restyle a page meant to be read in a browser, such as an artifact, report, dashboard, prototype, mockup, explainer or PR walkthrough. Skip it when the project you are working in has its own design system, or when the user asks for a different look.
---

# HTML theme

Text is Mona Sans and code is Geist Mono, on neutral grays, with red-orange only on marks. A script inserts the stylesheet and the icons. Write markup with the elements and classes below. Do not read the asset files unless you are changing the theme itself.

## Build a page

1. Put `<!-- html-theme -->` inside `<head>`. Write the body with the elements and classes below. For a page that uses every component, see [the example](assets/example.html).
2. Run `python3 <skill-dir>/scripts/apply_theme.py <page.html>`. It replaces the marker with the stylesheet and adds the icons the page uses. Run it again after every edit. It replaces its own earlier output.
3. Add `--web-fonts` when the page will be published or opened on another computer. Without it, the page makes no network requests: it uses the installed fonts and falls back to IBM Plex Sans and IBM Plex Mono. To publish an artifact, build the file on disk with `--web-fonts` and publish that file.
4. Fix every warning the script prints. Never write your own colors, font families or font sizes. If a page needs a layout the theme lacks, add a `<style>` block after the marker that uses only the theme's tokens.
5. Look at the page in light mode, dark mode and at phone width before you hand it off.

## Type

There are five sizes. Choose the size by role, through the element or class. Never set a font size.

| Size | Roles | Markup |
|---|---|---|
| 40 px | Page title, big numbers | `h1`, `.display` |
| 28 px | Section | `h2` |
| 20 px | Subsection, lead paragraph | `h3`, `p.lead` |
| 16 px | Body text, h4 at weight 600 | `p`, `li`, `h4` |
| 14 px | Tables, metadata, captions, hints, labels | `table`, `.small`, `.label`, `figcaption`, `.hint` |

- Use one `h1` per page, and go no deeper than `h4`.
- Titles stand alone. Never put a small label, an eyebrow, above a heading.
- Make secondary text gray with `.muted` or `.faint`. Never use a thinner weight for it.
- `.name` is body text at the label weight, for list item names. `.label` is the same at 14 px.
- Put `.num` on table cells that hold numbers. It right-aligns them with tabular digits.

## Color

- Grays do the work. From the page to the strongest text, the tokens are `--bg`, `--surface`, `--sunken`, `--hover`, `--selected`, `--border-subtle`, `--border`, `--border-strong`, `--text-faint`, `--text-muted`, `--text` and `--text-strong`.
- `--accent` is red-orange, and it colors marks only: link underlines, focus rings, the selected tab or item, and the one highlighted value in a chart. Text is never red-orange.
- `--success`, `--warning` and `--danger` color only status icons and callout stripes. The label beside them stays gray.
- Separate things with the weakest means that works. Use tone first, through `.panel` or `.inset`. Then use `--border-subtle` for dividers, `--border` for containers and `--border-strong` for inputs.
- Light and dark mode come with the theme. The page follows the system setting, or `data-theme="light"` or `data-theme="dark"` on `<html>`.

## Icons

Write `<svg class="icon" aria-hidden="true"><use href="#i-NAME"/></svg>` inside a `.with-icon` element, before its label.

| Name | Meaning |
|---|---|
| `circle-check` | Passed or done |
| `circle-x` | Failed |
| `triangle-alert` | Warning or alarm |
| `info` | Note |
| `clock` | Pending or in progress |
| `circle-minus` | Skipped |
| `check` | Selected |
| `x` | Close or dismiss |
| `git-pr`, `git-branch`, `git-commit` | Pull request, branch, commit |
| `file`, `folder` | File path, directory path |
| `code` | Function or module |
| `terminal` | Shell command |
| `external` | Link that leaves the page |
| `copy` | Copy to the clipboard |
| `search` | Search |
| `chevron-right` | Next step, or expand |
| `cpu`, `battery`, `activity`, `bell` | Hardware, power, measured signal, alert |

- Each icon means only what the table says. Do not reuse an icon for another meaning. Ask for a new icon instead.
- Every icon sits beside a visible label. Only copy and close buttons may show an icon alone, and they need `aria-label` and `title`.
- An icon takes its label's color. Only status icons take a status color, through `.is-success`, `.is-warning` or `.is-danger`. Use `.is-muted` or `.is-faint` for quiet icons.
- Mark the exception, not the default. In a list of normal rows, only the rows that need attention get an icon. Keep the others aligned with an empty `.icon-slot`.
- Never put icons on headings, and never use emoji in their place.

## Components

- `main.page` holds the page in one column. Add `.wide` for dashboards. Its `header`, `section` and `footer` children space themselves.
- `.grid` lays out tiles, and `.row` lays out buttons.
- `.panel` is a raised tile. `.inset` is a sunken box without a border.
- `ul.meta` is a row of small metadata, with each item in an `li.with-icon`.
- `ol.flow` is a row of up to five steps joined by chevrons. Each `li` holds a `.name` and a `.small.muted` description.
- `.code` wraps a `.code-head` with the file name and a copy button, then a `pre`. Highlight with `.tk-k` for keywords, `.tk-t` for types, `.tk-f` for functions, `.tk-p` for preprocessor lines and `.tk-c` for comments. They change weight and gray, never hue. A bare `pre` also works.
- `.source` is the line under a code block that links to the file.
- Wrap a `table` in `.table-wrap` so it scrolls on narrow screens.
- `ul.checks` is a status list. Each `li` holds a status icon, a `div` with a `.name` and a `.small.muted` detail, and an optional `.small.faint` duration.
- `.callout` is a note with an icon and a stripe. Add `.success`, `.warning` or `.danger` for a status.
- `nav.tabs` holds links or buttons. Mark the current one with `aria-current="page"` or `aria-selected="true"`.
- `.btn` takes `.btn-primary`, `.btn-secondary` or `.btn-quiet`. `.icon-btn` is for icon-only buttons.
- `.field` holds a `label`, an `.input` wrapper around the `input` with an optional `.suffix`, and a `.hint`. `.checkbox` is a `label` around a checkbox.
- `details` with a `summary` hides optional detail.
- `svg.chart` draws a chart. Use `.series` for bars, `.series-line` for lines, `.highlight` or `.highlight-line` for the one value that matters, then `.axis`, `.grid-line`, `.limit`, and `text` or `text.value` for labels. Draw the chart at its real size so labels stay at 14 px. Every series is gray, so label series directly instead of relying on color.
