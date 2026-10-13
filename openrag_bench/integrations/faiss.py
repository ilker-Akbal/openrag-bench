"""Optional FAISS adapter without a hard FAISS or NumPy dependency.

FAISS indices and vector IDs are owned by the calling application. This
adapter has no telemetry, downloads or implicit index persistence.
"""
from typing import Callable, Sequence


class FaissRetriever:
    """Map FAISS's integer search positions back to document IDs.

    Assumes a positional FAISS index where result 0 maps to document_ids[0].
    If using an IndexIDMap with custom IDs, map those IDs explicitly instead
    of passing this adapter an unrelated document list.
    """

    def __init__(self, index, document_ids: Sequence[str],
                 embed_query: Callable[[str], Sequence[float]], *,
                 vector_factory=None):
        if not callable(getattr(index, "search", None)):
            raise TypeError("index must provide search(vectors, k)")
        if not callable(embed_query):
            raise TypeError("embed_query must be callable")
        if not isinstance(document_ids, (list, tuple)) or (
            any(not isinstance(doc, str) or not doc.strip() for doc in document_ids)
        ):
            raise ValueError("document_ids must be a list of non-empty strings")
        if len(set(document_ids)) != len(document_ids):
            raise ValueError("document_ids must be unique")
        if hasattr(index, "ntotal") and index.ntotal != len(document_ids):
            raise ValueError("FAISS index.ntotal must equal len(document_ids)")
        self.index = index
        self.document_ids = list(document_ids)
        self.embed_query = embed_query
        self.vector_factory = vector_factory

    def retrieve(self, query: str, k: int):
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(k, int) or isinstance(k, bool) or k < 1:
            raise ValueError("k must be a positive integer")
        vector = self.embed_query(query)
        if self.vector_factory is None:
            try:
                import numpy as np
            except ImportError as exc:
                raise ImportError("FAISS adapter requires numpy: pip install numpy faiss-cpu") from exc
            batch = np.asarray([vector], dtype="float32")
            if batch.ndim != 2 or batch.shape[0] != 1 or batch.shape[1] < 1:
                raise ValueError("embed_query must return a one-dimensional non-empty vector")
        else:
            batch = self.vector_factory([vector])
        _, positions = self.index.search(batch, k)
        if len(positions) != 1:
            raise ValueError("FAISS search must return exactly one query row")
        result = []
        seen = set()
        for raw in positions[0]:
            position = int(raw)
            if position == -1:
                continue  # FAISS signals missing neighbors this way.
            if position < 0 or position >= len(self.document_ids):
                raise ValueError(f"FAISS returned out-of-range index {position}")
            doc = self.document_ids[position]
            if doc not in seen:
                result.append(doc)
                seen.add(doc)
        return result
