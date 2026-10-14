"""Offline README quality checks: local links and released version must stay current."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

from openrag_bench import __version__


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"


def local_targets(markdown):
    """Inspect Markdown links and HTML src/href without downloading anything."""
    raw_links = [match.group(1) for match in re.finditer(r"\]\(([^)]+)\)", markdown)]
    raw_links.extend(match.group(1) for match in re.finditer(
        r'(?:src|href)="([^"]+)"', markdown
    ))
    for raw in raw_links:
        if raw.startswith("#"):
            continue
        parts = urlsplit(raw)
        if parts.scheme or parts.netloc:
            continue
        path = unquote(parts.path)
        if path:
            yield path


class ReadmeIntegrityTests(unittest.TestCase):
    def test_readme_relative_file_links_exist(self):
        markdown = README.read_text(encoding="utf-8")
        targets = list(local_targets(markdown))
        self.assertGreaterEqual(len(targets), 30)
        missing = sorted({target for target in targets if not (ROOT / target).is_file()})
        self.assertEqual(missing, [], "README links to missing repository files")

    def test_readme_mentions_published_package_version(self):
        markdown = README.read_text(encoding="utf-8")
        self.assertIn(f"releases/tag/v{__version__}", markdown)
        self.assertIn(f"openrag_bench-{__version__}-py3-none-any.whl", markdown)
        self.assertIn("not on PyPI", markdown)
        self.assertIn("current **`main` source checkout**", markdown)


if __name__ == "__main__":
    unittest.main()
