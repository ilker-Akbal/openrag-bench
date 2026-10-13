import unittest

from openrag_bench.adapters import run_retriever
from openrag_bench.integrations.faiss import FaissRetriever


class FakeIndex:
    ntotal = 3

    def search(self, matrix, k):
        assert matrix == [[0.2, 0.3]]
        assert k == 4
        return [[.9, .7, .5, .0]], [[2, -1, 0, 2]]


class FaissIntegrationTests(unittest.TestCase):
    def make_retriever(self, index=None):
        return FaissRetriever(index or FakeIndex(),
                              ["doc-a", "doc-b", "doc-c"],
                              lambda query: [0.2, 0.3],
                              vector_factory=lambda rows: rows)

    def test_maps_positions_and_drops_missing_neighbors(self):
        retriever = self.make_retriever()
        self.assertEqual(retriever.retrieve("example query", 4),
                         ["doc-c", "doc-a"])

    def test_evaluates_retriever_end_to_end(self):
        retriever = self.make_retriever()
        report = run_retriever(retriever,
                               [{"question": "example", "relevant_ids": ["doc-c"]}], 4)
        self.assertEqual(report["metrics"]["hit_at_k"], 1)
        self.assertEqual(report["metrics"]["mrr_at_k"], 1)

    def test_rejects_bad_index_and_duplicate_ids(self):
        with self.assertRaises(ValueError):
            FaissRetriever(FakeIndex(), ["a", "a", "c"], lambda q: [1])
        with self.assertRaises(ValueError):
            FaissRetriever(FakeIndex(), ["a", "b"], lambda q: [1])
        with self.assertRaises(TypeError):
            FaissRetriever(object(), ["a"], lambda q: [1])
        with self.assertRaises(ValueError):
            self.make_retriever().retrieve("   ", 4)
        with self.assertRaises(ValueError):
            self.make_retriever().retrieve("hello", True)

    def test_rejects_out_of_range_position(self):
        class InvalidIndex:
            ntotal = 3

            def search(self, vectors, k):
                return [[0]], [[8]]
        with self.assertRaisesRegex(ValueError, "out-of-range"):
            self.make_retriever(InvalidIndex()).retrieve("question", 4)


if __name__ == "__main__":
    unittest.main()
