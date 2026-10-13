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
