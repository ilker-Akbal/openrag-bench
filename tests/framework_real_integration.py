"""Optional installed-framework integration tests (NOT in default test_*.py).

Environment:
OPENRAG_REAL_FRAMEWORK=langchain  or  OPENRAG_REAL_FRAMEWORK=llamaindex
"""
import os
import unittest

from examples.framework_real_integration import (
    DOCUMENTS, EXPECTED, QUESTIONS, keyword_vector, verify_framework,
)


class RealFrameworkTests(unittest.TestCase):
    def test_synthetic_vectors_are_unambiguous(self):
        for (_, content), row in zip(DOCUMENTS, QUESTIONS):
            document_vector = keyword_vector(content)
            question_vector = keyword_vector(row["question"])
            self.assertEqual(document_vector.index(max(document_vector)),
                             question_vector.index(max(question_vector)))
            self.assertEqual(sum(x > 0 for x in question_vector), 1)
        self.assertEqual(
            len(set(tuple(keyword_vector(t)) for _, t in DOCUMENTS)), 3
        )

    def test_real_vector_store_through_openrag_bench_adapter(self):
        framework = os.environ.get("OPENRAG_REAL_FRAMEWORK")
        self.assertIn(framework, ("langchain", "llamaindex"),
                      "Set OPENRAG_REAL_FRAMEWORK in the optional CI job")
        actual = verify_framework(framework)
        self.assertTrue(actual["tests_passed"])
        self.assertEqual(actual["top_1_document_ids"], list(EXPECTED))
        self.assertEqual(actual["query_count"], 3)
        self.assertEqual(actual["document_count"], 3)
        self.assertEqual(actual["metrics_at_1"]["ndcg_at_k"], 1.0)
        self.assertEqual(actual["metrics_at_1"]["map_at_k"], 1.0)
        self.assertEqual(len(actual["corpus_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
