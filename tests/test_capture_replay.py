"""Offline capture/replay contracts: no generated answers or silent ID changes."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from openrag_bench.capture import (capture, capture_from_retriever,
                                   capture_rows, replay)


def golden():
    return [
        {"query_id": "privacy", "question": "How do I delete my data?",
         "category": "privacy", "critical": True,
         "retrieved_ids": [], "relevant_ids": ["doc-privacy"],
         "relevance_grades": {"doc-privacy": 2}},
        {"query_id": "install", "question": "How do I install?",
         "category": "support", "critical": False,
         "retrieved_ids": [], "relevant_ids": ["doc-install"],
         "relevance_grades": {"doc-install": 1}},
    ]


def ranks():
    # Intentionally reverse incoming ranking order: output follows golden order.
    return [
        {"query_id": "install", "retrieved_ids": ["raw-install"]},
        {"query_id": "privacy", "retrieved_ids": ["raw-privacy", "raw-other"]},
    ]


def id_map():
    return {"raw-privacy": "doc-privacy", "raw-install": "doc-install",
            "raw-other": "not-relevant"}


class CaptureTests(unittest.TestCase):
    def test_captures_ranked_ids_in_golden_order(self):
        rows = capture_rows(golden(), ranks(), id_map=id_map())
        self.assertEqual([r["query_id"] for r in rows], ["privacy", "install"])
        self.assertEqual(rows[0]["retrieved_ids"], ["doc-privacy", "not-relevant"])
        self.assertEqual(rows[1]["retrieved_ids"], ["doc-install"])
        self.assertTrue(rows[0]["critical"])
        self.assertEqual(rows[0]["relevance_grades"], {"doc-privacy": 2})

    def test_direct_identity_ids(self):
        rows = capture_rows(golden(), [{"query_id": "privacy", "retrieved_ids": []},
                                        {"query_id": "install", "retrieved_ids": []}])
        self.assertEqual(rows[0]["retrieved_ids"], [])

    def test_missing_and_extra_queries_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing="):
            capture_rows(golden(), ranks()[:1])
        with self.assertRaisesRegex(ValueError, "extra="):
            capture_rows(golden(), ranks() + [{"query_id": "extra", "retrieved_ids": []}])

    def test_duplicate_queries_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate ranking"):
            capture_rows(golden(), ranks() + ranks()[:1])
        items = golden()
        items[1]["query_id"] = items[0]["query_id"]
        with self.assertRaisesRegex(ValueError, "unique"):
            capture_rows(items, ranks())

    def test_missing_ids_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "unmapped document"):
            capture_rows(golden(), ranks(), id_map={"raw-install": "doc-install"})

    def test_canonical_collisions_fail_closed(self):
        mapping = id_map()
        mapping["raw-other"] = "doc-privacy"
        with self.assertRaisesRegex(ValueError, "collapses"):
            capture_rows(golden(), ranks(), id_map=mapping)

    def test_raw_duplicate_and_nonstring_ids_rejected(self):
        items = ranks()
        items[1]["retrieved_ids"] = ["a", "a"]
        with self.assertRaisesRegex(ValueError, "duplicate raw"):
            capture_rows(golden(), items)
        items[1]["retrieved_ids"] = [123]
        with self.assertRaisesRegex(ValueError, "nonempty strings"):
            capture_rows(golden(), items)

    def test_rank_record_fields_are_strict(self):
        items = ranks()
        items[1]["private_data"] = "must not be exported"
        with self.assertRaisesRegex(ValueError, "exactly"):
            capture_rows(golden(), items)

    def test_map_shape_rejected(self):
        with self.assertRaisesRegex(ValueError, "ID map"):
            capture_rows(golden(), ranks(), id_map={"x": None})
        with self.assertRaisesRegex(ValueError, "ID map"):
            capture_rows(golden(), ranks(), id_map=["invalid"])

    def test_golden_labels_required(self):
        items = golden()
        items[0]["relevant_ids"] = []
        items[0]["relevance_grades"] = {}
        with self.assertRaisesRegex(ValueError, "positive human"):
            capture_rows(items, ranks())
        items = golden()
        items[0]["retrieved_ids"] = ["not-golden"]
        with self.assertRaisesRegex(ValueError, "empty retrieved_ids"):
            capture_rows(items, ranks())

    def test_metadata_types_strict(self):
        items = golden()
        items[0]["critical"] = "yes"
        with self.assertRaisesRegex(ValueError, "boolean"):
            capture_rows(items, ranks())
        items = golden()
        items[0]["category"] = ""
        with self.assertRaisesRegex(ValueError, "category"):
            capture_rows(items, ranks())

    def test_retriever_protocol_collects_actual_ids(self):
        class Retriever:
            def __init__(self):
                self.asked = []
            def retrieve(self, question, k):
                self.asked.append((question, k))
                return ["raw-privacy"] if "delete" in question else ["raw-install"]
        retriever = Retriever()
        result = capture_from_retriever(retriever, golden(), 3, id_map=id_map())
        self.assertEqual(len(retriever.asked), 2)
        self.assertEqual(result[0]["retrieved_ids"], ["doc-privacy"])

    def test_retriever_invalid_results_fail(self):
        class Bad:
            def retrieve(self, _q, k):
                return ["a"] * (k + 1)
        with self.assertRaisesRegex(ValueError, "more than k"):
            capture_from_retriever(Bad(), golden(), 1)
        with self.assertRaisesRegex(ValueError, "positive integer"):
            capture_from_retriever(Bad(), golden(), True)

    def test_cli_writes_stable_hash_only_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "golden.json").write_text(json.dumps(golden()), encoding="utf-8")
            (path / "ranks.json").write_text(json.dumps(ranks()), encoding="utf-8")
            (path / "id-map.json").write_text(json.dumps(id_map()), encoding="utf-8")
            args = [str(path / "golden.json"), "--rankings", str(path / "ranks.json"),
                    "--id-map", str(path / "id-map.json"), "--output", str(path / "result.json"),
                    "--manifest", str(path / "manifest.json")]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(capture(args), 0)
            rows = json.loads((path / "result.json").read_text(encoding="utf-8"))
            manifest_bytes = (path / "manifest.json").read_text(encoding="utf-8")
            manifest = json.loads(manifest_bytes)
            self.assertEqual(rows[0]["retrieved_ids"], ["doc-privacy", "not-relevant"])
            self.assertEqual(manifest["format"], "openrag-capture/v1")
            self.assertEqual(manifest["queries_with_results"], 2)
            self.assertNotIn("How do I delete", manifest_bytes)
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    capture(args)
            self.assertEqual(error.exception.code, 2)

    def test_cli_supports_jsonl_rankings_and_rejects_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / "golden.json").write_text(json.dumps(golden()), encoding="utf-8")
            (path / "ranks.jsonl").write_text("\n".join(json.dumps(row) for row in ranks()),
                                               encoding="utf-8")
            args = [str(path / "golden.json"), "--rankings", str(path / "ranks.jsonl"),
                    "--output", str(path / "out.json")]
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(capture(args), 0)
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    capture(args)
            self.assertEqual(json.loads((path / "out.json").read_text())[0]["query_id"],
                             "privacy")

    def test_replay_reuses_guard_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            baseline = capture_rows(golden(), [
                {"query_id": "privacy", "retrieved_ids": ["doc-privacy"]},
                {"query_id": "install", "retrieved_ids": []},
            ])
            candidate = capture_rows(golden(), [
                {"query_id": "privacy", "retrieved_ids": []},
                {"query_id": "install", "retrieved_ids": ["doc-install"]},
            ])
            policy = {"version": 1, "rules": [{
                "id": "privacy-protection", "select": {"type": "critical"},
                "metric": "hit_at_k", "min_query_score": 1,
                "max_regressed_queries": 0,
            }]}
            for name, value in [("base.json", baseline), ("candidate.json", candidate),
                                ("policy.json", policy)]:
                (path / name).write_text(json.dumps(value), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = replay([str(path / "candidate.json"), "--baseline",
                               str(path / "base.json"), "--policy", str(path / "policy.json"),
                               "--k", "1", "--html", str(path / "blocked.html")])
            self.assertEqual(code, 2)
            self.assertIn("html", str(path / "blocked.html"))
            self.assertTrue((path / "blocked.html").exists())


if __name__ == "__main__":
    unittest.main()
