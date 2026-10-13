"""Regression coverage for JSONL ingestion and CSV exports."""
import contextlib
import csv
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from openrag_bench.cli import evaluate, main
from openrag_bench.io import read_rows
from openrag_bench.csv_report import render_csv


def fixture(identifier, retrieved):
    return {
        "query_id": identifier, "question": "Example",
        "retrieved_ids": retrieved, "relevant_ids": ["d1"],
    }


class FormatsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def put(self, filename, text):
        path = self.root / filename
        path.write_text(text, encoding="utf-8")
        return path

    def test_json_and_jsonl_equivalent_with_blank_lines_and_bom(self):
        rows = [fixture("a", ["d1", "d2"]), fixture("b", [])]
        json_file = self.put("scores.json", json.dumps(rows))
        jsonl = self.put("scores.jsonl",
                         "\ufeff" + json.dumps(rows[0]) + "\n\n" +
                         json.dumps(rows[1]) + "\n")
        ndjson = self.put("scores.ndjson", "\n".join(json.dumps(x) for x in rows))
        self.assertEqual(read_rows(json_file), rows)
        self.assertEqual(read_rows(jsonl), rows)
        self.assertEqual(read_rows(ndjson), rows)
        self.assertEqual(read_rows(jsonl, input_format="jsonl"), rows)
        self.assertEqual(evaluate(read_rows(json_file), 2),
                         evaluate(read_rows(jsonl), 2))

    def test_jsonl_errors_include_physical_line_number(self):
        malformed = self.put("bad.jsonl", "\n" + json.dumps(fixture("a", [])) +
                             "\n{ not-json }\n")
        with self.assertRaisesRegex(ValueError, "line 3"):
            read_rows(malformed)
        not_object = self.put("bad2.jsonl", "[]\n")
        with self.assertRaisesRegex(ValueError, "line 1 must be an object"):
            read_rows(not_object)
        empty = self.put("empty.jsonl", "\n\n")
        with self.assertRaisesRegex(ValueError, "no records"):
            read_rows(empty)
        with self.assertRaisesRegex(ValueError, "input_format"):
            read_rows(empty, input_format="tsv")
        broken_json = self.put("bad.json", "[,]")
        with self.assertRaisesRegex(ValueError, "line 1, column"):
            read_rows(broken_json)

    def test_csv_no_questions_and_formula_injection_protection(self):
        rows = [fixture("=1+1", ["d1"]), fixture("+cmd", []),
                fixture("@A1", []), fixture("-2", []),
                fixture("\t=2", []), fixture("normal", ["d1"])]
        report = evaluate(rows, 1)
        output = render_csv(report)
        parsed = list(csv.DictReader(StringIO(output)))
        self.assertEqual(len(parsed), 6)
        self.assertEqual(parsed[0]["query_id"], "'=1+1")
        self.assertEqual(parsed[1]["query_id"], "'+cmd")
        self.assertEqual(parsed[2]["query_id"], "'@A1")
        self.assertEqual(parsed[3]["query_id"], "'-2")
        self.assertEqual(parsed[4]["query_id"], "'\t=2")
        self.assertEqual(parsed[5]["query_id"], "normal")
        self.assertNotIn("question", parsed[0])
        self.assertEqual(float(parsed[0]["hit_at_k"]), 1)

    def test_cli_paired_jsonl_to_csv_with_order_independent_query_ids(self):
        candidate = self.put("candidate.jsonl", "\n".join(
            json.dumps(row) for row in [fixture("b", ["d1"]),
                                        fixture("a", ["d1"])]))
        baseline = self.put("baseline.ndjson", "\n".join(
            json.dumps(row) for row in [fixture("a", []), fixture("b", [])]))
        path = self.root / "paired.csv"
        with contextlib.redirect_stdout(StringIO()):
            result = main([str(candidate), "--baseline", str(baseline), "--k",
                           "1", "--csv", str(path), "--min-delta", "0"])
        self.assertEqual(result, 0)
        csvtext = path.read_text(encoding="utf-8-sig")
        entries = list(csv.DictReader(StringIO(csvtext)))
        self.assertEqual([x["query_id"] for x in entries], ["a", "b"])
        self.assertEqual(float(entries[0]["delta_hit_at_k"]), 1)
        self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))

    def test_cli_input_override_and_trec_conflict(self):
        rows = [fixture("a", ["d1"])]
        custom = self.put("data.txt", "\n".join(json.dumps(x) for x in rows))
        output = self.root / "rows.csv"
        with contextlib.redirect_stdout(StringIO()):
            self.assertEqual(main([str(custom), "--input-format", "jsonl",
                                   "--csv", str(output)]), 0)
        with contextlib.redirect_stderr(StringIO()), self.assertRaises(SystemExit) as error:
            main([str(custom), "--input-format", "json", "--qrels", str(custom)])
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
