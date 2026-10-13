import json
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stdout
from io import StringIO

from openrag_bench.cli import evaluate, main
from openrag_bench.comparison import compare_rows
from openrag_bench.html_report import render_html
from openrag_bench.metrics import ndcg_at_k, reciprocal_rank


def fixture(query_id, retrieved, relevant=None):
    return {"query_id": query_id, "question": query_id,
            "retrieved_ids": retrieved, "relevant_ids": relevant or ["a"]}


class ComparisonTests(unittest.TestCase):
    def test_mrr_is_cutoff_aware(self):
        rows = [fixture("one", ["x", "a"])]
        self.assertEqual(evaluate(rows, 1)["metrics"]["mrr_at_k"], 0)
        self.assertEqual(evaluate(rows, 1)["metrics"]["reciprocal_rank"], .5)
        self.assertEqual(reciprocal_rank(["x", "a"], ["a"], 1), 0)

    def test_duplicate_does_not_inflate_ndcg(self):
        self.assertLessEqual(ndcg_at_k(["a", "a"], ["a"], 2), 1)

    def test_comparison_is_independent_of_row_order(self):
        candidate = [fixture("b", ["a"]), fixture("a", ["a"])]
        baseline = [fixture("a", ["x"]), fixture("b", ["a"])]
        report = compare_rows(candidate, baseline, 1)
        self.assertEqual(report["count"], 2)
        self.assertEqual(report["delta"]["hit_at_k"], .5)
        self.assertEqual(report["paired_bootstrap_95pct_ci"]["hit_at_k"], [0., 1.])
        self.assertEqual(
            compare_rows(candidate, baseline, 1)["paired_bootstrap_95pct_ci"],
            report["paired_bootstrap_95pct_ci"])

    def test_mismatching_queries_fail(self):
        with self.assertRaisesRegex(ValueError, "Query IDs differ"):
            compare_rows([fixture("x", ["a"])], [fixture("y", ["a"])], 1)
        with self.assertRaisesRegex(ValueError, "duplicate query_id"):
            compare_rows([fixture("x", ["a"]), fixture("x", ["a"])],
                         [fixture("x", ["a"])], 1)
        with self.assertRaisesRegex(ValueError, "query_id is required"):
            compare_rows([{"retrieved_ids": ["a"], "relevant_ids": ["a"]}],
                         [fixture("x", ["a"])], 1)

    def test_ground_truth_mismatch_fails(self):
        with self.assertRaisesRegex(ValueError, "Ground-truth"):
            compare_rows([fixture("x", ["a"], ["a"])],
                         [fixture("x", ["a"], ["b"])], 1)

    def test_validates_optional_fields(self):
        for broken in ({"query_id": 123}, {"query_id": ""},
                       {"question": None}, {"question": "  "}):
            row = fixture("x", ["a"])
            row.update(broken)
            with self.subTest(broken=broken), self.assertRaises(ValueError):
                evaluate([row], 1)

    def test_escaped_comparison_html(self):
        report = compare_rows([fixture("<script>", ["a"])],
                              [fixture("<script>", ["x"])], 1)
        html = render_html(report)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)

    def test_cli_regression_gate_exit_code_and_report(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            candidate = folder / "candidate.json"
            baseline = folder / "baseline.json"
            output = folder / "result.json"
            candidate.write_text(json.dumps([fixture("q", ["x"])]))
            baseline.write_text(json.dumps([fixture("q", ["a"])]))
            with redirect_stdout(StringIO()), self.assertRaises(SystemExit) as error:
                main([str(candidate), "--baseline", str(baseline), "--k", "1",
                      "--min-delta", "0", "--output", str(output)])
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(json.loads(output.read_text())["gate"]["passed"])

    def test_cli_baseline_passes_with_html(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            candidate = folder / "candidate.json"
            baseline = folder / "baseline.json"
            html_path = folder / "report.html"
            candidate.write_text(json.dumps([fixture("q", ["a"])]))
            baseline.write_text(json.dumps([fixture("q", ["x"])]))
            with redirect_stdout(StringIO()):
                result = main([str(candidate), "--baseline", str(baseline), "--k", "1",
                               "--min-delta", "0", "--html", str(html_path)])
            self.assertEqual(result, 0)
            self.assertIn("Candidate", html_path.read_text())


if __name__ == "__main__":
    unittest.main()
