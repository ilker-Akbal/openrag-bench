"""Dense pipeline contract tests without torch, NumPy, FAISS or network."""
import unittest

from examples.scifact_dense_faiss import build_rows, run_dense


class DenseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.docs = {"a": "blue planets and galaxies", "b": "green plants biology",
                     "c": "heavy gravity around stars"}
        self.questions = {"q1": "planets blue", "q2": "gravity stars"}
        self.relevant = {"q1": ["a"], "q2": ["c"]}

    def test_rows_are_aligned_and_sorted(self):
        ranked = {"q2": [("c", .99)], "q1": [("a", .97)]}
        rows = build_rows(self.questions, self.relevant, ranked, k=2)
        self.assertEqual([r["query_id"] for r in rows], ["q1", "q2"])
        self.assertEqual(rows[0]["retrieved_ids"], ["a"])

    def test_dense_vs_bm25_mock(self):
        def fake_dense(documents, questions, k):
            return {"q1": [("a", .9)], "q2": [("c", .8)]}
        comparison = run_dense(self.docs, self.questions, self.relevant, k=1,
                               dense_function=fake_dense)["comparison"]
        self.assertEqual(comparison["count"], 2)
        self.assertEqual(comparison["candidate"]["metrics"]["hit_at_k"], 1.0)

    def test_misaligned_ids_and_duplicates_fail(self):
        with self.assertRaisesRegex(ValueError, "must match"):
            build_rows(self.questions, self.relevant, {"q1": []}, 2)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_rows(self.questions, self.relevant,
                       {"q1": [("a", 1), ("a", .8)], "q2": []}, 2)


if __name__ == "__main__":
    unittest.main()
