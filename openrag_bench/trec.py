"""Read standard TREC six-column run and four-column qrels files.

All queries present in qrels are evaluated, including those with no run
results. Relevance is binary: judgments greater than zero count as relevant.
No data or network dependencies are bundled.
"""
import math
from pathlib import Path


def _lines(path):
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        clean = line.strip()
        if clean and not clean.startswith("#"):
            yield number, clean.split()


def load_qrels(path, *, with_grades=False):
    """Parse qrels, optionally preserving positive integer relevance grades."""
    judgments = {}
    for line_number, cols in _lines(path):
        if len(cols) != 4:
            raise ValueError(f"qrels line {line_number}: expected four fields")
        query_id, _iteration, doc_id, value = cols
        try:
            grade = int(value)
        except ValueError as exc:
            raise ValueError(f"qrels line {line_number}: relevance must be an integer") from exc
        if with_grades and grade > 31:
            raise ValueError(f"qrels line {line_number}: graded relevance cannot exceed 31")
        seen = judgments.setdefault(query_id, {})
        if doc_id in seen:
            raise ValueError(f"qrels line {line_number}: duplicate judgment for {query_id}/{doc_id}")
        seen[doc_id] = grade
    if not judgments:
        raise ValueError("qrels must include at least one judged query")
    if with_grades:
        return {query_id: {doc: grade for doc, grade in scores.items() if grade > 0}
                for query_id, scores in judgments.items()}
    return {query_id: sorted(doc for doc, grade in scores.items() if grade > 0)
            for query_id, scores in judgments.items()}


def load_trec_run(path, qrels_path, *, graded=False):
    """Produce validated evaluator rows from a TREC run and qrels file.

    Run format: query_id Q0 doc_id rank score run_id
    Query sets are defined by qrels to avoid inflated scores from omitted
    queries. Unknown query IDs in the run are an error, not silently ignored.
    """
    qrels = load_qrels(qrels_path, with_grades=graded)
    ranked = {query_id: [] for query_id in qrels}
    ids = {query_id: set() for query_id in qrels}
    ranks = {query_id: set() for query_id in qrels}
    for number, cols in _lines(path):
        if len(cols) != 6:
            raise ValueError(f"run line {number}: expected six fields")
        query_id, _q0, doc_id, position, raw_score, _run_id = cols
        if query_id not in qrels:
            raise ValueError(f"run line {number}: query_id {query_id!r} absent from qrels")
        try:
            rank = int(position)
            score = float(raw_score)
        except ValueError as exc:
            raise ValueError(f"run line {number}: invalid rank or score") from exc
        if rank < 1 or not math.isfinite(score):
            raise ValueError(f"run line {number}: positive rank and finite score required")
        if doc_id in ids[query_id]:
            raise ValueError(f"run line {number}: duplicate document for {query_id!r}")
        if rank in ranks[query_id]:
            raise ValueError(f"run line {number}: duplicate rank for {query_id!r}")
        ids[query_id].add(doc_id)
        ranks[query_id].add(rank)
        ranked[query_id].append((rank, doc_id))

    result = []
    for query_id, labels in sorted(qrels.items()):
        row = {
            "query_id": query_id,
            "retrieved_ids": [doc_id for _rank, doc_id in sorted(ranked[query_id])],
            "relevant_ids": sorted(labels) if graded else labels,
        }
        if graded:
            row["relevance_grades"] = labels
        result.append(row)
    return result
