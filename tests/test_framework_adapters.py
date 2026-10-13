"""Framework adapter contract tests; no frameworks, APIs or downloads."""
from types import SimpleNamespace
import unittest

from openrag_bench.adapters import Retriever, run_retriever
from openrag_bench.integrations.frameworks import LangChainAdapter, LlamaIndexAdapter


class FakeLangChain:
    def __init__(self, documents):
        self.documents = documents
        self.queries = []

    def invoke(self, query):
        self.queries.append(query)
        return self.documents


class FakeLlamaIndex:
    def __init__(self, results):
        self.results = results

    def retrieve(self, query):
        return self.results


def doc(id_value, *, attr=False):
    if attr:
        return SimpleNamespace(metadata={}, id=id_value)
    return SimpleNamespace(metadata={"doc_id": id_value}, id=None)


def node(id_value, *, use_id_attribute=False):
    if use_id_attribute:
        inner = SimpleNamespace(id_=id_value)
    else:
        inner = SimpleNamespace(node_id=id_value)
    return SimpleNamespace(node=inner, score=0.75)


class AdapterTests(unittest.TestCase):
    def test_langchain_metadata_and_document_id(self):
        original = FakeLangChain([doc("a"), doc("b"), doc("c", attr=True)])
        adapter = LangChainAdapter(original)
        self.assertIsInstance(adapter, Retriever)
        self.assertEqual(adapter.retrieve("research question", 2), ["a", "b"])
        self.assertEqual(original.queries, ["research question"])
        self.assertEqual(adapter.retrieve("x", 3), ["a", "b", "c"])

    def test_langchain_custom_metadata_key(self):
        backend = FakeLangChain([
            SimpleNamespace(metadata={"source_id": "s1"}),
            SimpleNamespace(metadata={"source_id": "s2"}),
        ])
        adapter = LangChainAdapter(backend, metadata_id_key="source_id",
                                   allow_document_id=False)
        self.assertEqual(adapter.retrieve("x", 3), ["s1", "s2"])

    def test_llamaindex_node_ids_and_ranking(self):
        original = FakeLlamaIndex([node("d2"), node("d1", use_id_attribute=True)])
        adapter = LlamaIndexAdapter(original)
        self.assertIsInstance(adapter, Retriever)
        self.assertEqual(adapter.retrieve("prompt", 2), ["d2", "d1"])
        self.assertEqual(adapter.retrieve("prompt", 1), ["d2"])

    def test_comparison_report_from_both_adapters(self):
        questions = [{"query_id": "q1", "question": "biology",
                      "relevant_ids": ["doc-a"]}]
        lc = LangChainAdapter(FakeLangChain([doc("doc-x"), doc("doc-a")]))
        li = LlamaIndexAdapter(FakeLlamaIndex([node("doc-a"), node("doc-x")]))
        lc_report = run_retriever(lc, questions, k=2)
        li_report = run_retriever(li, questions, k=2)
        self.assertEqual(lc_report["metrics"]["hit_at_k"], 1)
        self.assertGreater(li_report["metrics"]["mrr_at_k"],
                           lc_report["metrics"]["mrr_at_k"])

    def test_rejects_invalid_retriever(self):
        with self.assertRaises(TypeError):
            LangChainAdapter(object())
        with self.assertRaises(TypeError):
            LlamaIndexAdapter(object())
        with self.assertRaises(ValueError):
            LangChainAdapter(FakeLangChain([]), metadata_id_key="")
        with self.assertRaises(ValueError):
            LangChainAdapter(FakeLangChain([])).retrieve("x", 0)
        with self.assertRaises(ValueError):
            LlamaIndexAdapter(FakeLlamaIndex([])).retrieve("x", True)

    def test_rejects_missing_duplicate_and_invalid_ids(self):
        bad_lc = (
            [doc("a"), doc("a")],
            [SimpleNamespace(metadata={})],
            [doc(42)],
            [SimpleNamespace(metadata={"doc_id": " "})],
        )
        for docs in bad_lc:
            with self.subTest(docs=docs), self.assertRaises(ValueError):
                LangChainAdapter(FakeLangChain(docs)).retrieve("x", 3)
        for nodes in ([node("a"), node("a")],
                      [SimpleNamespace(node=None)],
                      [node(42)]):
            with self.subTest(nodes=nodes), self.assertRaises(ValueError):
                LlamaIndexAdapter(FakeLlamaIndex(nodes)).retrieve("x", 3)

    def test_invalid_iterables_and_no_hidden_dependencies(self):
        with self.assertRaisesRegex(ValueError, "iterable"):
            LangChainAdapter(FakeLangChain(None)).retrieve("x", 2)
        with self.assertRaisesRegex(ValueError, "iterable"):
            LlamaIndexAdapter(FakeLlamaIndex("string")).retrieve("x", 2)


if __name__ == "__main__":
    unittest.main()
