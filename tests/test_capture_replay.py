"""Offline capture/replay contracts: no generated answers or silent ID changes."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import openrag_bench.capture as capture_module

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


    def test_manifest_write_failure_rolls_back_primary_dataset(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gold = root / "golden.json"
            ranking_path = root / "rankings.json"
            gold.write_text(json.dumps(golden()), encoding="utf-8")
            ranking_path.write_text(json.dumps(ranks()), encoding="utf-8")
            result_path = root / "result.json"
            manifest_path = root / "manifest.json"
            real_write = capture_module._write_new

            def fail_manifest(path, payload):
                if Path(path) == manifest_path:
                    raise OSError("injected manifest write failure")
                return real_write(path, payload)

            with mock.patch.object(capture_module, "_write_new", side_effect=fail_manifest):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as error:
                        capture([str(gold), "--rankings", str(ranking_path),
                                 "--output", str(result_path),
                                 "--manifest", str(manifest_path)])
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(result_path.exists())
            self.assertFalse(manifest_path.exists())

    def test_real_offline_lexical_retriever_capture_and_replay(self):
        """Actual lexical ranking, not IDs fabricated from golden labels."""
        class LexicalRetriever:
            def __init__(self, documents):
                self.documents = documents

            def retrieve(self, question, k):
                query_terms = set(question.lower().split())
                scores = []
                for doc_id, text in self.documents.items():
                    score = len(query_terms.intersection(text.lower().split()))
                    if score:
                        scores.append((-score, doc_id))
                return [doc_id for _score, doc_id in sorted(scores)[:k]]

        human_labels = [
            {"query_id": "privacy", "question": "delete my data",
             "category": "privacy", "critical": True,
             "retrieved_ids": [], "relevant_ids": ["privacy-guide"]},
            {"query_id": "warranty", "question": "warranty duration",
             "category": "support", "critical": False,
             "retrieved_ids": [], "relevant_ids": ["warranty-guide"]},
            {"query_id": "setup", "question": "install application",
             "category": "support", "critical": False,
             "retrieved_ids": [], "relevant_ids": ["setup-guide"]},
        ]
        baseline_index = {
            "privacy-guide": "delete my data privacy",
            "warranty-guide": "consumer protection policy",
            "setup-guide": "setup steps and instructions",
        }
        # Simulates a candidate re-indexing that improves two topics but drops
        # one critical source document: it must still be blocked by Guard.
        candidate_index = {
            "warranty-guide": "warranty duration",
            "setup-guide": "install application",
        }
        base = capture_from_retriever(LexicalRetriever(baseline_index), human_labels, 1)
        cand = capture_from_retriever(LexicalRetriever(candidate_index), human_labels, 1)
        self.assertEqual(base[0]["retrieved_ids"], ["privacy-guide"])
        self.assertEqual(cand[0]["retrieved_ids"], [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "golden.json").write_text(json.dumps(human_labels), encoding="utf-8")
            for name, rows in (("baseline", base), ("candidate", cand)):
                observed = [{"query_id": r["query_id"], "retrieved_ids": r["retrieved_ids"]}
                            for r in rows]
                (root / f"{name}-ranks.json").write_text(json.dumps(observed),
                                                        encoding="utf-8")
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(capture([
                        str(root / "golden.json"), "--rankings",
                        str(root / f"{name}-ranks.json"),
                        "--output", str(root / f"{name}.json")
                    ]), 0)
            policy = {"version": 1, "rules": [
                {"id": "aggregate", "select": {"type": "all"},
                 "metric": "ndcg_at_k", "min_delta": 0},
                {"id": "critical", "select": {"type": "critical"},
                 "metric": "hit_at_k", "min_query_score": 1,
                 "max_regressed_queries": 0},
            ]}
            (root / "policy.json").write_text(json.dumps(policy), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                code = replay([str(root / "candidate.json"), "--baseline",
                               str(root / "baseline.json"), "--policy",
                               str(root / "policy.json"), "--k", "1",
                               "--output", str(root / "report.json")])
            report = json.loads((root / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(code, 2)
            self.assertGreater(report["delta"]["ndcg_at_k"], 0)
            self.assertFalse(report["guard"]["passed"])
            self.assertIn("critical", report["guard"]["failed_rules"])


if __name__ == "__main__":
    unittest.main()
