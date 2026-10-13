"""Real, completely offline LangChain/LlamaIndex vector-store integration.

Run with one installed optional backend:
    python examples/framework_real_integration.py --framework langchain
    python examples/framework_real_integration.py --framework llamaindex

Original three-dimensional keyword vectors are synthetic. This tests actual
framework interoperability, NOT semantic retrieval quality.
"""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

from openrag_bench.adapters import run_retriever
from openrag_bench.integrations.frameworks import LangChainAdapter, LlamaIndexAdapter

TOPICS = (
    ("planet", "orbit", "star"),
    ("forest", "tree", "leaf"),
    ("database", "query", "index"),
)
DOCUMENTS = (
    ("doc-space", "planet orbit star"),
    ("doc-nature", "forest tree leaf"),
    ("doc-sql", "database query index"),
)
QUESTIONS = (
    {"query_id": "q-space", "question": "planet", "relevant_ids": ["doc-space"]},
    {"query_id": "q-nature", "question": "forest", "relevant_ids": ["doc-nature"]},
    {"query_id": "q-sql", "question": "database", "relevant_ids": ["doc-sql"]},
)
EXPECTED = ("doc-space", "doc-nature", "doc-sql")


def keyword_vector(text):
    words = set(text.casefold().split())
    return [float(len(words.intersection(group))) for group in TOPICS]


def build_langchain():
    """Construct real Documents, Embeddings and InMemoryVectorStore."""
    from langchain_core.documents import Document
    from langchain_core.embeddings import Embeddings
    from langchain_core.vectorstores import InMemoryVectorStore

    class LocalKeywordEmbeddings(Embeddings):
        def embed_query(self, text):
            return keyword_vector(text)

        def embed_documents(self, texts):
            return [keyword_vector(text) for text in texts]

    store = InMemoryVectorStore(embedding=LocalKeywordEmbeddings())
    documents = [
        Document(page_content=text, metadata={"doc_id": doc_id}, id=doc_id)
        for doc_id, text in DOCUMENTS
    ]
    store.add_documents(documents)
    return LangChainAdapter(
        store.as_retriever(search_type="similarity", search_kwargs={"k": 3}),
        allow_document_id=False,
    )


def build_llamaindex():
    """Construct real TextNodes, BaseEmbedding and VectorStoreIndex."""
    from llama_index.core import VectorStoreIndex
    from llama_index.core.embeddings import BaseEmbedding
    from llama_index.core.schema import TextNode

    class LocalKeywordEmbedding(BaseEmbedding):
        def _get_text_embedding(self, text):
            return keyword_vector(text)

        def _get_query_embedding(self, query):
            return keyword_vector(query)

        async def _aget_query_embedding(self, query):
            return keyword_vector(query)

    nodes = [TextNode(text=text, id_=doc_id) for doc_id, text in DOCUMENTS]
    index = VectorStoreIndex(nodes=nodes, embed_model=LocalKeywordEmbedding())
    return LlamaIndexAdapter(index.as_retriever(similarity_top_k=3))


def verify_framework(name):
    """Perform actual indexed retrieval followed by labeled evaluation."""
    if name not in ("langchain", "llamaindex"):
        raise ValueError("framework must be langchain or llamaindex")
    adapter = build_langchain() if name == "langchain" else build_llamaindex()
    top_ids = [adapter.retrieve(row["question"], k=1)[0] for row in QUESTIONS]
    if tuple(top_ids) != EXPECTED:
        raise AssertionError(f"{name} vector retrieval produced unexpected IDs: {top_ids!r}")
    report = run_retriever(adapter, list(QUESTIONS), k=1)
    if report["count"] != len(QUESTIONS):
        raise AssertionError("Evaluated query count changed")
    for metric in ("precision_at_k", "recall_at_k", "hit_at_k", "mrr_at_k",
                   "map_at_k", "ndcg_at_k", "graded_ndcg_at_k"):
        if report["metrics"][metric] != 1.0:
            raise AssertionError(f"{name}: expected {metric}=1 for synthetic exact matches")
    for got, expected in zip(report["per_query"], QUESTIONS):
        if got["query_id"] != expected["query_id"]:
            raise AssertionError("Query alignment was not preserved")

    package = "langchain-core" if name == "langchain" else "llama-index-core"
    corpus_hash = hashlib.sha256(
        json.dumps(DOCUMENTS, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "framework": name,
        "framework_package": package,
        "framework_version": importlib.metadata.version(package),
        "python": platform.python_version(),
        "vector_store": ("LangChain InMemoryVectorStore" if name == "langchain"
                         else "LlamaIndex VectorStoreIndex"),
        "embedding": "synthetic local 3D keyword vector",
        "query_count": len(QUESTIONS),
        "document_count": len(DOCUMENTS),
        "corpus_sha256": corpus_hash,
        "top_1_document_ids": top_ids,
        "metrics_at_1": report["metrics"],
        "tests_passed": True,
        "limitation": "Framework compatibility only, not semantic model quality",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--framework", required=True, choices=("langchain", "llamaindex"))
    parser.add_argument("--output", type=Path, help="Optional aggregate-only JSON report")
    args = parser.parse_args(argv)
    report = verify_framework(args.framework)
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
