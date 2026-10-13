"""Offline regression tests; the real SciFact archive is never bundled."""
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

from examples.scifact_benchmark import (
    LexicalIndex, load_scifact, run_scifact, save_results, file_digest, tokens,
    download_archive,
)


class SciFactBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.archive = self.folder / "fixture.zip"
        corpus = [
            {"_id": "a", "title": "Alpha science", "text": "Biology cells divide."},
            {"_id": "b", "title": "Beta chemistry", "text": "Chemistry studies molecules."},
            {"_id": "c", "title": "Gamma physics", "text": "Physics gravity motion."},
            {"_id": "d", "title": "Delta empty", "text": "A totally unrelated subject."},
        ]
        queries = [
            {"_id": "q1", "text": "cells biology"},
            {"_id": "q2", "text": "molecules chemistry"},
            {"_id": "q3", "text": "gravity physics"},
        ]
        with ZipFile(self.archive, "w") as archive:
            archive.writestr("scifact/corpus.jsonl",
                             "".join(json.dumps(v) + "\n" for v in corpus))
            archive.writestr("scifact/queries.jsonl",
                             "".join(json.dumps(v) + "\n" for v in queries))
            archive.writestr("scifact/qrels/test.tsv",
                             "query-id\tcorpus-id\tscore\n"
                             "q1\ta\t1\nq2\tb\t1\nq3\tc\t1\n")

    def test_load_archive_and_full_benchmark(self):
        docs, questions, labels = load_scifact(self.archive)
        self.assertEqual(len(docs), 4)
        self.assertEqual(len(questions), 3)
        self.assertEqual(labels["q2"], ["b"])
        outputs, comparison = run_scifact(docs, questions, labels, k=2)
        self.assertEqual(comparison["count"], 3)
        self.assertEqual(comparison["k"], 2)
        for name in ("tfidf", "bm25"):
            self.assertEqual(outputs[name]["count"], 3)
            self.assertEqual(outputs[name]["metrics"]["hit_at_k"], 1.0)
        out = save_results(self.folder / "results", docs, questions, labels,
                           outputs, comparison, self.archive)
        self.assertTrue((out / "bm25.run").is_file())
        self.assertTrue((out / "tfidf.run").is_file())
        self.assertTrue((out / "test.qrels").is_file())
        self.assertEqual(json.loads((out / "comparison.json").read_text())["documents"], 4)

    def test_determinism_and_rank_order(self):
        docs, questions, labels = load_scifact(self.archive)
        idx = LexicalIndex(docs)
        self.assertEqual(idx.search("biology cells", 1, "bm25")[0][0], "a")
        self.assertEqual(idx.search("biology cells", 1, "tfidf")[0][0], "a")
        a, report1 = run_scifact(docs, questions, labels, k=3)
        b, report2 = run_scifact(docs, questions, labels, k=3)
        self.assertEqual(report1, report2)
        self.assertEqual(a["bm25_rankings"], b["bm25_rankings"])

    def test_bad_qrels_unknown_document(self):
        with ZipFile(self.archive, "a") as archive:
            # Rebuilding rather than overwriting existing name avoids zip-duplicate ambiguity.
            pass
        bad = self.folder / "bad.zip"
        with ZipFile(bad, "w") as archive:
            archive.writestr("scifact/corpus.jsonl", '{"_id":"doc","text":"text"}\n')
            archive.writestr("scifact/queries.jsonl", '{"_id":"q","text":"q"}\n')
            archive.writestr("scifact/qrels/test.tsv",
                             "query-id\tcorpus-id\tscore\nq\tmissing\t1\n")
        with self.assertRaisesRegex(ValueError, "unknown query or document"):
            load_scifact(bad)

    def test_missing_query_term_and_input_rejections(self):
        idx = LexicalIndex({"a": "cats", "b": "dogs"})
        self.assertEqual(idx.search("unseenword", 10, "tfidf"), [])
        self.assertEqual(idx.search("unseenword", 10, "bm25"), [])
        self.assertEqual(tokens("İstanbul 2026!"), ["i", "stanbul", "2026"])
        with self.assertRaises(ValueError):
            idx.search("cats", 0, "bm25")
        with self.assertRaises(ValueError):
            idx.search("cats", 2, "unknown")

    def test_no_implicit_download_and_file_hashes(self):
        self.assertEqual(len(file_digest(self.archive)), 64)
        self.assertEqual(len(file_digest(self.archive, "md5")), 32)
        with self.assertRaises(FileExistsError):
            download_archive(self.archive)


if __name__ == "__main__":
    unittest.main()
