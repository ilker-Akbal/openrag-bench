"""Self-check for the Luna Work black-box QA probe, using original synthetic data."""
from pathlib import Path
import tempfile
import unittest

from scripts.luna_qa_probe import probe


class LunaQAProbeTests(unittest.TestCase):
    def test_blackbox_capture_replay_and_redaction_suite(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "luna"
            result = probe(target)
            self.assertGreaterEqual(result["total"], 10)
            self.assertEqual(result["passed"], result["total"], result["checks"])
            self.assertTrue((target / "studio.html").is_file())
            self.assertTrue((target / "blocked.html").is_file())
            self.assertTrue((target / "passed.html").is_file())
            self.assertTrue((target / "probe-summary.json").is_file())
            self.assertTrue(all(item["passed"] for item in result["checks"]))

    def test_existing_evidence_not_overwritten(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "already-there"
            target.mkdir()
            sentinel = target / "existing.txt"
            sentinel.write_text("KEEP", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                probe(target)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "KEEP")


if __name__ == "__main__":
    unittest.main()
