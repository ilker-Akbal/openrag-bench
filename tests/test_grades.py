"""Graded relevance, MAP@k and TREC graded-qrels regression coverage."""
import contextlib
from io import StringIO
import json
import math
from pathlib import Path
import tempfile
import unittest

from openrag_bench.cli import evaluate, main
from openrag_bench.comparison import compare_rows
from openrag_bench.metrics import (
    average_precision_at_k, graded_ndcg_at_k, ndcg_at_k)
from openrag_bench.trec import load_qrels, load_trec_run


class GradedMetricsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def put(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_map_at_k_convention_and_duplicates(self):
        self.assertAlmostEqual(average_precision_at_k(["a", "x", "b"], ["a", "b"], 3),
                               (1 + 2/3)/2)
        self.assertEqual(average_precision_at_k(["a", "x", "b"], ["a", "b"], 1), 1.0)
        self.assertEqual(average_precision_at_k(["a", "a", "b"], ["a", "b"], 3),
                         (1 + 2/3)/2)  # repeated doc earns no second credit
        self.assertEqual(average_precision_at_k([], ["a"], 3), 0)
        self.assertEqual(average_precision_at_k(["a"], [], 2), 0)
        with self.assertRaises(ValueError):
            average_precision_at_k(["a"], ["a"], 0)

    def test_graded_ndcg_differs_from_binary(self):
        relevance = {"a": 3, "b": 1}
        binary = ndcg_at_k(["b", "a"], ["a", "b"], 2)
        graded = graded_ndcg_at_k(["b", "a"], relevance, 2)
        expected = (1 + 7 / math.log2(3)) / (7 + 1 / math.log2(3))
        self.assertEqual(binary, 1)
        self.assertAlmostEqual(graded, expected)
        self.assertLess(graded, binary)
        self.assertEqual(graded_ndcg_at_k([], relevance, 2), 0)
        self.assertEqual(graded_ndcg_at_k(["a"], {"a": 0}, 2), 0)
        self.assertAlmostEqual(graded_ndcg_at_k(["a", "a"], {"a": 1}, 2), 1)

    def test_plain_binary_scores_preserved_and_report_extended(self):
        row = {"query_id": "q1", "retrieved_ids": ["b", "a"],
               "relevant_ids": ["a", "b"]}
        report = evaluate([row], 2)
        self.assertEqual(report["metrics"]["ndcg_at_k"], 1)
        self.assertEqual(report["metrics"]["graded_ndcg_at_k"], 1)
        self.assertEqual(report["metrics"]["map_at_k"], .5 + .5)

    def test_grades_validation(self):
        base = {"query_id": "q1", "retrieved_ids": ["a"],
                "relevant_ids": ["a"]}
        for grades in ({"a": 0}, {"a": True}, {"a": 32}, {"a": 1.2},
                       {"b": 2}, {"a": 2, "b": 3}, [], None):
            with self.subTest(grades=grades), self.assertRaises(ValueError):
                evaluate([{**base, "relevance_grades": grades}], 2)
        for invalid in ({"a": -1}, {"a": float("inf")}, {"a": True},
                        {"a": 32}, {"": 1}):
            with self.subTest(direct_grades=invalid), self.assertRaises(ValueError):
                graded_ndcg_at_k(["a"], invalid, 2)

    def test_paired_grades_must_match(self):
        base = {"query_id": "q1", "retrieved_ids": ["a"],
                "relevant_ids": ["a"]}
        with self.assertRaisesRegex(ValueError, "relevance_grades"):
            compare_rows([{**base, "relevance_grades": {"a": 3}}],
                         [{**base, "relevance_grades": {"a": 1}}], 1)
        plain = compare_rows([base], [{**base, "relevance_grades": {"a": 1}}], 1)
        self.assertEqual(plain["delta"]["graded_ndcg_at_k"], 0.0)

    def test_trec_grades_opt_in_with_cli(self):
        qrels = self.put("grades.qrels", "q1 0 a 3\nq1 0 b 1\nq1 0 c -1\n")
        run = self.put("run.trec", "q1 Q0 b 1 3 run\nq1 Q0 a 2 2 run\n")
        default = load_trec_run(run, qrels)
        with_grades = load_trec_run(run, qrels, graded=True)
        self.assertNotIn("relevance_grades", default[0])
        self.assertEqual(load_qrels(qrels, with_grades=True), {"q1": {"a": 3, "b": 1}})
        self.assertEqual(with_grades[0]["relevance_grades"], {"a": 3, "b": 1})
        self.assertEqual(evaluate(default, 2)["metrics"]["ndcg_at_k"], 1)
        self.assertLess(evaluate(with_grades, 2)["metrics"]["graded_ndcg_at_k"], 1)
        with contextlib.redirect_stdout(StringIO()):
            status = main([str(run), "--qrels", str(qrels), "--graded-qrels",
                           "--k", "2", "--metric", "graded_ndcg_at_k"])
        self.assertEqual(status, 0)

    def test_invalid_graded_qrels_and_cli_usage(self):
        invalid = self.put("bad.qrels", "q1 0 a 32\n")
        with self.assertRaisesRegex(ValueError, "cannot exceed 31"):
            load_qrels(invalid, with_grades=True)
        jsonfile = self.put("rows.json", json.dumps([{
            "query_id": "q1", "retrieved_ids": ["a"], "relevant_ids": ["a"]}]))
        with contextlib.redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
            main([str(jsonfile), "--graded-qrels"])
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
