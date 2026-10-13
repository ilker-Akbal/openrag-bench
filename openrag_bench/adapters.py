"""Protocol and helpers for integrating retrieval pipelines."""
from typing import Protocol, Sequence, runtime_checkable

@runtime_checkable
class Retriever(Protocol):
    def retrieve(self, query: str, k: int) -> Sequence[str]:
        """Return ranked unique document IDs."""

def run_retriever(retriever: Retriever, questions, k: int):
    """Evaluate an existing retriever using labeled question rows.

    Each row requires question and relevant_ids; retrieved_ids are generated.
    """
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer")
    if not isinstance(questions, list) or not questions:
        raise ValueError("questions must be a non-empty list")
    rows = []
    for i, row in enumerate(questions):
        if not isinstance(row, dict) or not isinstance(row.get("question"), str) or not row["question"]:
            raise ValueError(f"row {i}: question must be a non-empty string")
        if not isinstance(row.get("relevant_ids"), list):
            raise ValueError(f"row {i}: relevant_ids must be a list")
        retrieved = list(retriever.retrieve(row["question"], k))
        payload = {"question": row["question"], "relevant_ids": row["relevant_ids"],
                   "retrieved_ids": retrieved}
        if "query_id" in row:
            payload["query_id"] = row["query_id"]
        rows.append(payload)
    from .cli import evaluate
    return evaluate(rows, k)
