"""SciFact Capture & Replay fixture tests (no downloads or third-party data)."""
import json
from pathlib import Path
import tempfile
import unittest

from examples.scifact_benchmark import run_scifact
from examples.scifact_capture_replay import (LexicalRetriever, capture_real_search,
                                             run_capture_replay)
from examples.scifact_benchmark import LexicalIndex


def sample():
    corpus = {
        "a": "Alpha science biology cells divide",
        "b": "Beta chemistry molecules chemistry",
        "c": "Gamma physics gravity motion",
        "d": "Delta unrelated subject",
    }
    questions = {"q1": "cells biology", "q2": "molecules chemistry",
                 "q3": "gravity physics"}
    qrels = {"q1": ["a"], "q2": ["b"], "q3": ["c"]}
    return corpus, questions, qrels


class SciFactCaptureReplayTests(unittest.TestCase):
    def test_actual_retrievers_and_capture_match_existing_benchmark(self):
        docs, questions, qrels = sample()
        golden, observed = capture_real_search(docs, questions, qrels, 3)
        self.assertEqual(len(golden), 3)
        self.assertTrue(all(not row["retrieved_ids"] for row in golden))
        self.assertEqual(observed["tfidf"][0]["retrieved_ids"][0], "a")
        self.assertEqual(observed["bm25"][1]["retrieved_ids"][0], "b")
        old, _report = run_scifact(docs, questions, qrels, k=3)
        for method in ("tfidf", "bm25"):
            for row in observed[method]:
                expected = [doc for doc, _score in
                            old[method + "_rankings"][row["query_id"]]]
                self.assertEqual(row["retrieved_ids"], expected)

    def test_real_search_capture_replay_cli_report_parity(self):
        docs, questions, qrels = sample()
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / "capture"
            summary = run_capture_replay(docs, questions, qrels, k=3, output_dir=dest)
            self.assertTrue(summary["guard_passed"])
            self.assertEqual(summary["exit_code"], 0)
            self.assertEqual(summary["queries"], 3)
            self.assertEqual(summary["documents"], 4)
            report = json.loads((dest / "guard.json").read_text(encoding="utf-8"))
            old, _comparison = run_scifact(docs, questions, qrels, 3)
            self.assertAlmostEqual(
                report["baseline"]["metrics"]["ndcg_at_k"],
                old["tfidf"]["metrics"]["ndcg_at_k"], places=12)
            self.assertAlmostEqual(
                report["candidate"]["metrics"]["ndcg_at_k"],
                old["bm25"]["metrics"]["ndcg_at_k"], places=12)
            self.assertTrue((dest / "guard.html").exists())
            for method in ("tfidf", "bm25"):
                recorded = json.loads((dest / f"{method}-captured.json").read_text())
                self.assertEqual(len(recorded), 3)
                self.assertEqual(recorded[0]["relevant_ids"], ["a"])
                manifest_text = (dest / f"{method}-manifest.json").read_text()
                self.assertNotIn("cells biology", manifest_text)
            with self.assertRaisesRegex(ValueError, "refusing to overwrite"):
                run_capture_replay(docs, questions, qrels, k=3, output_dir=dest)

    def test_search_is_independent_from_judgment_labels(self):
        docs, questions, qrels = sample()
        _golden, observed = capture_real_search(docs, questions, qrels, 2)
        modified = {**qrels, "q1": ["d"]}
        golden2, observed2 = capture_real_search(docs, questions, modified, 2)
        self.assertEqual(observed, observed2)
        self.assertEqual(golden2[0]["relevant_ids"], ["d"])

    def test_bad_inputs_fail_without_creating_output(self):
        docs, questions, qrels = sample()
        with self.assertRaisesRegex(ValueError, "matching questions"):
            capture_real_search(docs, questions, {}, 2)
        with self.assertRaisesRegex(ValueError, "human qrels"):
            capture_real_search(docs, questions, {**qrels, "q2": []}, 2)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            capture_real_search(docs, questions, qrels, 0)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "report"
            target.write_text("do not overwrite", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "points to a file"):
                run_capture_replay(docs, questions, qrels, k=1, output_dir=target)
            self.assertEqual(target.read_text(), "do not overwrite")

    def test_lexical_adapter_uses_index_ranking(self):
        docs, _questions, _qrels = sample()
        index = LexicalIndex(docs)
        baseline = LexicalRetriever(index, "tfidf")
        self.assertEqual(baseline.retrieve("biology cells", 1), ["a"])
        self.assertEqual(baseline.retrieve("no-exact-match", 2), [])
        with self.assertRaisesRegex(ValueError, "method must be"):
            LexicalRetriever(index, "unknown")


if __name__ == "__main__":
    unittest.main()
