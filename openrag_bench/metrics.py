"""Dependency-free, binary-relevance information retrieval metrics.

A duplicate returned document occupies a rank but does not earn relevance twice.
Callers working with labeled datasets should additionally use evaluate(), which
rejects duplicate IDs in the input.
"""
import math


def _check_k(k):
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer")


def _hits(retrieved, relevant, k):
    relevant_set = set(relevant)
    return len(set(retrieved[:k]) & relevant_set)


def precision_at_k(retrieved, relevant, k):
    """Precision uses the requested k as denominator even for shorter results."""
    _check_k(k)
    return _hits(retrieved, relevant, k) / k


def recall_at_k(retrieved, relevant, k):
    _check_k(k)
    relevant_set = set(relevant)
    return _hits(retrieved, relevant_set, k) / len(relevant_set) if relevant_set else 0.0


def reciprocal_rank(retrieved, relevant, k=None):
    """First relevant rank; pass k to limit the search to the first k results."""
    if k is not None:
        _check_k(k)
    relevant_set = set(relevant)
    ranked = retrieved if k is None else retrieved[:k]
    return next((1.0 / rank for rank, doc in enumerate(ranked, 1)
                 if doc in relevant_set), 0.0)


def hit_at_k(retrieved, relevant, k):
    _check_k(k)
    return float(_hits(retrieved, relevant, k) > 0)


def ndcg_at_k(retrieved, relevant, k):
    """Binary NDCG: repeated IDs never receive repeated relevance credit."""
    _check_k(k)
    relevant_set = set(relevant)
    seen = set()
    dcg = 0.0
    for rank, doc in enumerate(retrieved[:k], 1):
        if doc in seen:
            continue
        seen.add(doc)
        if doc in relevant_set:
            dcg += 1.0 / math.log2(rank + 1)
    ideal = sum(1.0 / math.log2(rank + 1)
                for rank in range(1, min(len(relevant_set), k) + 1))
    return dcg / ideal if ideal else 0.0


def average_precision_at_k(retrieved, relevant, k):
    """AP@k using min(k, number_of_relevant_documents) for normalization.

    Only the first occurrence of a relevant ID can earn credit; duplicates
    still occupy ranks. MAP@k is the macro average of this per-query score.
    """
    _check_k(k)
    relevant_set = set(relevant)
    denominator = min(len(relevant_set), k)
    if denominator == 0:
        return 0.0
    found = set()
    precision_sum = 0.0
    for rank, document in enumerate(retrieved[:k], 1):
        if document in relevant_set and document not in found:
            found.add(document)
            precision_sum += len(found) / rank
    return precision_sum / denominator


def graded_ndcg_at_k(retrieved, relevance_grades, k):
    """Graded NDCG@k with exponential gain 2**grade-1.

    Relevance grades must be integer levels between 0 and 31.
    Duplicated IDs contribute gain at their first occurrence only.
    """
    _check_k(k)
    if not isinstance(relevance_grades, dict):
        raise ValueError("relevance_grades must map document IDs to integer grades")
    for doc_id, grade in relevance_grades.items():
        if (not isinstance(doc_id, str) or not doc_id.strip() or
                not isinstance(grade, int) or isinstance(grade, bool) or
                grade < 0 or grade > 31):
            raise ValueError("relevance_grades require nonempty IDs and integer grades from 0 through 31")
    grades = relevance_grades
    observed = set()
    gain = 0.0
    for rank, doc_id in enumerate(retrieved[:k], 1):
        if doc_id not in observed:
            observed.add(doc_id)
            if grades.get(doc_id, 0) > 0:
                gain += (2 ** grades[doc_id] - 1) / math.log2(rank + 1)
    ideal_grades = sorted((grade for grade in grades.values() if grade > 0), reverse=True)[:k]
    ideal = sum((2 ** grade - 1) / math.log2(rank + 1)
                for rank, grade in enumerate(ideal_grades, 1))
    return gain / ideal if ideal else 0.0
