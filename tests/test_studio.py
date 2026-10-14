"""Golden Dataset Studio local generator and HTML privacy regression tests."""
import contextlib
from io import StringIO
from html.parser import HTMLParser
from pathlib import Path
import tempfile
import unittest

from openrag_bench.cli import main
from openrag_bench.studio import STUDIO_HTML, studio


class _ScriptCounter(HTMLParser):
    """Count script tags using an HTML-aware parser, not a filtering regex."""

    def __init__(self):
        super().__init__()
        self.opened = 0
        self.closed = 0

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.opened += 1

    def handle_endtag(self, tag):
        if tag == "script":
            self.closed += 1


class StudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)

    def test_generate_html_and_safe_refuse_overwrite(self):
        output = self.folder / "studio.html"
        with contextlib.redirect_stdout(StringIO()):
            self.assertEqual(main(["studio", "--output", str(output)]), 0)
        first = output.read_bytes()
        self.assertTrue(first.startswith(b"<!doctype html>"))
        self.assertIn(b"Golden Dataset Studio", first)
        with contextlib.redirect_stderr(StringIO()), self.assertRaises(SystemExit) as caught:
            studio(["--output", str(output)])
        self.assertEqual(caught.exception.code, 2)
        self.assertEqual(output.read_bytes(), first)
        self.assertEqual(studio(["--output", str(output), "--overwrite"]), 0)
        self.assertEqual(output.read_bytes(), first)

    def test_disallow_symlink_targets(self):
        old = self.folder / "source.html"
        old.write_text("do not change me", encoding="utf-8")
        target = self.folder / "link.html"
        target.symlink_to(old)
        with contextlib.redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            studio(["--output", str(target), "--overwrite"])
        self.assertEqual(old.read_text(encoding="utf-8"), "do not change me")

    def test_offline_privacy_by_construction(self):
        html = STUDIO_HTML
        self.assertIn("Content-Security-Policy", html)
        self.assertIn("connect-src 'none'", html)
        self.assertIn("default-src 'none'", html)
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("<script src=", html)
        self.assertNotIn("<link rel=", html)
        self.assertNotIn("XMLHttpRequest", html)
        self.assertNotIn("fetch(", html)
        self.assertNotIn("localStorage", html)
        self.assertNotIn("sessionStorage", html)
        self.assertNotIn("innerHTML", html)
        self.assertIn("textContent", html)
        self.assertIn("FileReader", html)
        self.assertIn("URL.createObjectURL", html)
        self.assertIn("beforeunload", html)
        self.assertIn('role="status"', html)
        self.assertIn("@media(max-width:650px)", html)
        parser = _ScriptCounter()
        parser.feed(html)
        self.assertEqual(parser.opened, 1)
        self.assertEqual(parser.closed, 1)

    def test_export_has_real_metric_schema_and_explicit_empty_results(self):
        html = STUDIO_HTML
        self.assertIn('retrieved_ids:[]', html)
        self.assertIn('relevant_ids:ids', html)
        self.assertIn('relevance_grades:grades', html)
        self.assertIn('critical:q.critical', html)
        self.assertIn('question:q.question', html)
        self.assertIn("return {version:1,rules:rules};", html)
        self.assertIn('select:{type:"critical"}', html)
        self.assertIn('metric:"hit_at_k",min_query_score:1,max_regressed_queries:0', html)
        self.assertIn("retriever must subsequently supply ranked", html)

    def test_import_validation_and_draft_controls_present(self):
        html = STUDIO_HTML
        for anchor in (
            "validDocs(docs)", "validQueries(rows)", "validateRefs()",
            "clean(row.question,4000", "Output", "Save editable draft",
            "Import dataset or draft", "Import catalog JSON", "Export Guard policy",
            "Load synthetic example", "Grade", "Golden Dataset Studio",
        ):
            # Source labels and function names are contractual browser controls.
            self.assertIn(anchor.lower(), html.lower())

    def test_invalid_output_directory_stops_cleanly(self):
        missing = self.folder / "missing" / "studio.html"
        with contextlib.redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            studio(["--output", str(missing)])
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
