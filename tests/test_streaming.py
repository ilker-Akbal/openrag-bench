"""Streaming JSONL evaluation parity and strict mode contract."""
import contextlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from openrag_bench.cli import evaluate, main
from openrag_bench.io import read_rows
from openrag_bench.streaming import evaluate_jsonl_stream


class StreamingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def save(self, name, value):
        path = self.root / name
        path.write_text(value, encoding="utf-8")
        return path

    def test_parity_binary_graded_empty_qrels_and_blank_lines(self):
        data = [
            {"query_id": "a", "question": "planet", "retrieved_ids": ["d1", "d2"],
             "relevant_ids": ["d1", "d2"], "relevance_grades": {"d1": 3, "d2": 1}},
            {"query_id": "b", "retrieved_ids": [], "relevant_ids": []},
            {"query_id": "c", "retrieved_ids": ["x", "y"],
             "relevant_ids": ["y"]},
        ]
        file = self.save("file.jsonl", "\ufeff" + "\n\n".join(json.dumps(x) for x in data))
        exact = evaluate(read_rows(file), 2)
        observed = evaluate_jsonl_stream(file, 2)
        self.assertEqual(observed["count"], exact["count"])
        self.assertEqual(observed["k"], 2)
        self.assertNotIn("per_query", observed)
        for metric in exact["metrics"]:
            self.assertAlmostEqual(observed["metrics"][metric], exact["metrics"][metric], places=12)

    def test_cli_streaming_and_output(self):
        row = {"query_id": "q1", "retrieved_ids": ["doc"], "relevant_ids": ["doc"]}
        path = self.save("x.ndjson", json.dumps(row) + "\n")
        out = self.root / "summary.json"
        with contextlib.redirect_stdout(StringIO()):
            self.assertEqual(main([str(path), "--streaming-summary", "--k", "1",
                                   "--output", str(out)]), 0)
        report = json.loads(out.read_text())
        self.assertEqual(report["count"], 1)
        self.assertEqual(report["metrics"]["ndcg_at_k"], 1)
        self.assertEqual(report["evaluation_mode"], "streaming_jsonl_summary")
        custom = self.save("unnamed.data", json.dumps(row))
        with contextlib.redirect_stdout(StringIO()):
            self.assertEqual(main([str(custom), "--streaming-summary",
                                   "--input-format", "jsonl"]), 0)

    def test_rejected_features_do_not_silently_fallback(self):
        file = self.save("one.jsonl", '{"retrieved_ids":[],"relevant_ids":[]}')
        rejected = (
            [str(file), "--streaming-summary", "--baseline", str(file)],
            [str(file), "--streaming-summary", "--html", str(self.root / "a.html")],
            [str(file), "--streaming-summary", "--csv", str(self.root / "a.csv")],
            [str(file), "--streaming-summary", "--qrels", str(file)],
            [str(file), "--streaming-summary", "--graded-qrels"],
        )
        for args in rejected:
            with self.subTest(args=args), contextlib.redirect_stderr(StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main(args)
                self.assertEqual(error.exception.code, 2)
        wrong = self.save("bad.json", "[]")
        with contextlib.redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            main([str(wrong), "--streaming-summary"])

    def test_errors_include_physical_lines_and_duplicate_ids(self):
        invalid = self.save("errors.jsonl", "\n" + json.dumps({
            "retrieved_ids": ["a", "a"], "relevant_ids": ["a"]}) + "\n")
        with self.assertRaisesRegex(ValueError, "line 2"):
            evaluate_jsonl_stream(invalid, 3)
        broken = self.save("broken.jsonl", "\n{fail\n")
        with self.assertRaisesRegex(ValueError, "line 2"):
            evaluate_jsonl_stream(broken, 3)
        empty = self.save("empty.jsonl", "\n\n")
        with self.assertRaisesRegex(ValueError, "no records"):
            evaluate_jsonl_stream(empty, 3)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            evaluate_jsonl_stream(broken, 0)

    def test_ten_thousand_synthetic_rows_parity(self):
        path = self.root / "10k.jsonl"
        with path.open("w", encoding="utf-8") as handle:
            for i in range(10000):
                row = {"query_id": f"q{i}", "retrieved_ids":
                       ["a", "b"] if i % 2 else ["b", "a"],
                       "relevant_ids": ["a"]}
                handle.write(json.dumps(row) + "\n")
        streaming = evaluate_jsonl_stream(path, 2)
        regular = evaluate(read_rows(path), 2)
        self.assertEqual(streaming["count"], 10000)
        for metric in regular["metrics"]:
            self.assertAlmostEqual(streaming["metrics"][metric],
                                   regular["metrics"][metric], places=10)


if __name__ == "__main__":
    unittest.main()
