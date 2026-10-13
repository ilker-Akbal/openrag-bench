import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from openrag_bench.cli import evaluate, main
from openrag_bench.trec import load_qrels, load_trec_run


class TrecTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)
        self.qrels = self._file("qrels.txt",
            "q2 0 d2 2\nq1 0 d1 1\nq1 0 d3 0\nq3 0 d8 0\n")
        self.candidate = self._file("candidate.run",
            "q1 Q0 d3 2 .1 current\nq1 Q0 d1 1 0.9 current\n"
            "q2 Q0 d2 1 0.7 current\n")
        self.baseline = self._file("baseline.run",
            "q1 Q0 d3 1 1 baseline\nq1 Q0 d1 2 0.2 baseline\n"
            "q2 Q0 d2 1 1 baseline\n")

    def _file(self, name, content):
        path = self.path / name
        path.write_text(content, encoding="utf-8")
        return path

    def test_all_qrels_queries_evaluated_including_missing_run_queries(self):
        rows = load_trec_run(self.candidate, self.qrels)
        self.assertEqual([row["query_id"] for row in rows], ["q1", "q2", "q3"])
        self.assertEqual(rows[0]["retrieved_ids"], ["d1", "d3"])
        self.assertEqual(rows[2]["retrieved_ids"], [])
        self.assertEqual(rows[2]["relevant_ids"], [])
        report = evaluate(rows, 2)
        self.assertEqual(report["count"], 3)
        self.assertAlmostEqual(report["metrics"]["hit_at_k"], 2/3)

    def test_qrels_binary_labels_and_duplicate_detection(self):
        self.assertEqual(load_qrels(self.qrels)["q2"], ["d2"])
        duplicate = self._file("dup.qrels", "q1 0 d1 1\nq1 0 d1 1\n")
        with self.assertRaisesRegex(ValueError, "duplicate judgment"):
            load_qrels(duplicate)

    def test_invalid_trec_runs(self):
        bad = {
            "unknown qid": ("q9 Q0 d1 1 1 tag\n", "absent from qrels"),
            "duplicate doc": ("q1 Q0 d1 1 1 tag\nq1 Q0 d1 2 0 tag\n", "duplicate document"),
            "duplicate rank": ("q1 Q0 d1 1 1 tag\nq1 Q0 d2 1 0 tag\n", "duplicate rank"),
            "infinite score": ("q1 Q0 d1 1 inf tag\n", "finite score"),
            "negative rank": ("q1 Q0 d1 -1 0 tag\n", "positive rank"),
            "malformed": ("q1 d1 1 1 tag\n", "six fields"),
        }
        for name, (data, error) in bad.items():
            with self.subTest(name=name):
                filename = self._file("bad.run", data)
                with self.assertRaisesRegex(ValueError, error):
                    load_trec_run(filename, self.qrels)

    def test_comparison_through_cli(self):
        output = self.path / "comparison.json"
        with contextlib.redirect_stdout(io.StringIO()):
            status = main([str(self.candidate), "--qrels", str(self.qrels),
                           "--baseline", str(self.baseline), "--k", "2",
                           "--min-delta", "0", "--output", str(output)])
        self.assertEqual(status, 0)
        report = json.loads(output.read_text())
        self.assertEqual(report["count"], 3)
        self.assertTrue(report["gate"]["passed"])

    def test_empty_qrels_and_bad_grade(self):
        blank = self._file("empty.qrels", "")
        with self.assertRaisesRegex(ValueError, "at least one"):
            load_qrels(blank)
        bad = self._file("grade.qrels", "q1 0 d1 positive\n")
        with self.assertRaisesRegex(ValueError, "integer"):
            load_qrels(bad)


if __name__ == "__main__":
    unittest.main()
