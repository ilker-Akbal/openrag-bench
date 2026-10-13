"""Paired evaluation of two retriever outputs over identical relevance labels.

Confidence bounds use seeded, percentile paired-bootstrap resampling over
queries. They are descriptive uncertainty estimates, NOT significance tests.
"""
import random

from .cli import METRICS, evaluate


def _indexed(rows, description):
    result = {}
    for index, row in enumerate(rows):
        query_id = row.get("query_id")
        if not isinstance(query_id, str) or not query_id.strip():
            raise ValueError(
                f"{description} row {index}: query_id is required for comparisons")
        if query_id in result:
            raise ValueError(f"{description}: duplicate query_id {query_id!r}")
        result[query_id] = row
    return result


def _bootstrap_ci(differences, iterations=1000, seed=42):
    """95% percentile interval for the mean paired difference."""
    rng = random.Random(seed)
    count = len(differences)
    estimates = sorted(sum(differences[rng.randrange(count)]
                           for _ in range(count)) / count
                       for _ in range(iterations))

    def percentile(p):
        position = (iterations - 1) * p
        left = int(position)
        fraction = position - left
        return estimates[left] * (1 - fraction) + estimates[min(left + 1, iterations - 1)] * fraction

    return [percentile(0.025), percentile(0.975)]


def compare_rows(candidate_rows, baseline_rows, k):
    """Compare paired query results, refusing mismatched labels or query IDs."""
    candidate = evaluate(candidate_rows, k)
    baseline = evaluate(baseline_rows, k)
    cand_index = _indexed(candidate_rows, "candidate")
    base_index = _indexed(baseline_rows, "baseline")
    if set(cand_index) != set(base_index):
        missing = sorted(set(base_index) - set(cand_index))
        extra = sorted(set(cand_index) - set(base_index))
        raise ValueError(f"Query IDs differ; missing in candidate: {missing}; "
                         f"extra in candidate: {extra}")
    for query_id in base_index:
        if set(cand_index[query_id]["relevant_ids"]) != set(base_index[query_id]["relevant_ids"]):
            raise ValueError(f"Ground-truth relevant_ids differ for {query_id!r}")

    cand_scores = {row["query_id"]: row["metrics"] for row in candidate["per_query"]}
    base_scores = {row["query_id"]: row["metrics"] for row in baseline["per_query"]}
    ids = sorted(base_index)
    per_query = [{
        "query_id": query_id,
        "delta": {key: cand_scores[query_id][key] - base_scores[query_id][key]
                  for key in METRICS},
    } for query_id in ids]
    delta = {key: sum(row["delta"][key] for row in per_query) / len(ids)
             for key in METRICS}
    intervals = {key: _bootstrap_ci([row["delta"][key] for row in per_query])
                 for key in METRICS}
    return {
        "count": len(ids),
        "k": k,
        "baseline": baseline,
        "candidate": candidate,
        "delta": delta,
        "paired_bootstrap_95pct_ci": intervals,
        "bootstrap_note": "Seeded percentile paired bootstrap across queries; "
                          "descriptive only, not a test of significance.",
        "per_query_delta": per_query,
    }
