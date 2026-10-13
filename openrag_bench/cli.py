"""Strictly validate and evaluate offline retrieval datasets.

The input is a JSON array of rows. Each row contains retrieved_ids and
relevant_ids; query_id is required only for paired comparisons.
"""
import argparse
import json
from pathlib import Path

from .metrics import hit_at_k, ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank

METRICS = ("precision_at_k", "recall_at_k", "hit_at_k", "mrr_at_k",
           "reciprocal_rank", "ndcg_at_k")


def _validate(rows, k):
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Dataset must be a non-empty JSON array")
    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"Row {i} must be a JSON object")
        for field in ("retrieved_ids", "relevant_ids"):
            ids = row.get(field)
            if not isinstance(ids, list) or any(
                    not isinstance(v, str) or not v.strip() for v in ids):
                raise ValueError(f"Row {i}: {field} must be a list of non-empty strings")
            if len(ids) != len(set(ids)):
                raise ValueError(f"Row {i}: duplicate document IDs in {field}")
        for field in ("query_id", "question"):
            if field in row and (not isinstance(row[field], str) or
                                  not row[field].strip()):
                raise ValueError(f"Row {i}: {field} must be a non-empty string")


def evaluate(rows, k):
    """Return macro-averaged metrics, with equal weight given to each query."""
    _validate(rows, k)
    scores = []
    for row in rows:
        retrieved, relevant = row["retrieved_ids"], row["relevant_ids"]
        scores.append({
            "precision_at_k": precision_at_k(retrieved, relevant, k),
            "recall_at_k": recall_at_k(retrieved, relevant, k),
            "hit_at_k": hit_at_k(retrieved, relevant, k),
            "mrr_at_k": reciprocal_rank(retrieved, relevant, k),
            "reciprocal_rank": reciprocal_rank(retrieved, relevant),
            "ndcg_at_k": ndcg_at_k(retrieved, relevant, k),
        })
    return {
        "count": len(rows), "k": k,
        "metrics": {key: sum(x[key] for x in scores) / len(scores)
                    for key in METRICS},
        "per_query": [{
            "query_id": row.get("query_id"),
            "question": row.get("question"),
            "metrics": score,
        } for row, score in zip(rows, scores)],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Evaluate or compare ranked retrieval results (offline)")
    parser.add_argument("dataset", type=Path, help="Candidate JSON dataset")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--baseline", type=Path,
                        help="Baseline dataset with matching query_id and ground truth")
    parser.add_argument("--metric", choices=METRICS, default="ndcg_at_k",
                        help="Metric used by --min-delta (default: ndcg_at_k)")
    parser.add_argument("--min-delta", type=float,
                        help="Fail if candidate mean minus baseline mean falls below this")
    parser.add_argument("--output", type=Path, help="Write machine-readable JSON report")
    parser.add_argument("--html", type=Path, help="Write standalone HTML report")
    args = parser.parse_args(argv)
    if args.min_delta is not None and not args.baseline:
        parser.error("--min-delta requires --baseline")
    if args.min_delta is not None:
        import math
        if not math.isfinite(args.min_delta):
            parser.error("--min-delta must be finite")

    try:
        candidate = json.loads(args.dataset.read_text(encoding="utf-8"))
        if args.baseline:
            from .comparison import compare_rows
            baseline = json.loads(args.baseline.read_text(encoding="utf-8"))
            report = compare_rows(candidate, baseline, args.k)
        else:
            report = evaluate(candidate, args.k)
    except (ValueError, KeyError, TypeError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    if args.baseline:
        report["gate"] = {"metric": args.metric, "min_delta": args.min_delta,
                          "passed": (args.min_delta is None or
                                     report["delta"][args.metric] >= args.min_delta)}
    rendered = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    if args.html:
        from .html_report import render_html
        args.html.write_text(render_html(report), encoding="utf-8")
    print(rendered)
    if args.baseline and not report["gate"]["passed"]:
        parser.exit(2, f"Regression gate failed: {args.metric} delta "
                       f"{report['delta'][args.metric]:+.6f} < {args.min_delta:+.6f}\n")
    return 0


if __name__ == "__main__":
    main()
