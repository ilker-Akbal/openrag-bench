"""Quickstart must use observed retrieval and block a critical regression."""
import json
from pathlib import Path
import tempfile
import unittest

from examples.quickstart_capture_replay import (
    BASELINE_DOCUMENTS, CANDIDATE_DOCUMENTS, GOLDEN,
    KeywordRetriever, main, run_demo,
)


class QuickstartCaptureReplayTests(unittest.TestCase):
    def test_actual_retrieval_not_constructed_from_labels(self):
        retriever = KeywordRetriever(BASELINE_DOCUMENTS)
        self.assertEqual(retriever.retrieve("delete my data", 1), ["privacy-guide"])
        self.assertEqual(retriever.retrieve("warranty duration", 1), [])
        another = KeywordRetriever(CANDIDATE_DOCUMENTS)
        self.assertEqual(another.retrieve("delete my data", 1), [])
        self.assertEqual(another.retrieve("install application", 1), ["setup-guide"])
        self.assertEqual(another.retrieve("warranty duration", 1), ["warranty-guide"])
        changed_labels = [{**row, "relevant_ids": ["other"]} for row in GOLDEN]
        self.assertEqual(retriever.retrieve(changed_labels[0]["question"], 1),
                         ["privacy-guide"])

    def test_complete_cli_capture_and_guard_replay_block(self):
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "demo"
            summary = run_demo(destination)
            self.assertEqual(summary["queries"], 3)
            self.assertTrue(summary["overall_improved"])
            self.assertFalse(summary["guard_passed"])
            self.assertEqual(summary["failed_rules"], ["critical-privacy-hit"])
            report = json.loads((destination / "guard.json").read_text(encoding="utf-8"))
            self.assertGreater(report["delta"]["ndcg_at_k"], 0)
            self.assertTrue((destination / "guard.html").exists())
            baseline = json.loads((destination / "baseline.json").read_text(encoding="utf-8"))
            candidate = json.loads((destination / "candidate.json").read_text(encoding="utf-8"))
            self.assertEqual(baseline[0]["retrieved_ids"], ["privacy-guide"])
            self.assertEqual(candidate[0]["retrieved_ids"], [])
            self.assertEqual(candidate[1]["retrieved_ids"], ["setup-guide"])
            self.assertTrue(baseline[0]["critical"])
            self.assertEqual(candidate[0]["relevance_grades"], {"privacy-guide": 2})
            for name in ("baseline", "candidate"):
                manifest = (destination / f"{name}.manifest.json").read_text()
                self.assertNotIn("delete my data", manifest)
                self.assertIn("openrag-capture/v1", manifest)

    def test_no_overwrite_and_no_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "demo"
            result = run_demo(path)
            self.assertFalse(result["guard_passed"])
            with self.assertRaises(FileExistsError):
                run_demo(path)
            self.assertTrue((path / "guard.html").exists())

    def test_entrypoint_default_failure_reporting(self):
        with tempfile.TemporaryDirectory() as tmp:
            import contextlib
            import io
            target = Path(tmp) / "new"
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(["--output-dir", str(target)]), 0)
            self.assertTrue((target / "candidate-observed.json").exists())


if __name__ == "__main__":
    unittest.main()
