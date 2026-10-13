import unittest
from openrag_bench.adapters import run_retriever
from openrag_bench.html_report import render_html

class FakeRetriever:
    def retrieve(self, query, k):
        return ["doc-a", "doc-b"][:k]

class AdapterTests(unittest.TestCase):
    def test_retriever_integration(self):
        result = run_retriever(FakeRetriever(), [{"question": "example", "relevant_ids": ["doc-a"]}], 2)
        self.assertEqual(result["metrics"]["recall_at_k"], 1.0)
    def test_query_id_is_preserved(self):
        report = run_retriever(FakeRetriever(),
            [{"query_id":"q-01","question":"example","relevant_ids":["doc-a"]}], 2)
        self.assertEqual(report["per_query"][0]["query_id"], "q-01")

    def test_invalid_query(self):
        with self.assertRaises(ValueError):
            run_retriever(FakeRetriever(), [{"question": "", "relevant_ids": []}], 1)
    def test_html_escapes_untrusted_question(self):
        report = {"count": 1, "k": 1, "metrics": {"hit_at_k": 1.0},
                  "per_query": [{"question": "<script>alert(1)</script>", "metrics": {"hit_at_k": 1.0}}]}
        html = render_html(report)
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

if __name__ == "__main__":
    unittest.main()
