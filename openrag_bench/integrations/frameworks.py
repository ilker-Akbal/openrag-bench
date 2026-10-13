"""Lightweight interoperability for LangChain and LlamaIndex retrievers.

No imports of LangChain, LlamaIndex, model weights or hosted services occur
here. Pass an existing, already configured retriever to an adapter.

Both adapters produce a ranked list of stable document IDs and intentionally
reject duplicate/missing IDs to prevent silent metric corruption.
"""
from collections.abc import Iterable
from itertools import islice


def _check_k(k):
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer")


def _nonempty_id(value, *, backend):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{backend}: document must have a non-empty string ID")
    return value


def _as_documents(items, k, *, backend):
    if not isinstance(items, Iterable) or isinstance(items, (str, bytes, dict)):
        raise ValueError(f"{backend}: retriever must return an iterable of documents")
    return islice(items, k)


def _unique_ids(documents, *, backend, id_resolver):
    ids = []
    seen = set()
    for document in documents:
        doc_id = _nonempty_id(id_resolver(document), backend=backend)
        if doc_id in seen:
            raise ValueError(f"{backend}: duplicate retrieved document ID {doc_id!r}")
        seen.add(doc_id)
        ids.append(doc_id)
    return ids


class LangChainAdapter:
    """Adapt an existing LangChain BaseRetriever / vector-store retriever.

    Uses doc.metadata[metadata_id_key] if present; optionally falls back to
    the document's .id attribute. IDs must be stable across retrieval runs.
    LangChain retrievers generally have a fixed search_kwargs k; this adapter
    truncates any extra output but does not change the upstream retriever.
    """

    def __init__(self, retriever, *, metadata_id_key="doc_id", allow_document_id=True):
        if not callable(getattr(retriever, "invoke", None)):
            raise TypeError("LangChain retriever must have an invoke(query) method")
        if not isinstance(metadata_id_key, str) or not metadata_id_key.strip():
            raise ValueError("metadata_id_key must be a non-empty string")
        self.retriever = retriever
        self.metadata_id_key = metadata_id_key
        self.allow_document_id = allow_document_id

    def retrieve(self, query: str, k: int):
        _check_k(k)

        def document_id(document):
            metadata = getattr(document, "metadata", None)
            if isinstance(metadata, dict) and self.metadata_id_key in metadata:
                return metadata[self.metadata_id_key]
            if self.allow_document_id:
                return getattr(document, "id", None)
            return None

        result = self.retriever.invoke(query)
        return _unique_ids(
            _as_documents(result, k, backend="LangChain"),
            backend="LangChain", id_resolver=document_id,
        )


class LlamaIndexAdapter:
    """Adapt an existing LlamaIndex retriever returning NodeWithScore nodes.

    Looks for .node.node_id or .node.id_, the commonly exposed stable IDs.
    Configure the underlying retriever's similarity_top_k when creating it.
    """

    def __init__(self, retriever):
        if not callable(getattr(retriever, "retrieve", None)):
            raise TypeError("LlamaIndex retriever must have a retrieve(query) method")
        self.retriever = retriever

    def retrieve(self, query: str, k: int):
        _check_k(k)

        def node_id(item):
            node = getattr(item, "node", None)
            if node is None:
                return None
            value = getattr(node, "node_id", None)
            if value is not None:
                return value
            return getattr(node, "id_", None)

        result = self.retriever.retrieve(query)
        return _unique_ids(
            _as_documents(result, k, backend="LlamaIndex"),
            backend="LlamaIndex", id_resolver=node_id,
        )
