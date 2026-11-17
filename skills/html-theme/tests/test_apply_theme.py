from html import escape
from html.parser import HTMLParser
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


SKILL_DIR = Path(__file__).resolve().parent.parent
SCRIPT = SKILL_DIR / "scripts" / "apply_theme.py"
spec = importlib.util.spec_from_file_location("apply_theme", SCRIPT)
theme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(theme)


def page_with_code(source, language):
    return (
        '<!doctype html><html><head><!-- html-theme --></head><body>'
        f'<pre id="excerpt"><code class="language-{language}" data-file="example">{escape(source)}</code></pre>'
        '</body></html>'
    )


class RenderedCode(HTMLParser):
    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.in_code = False
        self.parts = []
        self.tags = []
        self.span_depth = 0
        self.max_span_depth = 0
        self.styled_parts = []
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        if tag == "code":
            self.in_code = True
        elif self.in_code:
            self.tags.append(tag)
            if tag == "span":
                self.span_depth += 1
                self.max_span_depth = max(self.max_span_depth, self.span_depth)

    def handle_endtag(self, tag):
        if tag == "code":
            self.in_code = False
        elif tag == "span" and self.in_code:
            self.span_depth -= 1

    def handle_data(self, data):
        if self.in_code:
            self.parts.append(data)
            if self.span_depth:
                self.styled_parts.append(data)


class ApplyThemeTests(unittest.TestCase):
    def test_real_language_formats_keep_exact_source(self):
        samples = {
            "sql": "ALTER TABLE orders ADD COLUMN status text DEFAULT 'pending';\n",
            "ts": "export async function find<T>(id: string): Promise<T> {\n  // Keep the result.\n  return await store.get(id);\n}\n",
            "tsx": 'export function Label() {\n  return <strong aria-label="Status">{`Ready: ${true}`}</strong>;\n}\n',
            "go": 'func Reserve(sku string) error {\n  return fmt.Errorf("missing %q", sku)\n}\n',
            "bash": 'report_dir="${1:-./reports}"\nprintf \'%s\\n\' "$report_dir"\n',
            "json": json.dumps({"note": '<script>alert("x")</script>', "ready": True}) + "\n",
        }
        pages, counts = theme.highlight_pages([page_with_code(source, language) for language, source in samples.items()])
        self.assertEqual(counts, [1] * len(samples))
        for source, page in zip(samples.values(), pages):
            with self.subTest(source=source):
                rendered = RenderedCode(page)
                self.assertEqual("".join(rendered.parts), source)
                self.assertTrue(rendered.styled_parts)
                self.assertEqual(set(rendered.tags), {"span"})
                self.assertIn('id="excerpt"', page)
                self.assertIn('data-file="example"', page)

    def test_line_endings_unicode_and_partial_excerpts_survive(self):
        samples = [
            "const label = 'Møn & København';",
            "\tconst complete = true;\r\n\r\n",
            '    <section aria-label="Status">\n      {complete ? \'Complete\' :\n',
            "",
        ]
        pages, _ = theme.highlight_pages([page_with_code(source, "tsx") for source in samples])
        self.assertEqual(["".join(RenderedCode(page).parts) for page in pages], samples)

    def test_rerunning_produces_identical_markup_without_nested_spans(self):
        page = page_with_code("const value = true; // Keep this.\n", "typescript")
        first, _ = theme.highlight_pages([theme.apply(page, False)[0]])
        second, _ = theme.highlight_pages([theme.apply(first[0], False)[0]])
        self.assertEqual(first, second)
        self.assertEqual(RenderedCode(second[0]).max_span_depth, 1)
        self.assertEqual(theme.own_style_warnings(second[0]), [])

    def test_unknown_and_plain_languages_stay_escaped_plain_text(self):
        source = '<script>alert("example")</script> & <em>source</em>\n'
        with patch.object(theme.sys, "stderr") as stderr:
            pages, counts = theme.highlight_pages([
                page_with_code(source, "made-up-language"),
                page_with_code(source, "text"),
            ])
        self.assertEqual(counts, [0, 0])
        self.assertIn("made-up-language", "".join(call.args[0] for call in stderr.write.call_args_list))
        for page in pages:
            rendered = RenderedCode(page)
            self.assertEqual("".join(rendered.parts), source)
            self.assertEqual(rendered.tags, [])

    def test_unmarked_and_inline_code_do_not_start_node(self):
        page = '<p><code class="language-ts">let x = 1;</code></p><pre><code>plain</code></pre>'
        with patch.object(theme.subprocess, "run") as run:
            pages, counts = theme.highlight_pages([page])
        self.assertEqual(pages, [page])
        self.assertEqual(counts, [0])
        run.assert_not_called()

    def test_several_pages_use_one_highlighter_process(self):
        pages = [page_with_code("const ready = true;", "typescript")] * 3
        with patch.object(theme.subprocess, "run", wraps=subprocess.run) as run:
            _, counts = theme.highlight_pages(pages)
        self.assertEqual(counts, [1, 1, 1])
        self.assertEqual(run.call_count, 1)

    def test_unescaped_html_is_rejected(self):
        page = '<pre><code class="language-html"><script>example</script></code></pre>'
        with self.assertRaisesRegex(ValueError, "Escape HTML"):
            theme.highlight_pages([page])

    def test_missing_dependency_does_not_write_a_partial_page(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            original = page_with_code("const ready = true;", "typescript")
            path.write_text(original)
            with patch.object(theme, "SKILL_DIR", Path(directory)), patch.object(sys, "argv", [str(SCRIPT), str(path)]):
                with patch.object(sys, "stderr"), self.assertRaises(SystemExit) as error:
                    theme.main()
            self.assertEqual(error.exception.code, 1)
            self.assertEqual(path.read_text(), original)

    def test_cli_works_from_another_directory_and_preserves_crlf(self):
        source = "const ready = true;\r\n\r\n"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "page.html"
            with path.open("w", newline="") as target:
                target.write(page_with_code(source, "typescript"))
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)], cwd=directory, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("1 highlighted code blocks", result.stdout)
            self.assertEqual(result.stderr, "")
            with path.open(newline="") as result_file:
                page = result_file.read()
            self.assertEqual("".join(RenderedCode(page).parts), source)
            self.assertNotIn('<script src=', page)
            self.assertNotIn('<link ', page)


if __name__ == "__main__":
    unittest.main()
