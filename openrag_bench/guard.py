"""Fail-closed, dependency-free quality policies for paired retrieval outputs.

Policies use only stable query IDs, boolean critical flags, optional categories
and already computed retrieval relevance metrics. No LLM judge or API required.
"""
import math

from .cli import METRICS
from .comparison import compare_rows

RULE_FIELDS = frozenset({
    "id", "select", "metric", "min_delta", "min_score",
    "min_query_score", "max_regressed_queries",
})
SELECT_TYPES = frozenset(("all", "critical", "category", "query_ids"))
EPSILON = 1e-12


def _number(value, name, *, zero_to_one=False):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not math.isfinite(number) or (zero_to_one and not 0 <= number <= 1):
        raise ValueError(f"{name} must be finite" + (" and between 0 and 1" if zero_to_one else ""))
    return number


def validate_policy(policy):
    if not isinstance(policy, dict) or set(policy) != {"version", "rules"}:
        raise ValueError("Policy must contain exactly version and rules")
    if type(policy["version"]) is not int or policy["version"] != 1:
        raise ValueError("Policy version must be integer 1")
    rules = policy["rules"]
    if not isinstance(rules, list) or not rules:
        raise ValueError("Policy rules must be a non-empty list")
    names = set()
    for index, rule in enumerate(rules):
        location = f"Rule {index}"
        if not isinstance(rule, dict) or not {"id", "select", "metric"} <= set(rule):
            raise ValueError(f"{location} requires id, select and metric")
        if set(rule) - RULE_FIELDS:
            raise ValueError(f"{location} has unsupported fields")
        name = rule["id"]
        if not isinstance(name, str) or not name.strip() or len(name) > 100 or name in names:
            raise ValueError(f"{location} id must be unique and nonempty (max 100 chars)")
        names.add(name)
        if rule["metric"] not in METRICS:
            raise ValueError(f"{location} metric must be a supported retrieval metric")
        select = rule["select"]
        if not isinstance(select, dict) or select.get("type") not in SELECT_TYPES:
            raise ValueError(f"{location} select.type must be all, critical, category or query_ids")
        selector = select["type"]
        if selector in ("all", "critical") and set(select) != {"type"}:
            raise ValueError(f"{location} {selector} selector accepts no other fields")
        if selector == "category" and (set(select) != {"type", "value"}
                                       or not isinstance(select.get("value"), str)
                                       or not select["value"].strip()):
            raise ValueError(f"{location} category requires a nonempty value")
        if selector == "query_ids":
            ids = select.get("ids")
            if (set(select) != {"type", "ids"} or not isinstance(ids, list)
                    or not ids or any(not isinstance(v, str) or not v.strip() for v in ids)
                    or len(set(ids)) != len(ids)):
                raise ValueError(f"{location} query_ids requires unique nonempty string IDs")
        thresholds = set(rule) & {
            "min_delta", "min_score", "min_query_score", "max_regressed_queries",
        }
        if not thresholds:
            raise ValueError(f"{location} must specify at least one quality threshold")
        for key in ("min_delta", "min_score", "min_query_score"):
            if key in rule:
                _number(rule[key], f"{location}.{key}",
                        zero_to_one=key != "min_delta")
        if "max_regressed_queries" in rule:
            limit = rule["max_regressed_queries"]
            if type(limit) is not int or limit < 0:
                raise ValueError(f"{location}.max_regressed_queries must be a nonnegative integer")
    return policy


def _metadata(candidate, baseline):
    """Pair exact metadata; no absent/changed critical and category flags."""
    def indexed(rows, side):
        result = {}
        for row in rows:
            key = row.get("query_id")
            if not isinstance(key, str) or not key.strip() or key in result:
                raise ValueError(f"{side} requires unique nonempty query_id")
            if "critical" in row and type(row["critical"]) is not bool:
                raise ValueError(f"{side} {key!r}: critical must be a boolean")
            if "category" in row and (not isinstance(row["category"], str)
                                      or not row["category"].strip()):
                raise ValueError(f"{side} {key!r}: category must be a nonempty string")
            result[key] = row
        return result
    c, b = indexed(candidate, "candidate"), indexed(baseline, "baseline")
    if set(c) != set(b):
        raise ValueError("Candidate and baseline query IDs do not match")
    for query_id in c:
        for key in ("critical", "category"):
            if c[query_id].get(key) != b[query_id].get(key):
                raise ValueError(f"Metadata {key} differs for {query_id!r}")
    return c


def _select_ids(rule, metadata):
    select = rule["select"]
    kind = select["type"]
    if kind == "all":
        ids = sorted(metadata)
    elif kind == "critical":
        ids = sorted(k for k, row in metadata.items() if row.get("critical") is True)
    elif kind == "category":
        ids = sorted(k for k, row in metadata.items()
                     if row.get("category") == select["value"])
    else:
        requested = set(select["ids"])
        missing = sorted(requested - set(metadata))
        if missing:
            raise ValueError(f"Rule {rule['id']!r}: query IDs are missing: {missing[:10]}")
        ids = sorted(requested)
    if not ids:
        raise ValueError(f"Rule {rule['id']!r}: selector matched no queries")
    if any(not metadata[q]["relevant_ids"] for q in ids):
        raise ValueError(f"Rule {rule['id']!r}: selected queries must have positive judgments")
    return ids


def guard_comparison(candidate_rows, baseline_rows, policy, k):
    """Validate, evaluate, diagnose and enforce a strict policy.

    Returns a report stripped of raw question contents and document IDs.
    For a failing policy, callers should write reports and exit nonzero.
    """
    validate_policy(policy)
    compared = compare_rows(candidate_rows, baseline_rows, k)
    metadata = _metadata(candidate_rows, baseline_rows)
    base_scores = {x["query_id"]: x["metrics"] for x in compared["baseline"]["per_query"]}
    cand_scores = {x["query_id"]: x["metrics"] for x in compared["candidate"]["per_query"]}
    results = []
    for rule in policy["rules"]:
        ids = _select_ids(rule, metadata)
        metric = rule["metric"]
        baseline_mean = sum(base_scores[q][metric] for q in ids) / len(ids)
        candidate_mean = sum(cand_scores[q][metric] for q in ids) / len(ids)
        delta = candidate_mean - baseline_mean
        regressed = sorted(q for q in ids
                           if cand_scores[q][metric] < base_scores[q][metric] - EPSILON)
        per_query_limit = rule.get("min_query_score")
        below_threshold = (sorted(q for q in ids
                            if cand_scores[q][metric] < per_query_limit - EPSILON)
                           if per_query_limit is not None else [])
        reasons = []
        if "min_delta" in rule and delta < rule["min_delta"] - EPSILON:
            reasons.append("min_delta")
        if "min_score" in rule and candidate_mean < rule["min_score"] - EPSILON:
            reasons.append("min_score")
        if ("max_regressed_queries" in rule
                and len(regressed) > rule["max_regressed_queries"]):
            reasons.append("max_regressed_queries")
        if below_threshold:
            reasons.append("min_query_score")
        results.append({
            "id": rule["id"], "selector": rule["select"],
            "metric": metric, "query_count": len(ids),
            "baseline_mean": baseline_mean, "candidate_mean": candidate_mean,
            "delta": delta, "regressed_count": len(regressed),
            "regressed_query_ids": regressed[:20],
            "below_min_query_score_count": len(below_threshold),
            "below_min_query_score_ids": below_threshold[:20],
            "passed": not reasons, "failed_thresholds": reasons,
        })
    # One lookup per query: rank observations, not causal explanations.
    candidate_ranked = {row["query_id"]: row["retrieved_ids"] for row in candidate_rows}
    baseline_ranked = {row["query_id"]: row["retrieved_ids"] for row in baseline_rows}
    for item in compared["per_query_delta"]:
        key = item["query_id"]
        relevant = set(metadata[key]["relevant_ids"])
        candidate_rank = next(
            (i for i, doc in enumerate(candidate_ranked[key], 1)
             if doc in relevant), None)
        baseline_rank = next(
            (i for i, doc in enumerate(baseline_ranked[key], 1)
             if doc in relevant), None)
        diag = item["diagnostics"]
        diag["baseline_first_relevant_rank"] = baseline_rank
        diag["candidate_first_relevant_rank"] = candidate_rank
        diag["lost_top_k_hit"] = bool(baseline_rank and baseline_rank <= k and
                                      (candidate_rank is None or candidate_rank > k))
        diag["gained_top_k_hit"] = bool(candidate_rank and candidate_rank <= k and
                                        (baseline_rank is None or baseline_rank > k))
        diag["rank_drop"] = (candidate_rank - baseline_rank if
                            baseline_rank is not None and candidate_rank is not None else None)
    # Avoid accidentally publishing questions embedded in old evaluate() output.
    for key in ("baseline", "candidate"):
        compared[key]["per_query"] = [
            {"query_id": row["query_id"], "metrics": row["metrics"],
             "diagnostics": row["diagnostics"]}
            for row in compared[key]["per_query"]
        ]
    compared["guard"] = {
        "passed": all(item["passed"] for item in results),
        "rules": results, "failed_rules": [item["id"] for item in results
                                          if not item["passed"]],
        "note": "Policy evaluation is deterministic. Rank changes are observations, "
                "not proof of a particular root cause.",
    }
    return compared
