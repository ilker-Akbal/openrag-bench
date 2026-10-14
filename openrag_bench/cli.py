"""Strictly validate and evaluate offline JSON, JSONL and TREC datasets.

Rows contain retrieved_ids and relevant_ids; query_id is required only for
paired comparisons. TREC run files require --qrels.
"""
import argparse
import json
from pathlib import Path

from .metrics import (average_precision_at_k, graded_ndcg_at_k, hit_at_k,
                      ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank)

METRICS = ("precision_at_k", "recall_at_k", "hit_at_k", "mrr_at_k",
           "reciprocal_rank", "ndcg_at_k", "map_at_k", "graded_ndcg_at_k")


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
        if "relevance_grades" in row:
            grades = row["relevance_grades"]
            if not isinstance(grades, dict) or set(grades) != set(row["relevant_ids"]):
                raise ValueError(
                    f"Row {i}: relevance_grades must map exactly the relevant_ids")
            if any(not isinstance(grade, int) or isinstance(grade, bool) or
                   not 1 <= grade <= 31 for grade in grades.values()):
                raise ValueError(f"Row {i}: positive integer grades must be in 1..31")
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
        grades = row.get("relevance_grades", {doc_id: 1 for doc_id in relevant})
        scores.append({
            "precision_at_k": precision_at_k(retrieved, relevant, k),
            "recall_at_k": recall_at_k(retrieved, relevant, k),
            "hit_at_k": hit_at_k(retrieved, relevant, k),
            "mrr_at_k": reciprocal_rank(retrieved, relevant, k),
            "reciprocal_rank": reciprocal_rank(retrieved, relevant),
            "ndcg_at_k": ndcg_at_k(retrieved, relevant, k),
            "map_at_k": average_precision_at_k(retrieved, relevant, k),
            "graded_ndcg_at_k": graded_ndcg_at_k(retrieved, grades, k),
        })
    return {
        "count": len(rows), "k": k,
        "metrics": {key: sum(x[key] for x in scores) / len(scores)
                    for key in METRICS},
        "per_query": [{
            "query_id": row.get("query_id"),
            "question": row.get("question"),
            "metrics": score,
            "diagnostics": {
                "retrieved_count": len(row["retrieved_ids"]),
                "judged_positive_count": len(row["relevant_ids"]),
                "hits_at_k": len(set(row["retrieved_ids"][:k]) & set(row["relevant_ids"])),
            },
        } for row, score in zip(rows, scores)],
    }


def main(argv=None):
    import sys
    supplied = sys.argv[1:] if argv is None else list(argv)
    if supplied and supplied[0] in ("capture", "replay"):
        from . import capture as capture_module
        return getattr(capture_module, supplied[0])(supplied[1:])
    if supplied and supplied[0] == "studio":
        from .studio import studio
        return studio(supplied[1:])
    if supplied and supplied[0] in ("init", "doctor", "guard"):
        from . import commands
        return getattr(commands, supplied[0])(supplied[1:])
    parser = argparse.ArgumentParser(
        description="Evaluate or compare ranked retrieval results (offline)",
        epilog="Subcommands: init, doctor, guard, studio, capture (ranked retrieval), replay (Guard).")
    parser.add_argument("dataset", type=Path, help="Candidate JSON or TREC run file")
    parser.add_argument("--input-format", choices=("auto", "json", "jsonl"),
                        default="auto", help="Select JSON array or JSON Lines; auto uses filename extension")
    parser.add_argument("--qrels", type=Path,
                        help="TREC qrels file; interpret inputs as six-column TREC runs")
    parser.add_argument("--graded-qrels", action="store_true",
                        help="Preserve positive graded qrels for graded NDCG (requires --qrels)")
    parser.add_argument("--k", type=int, default=3)
    parser.add_argument("--baseline", type=Path,
                        help="Baseline dataset with matching query_id and ground truth")
    parser.add_argument("--metric", choices=METRICS, default="ndcg_at_k",
                        help="Metric used by --min-delta (default: ndcg_at_k)")
    parser.add_argument("--min-delta", type=float,
                        help="Fail if candidate mean minus baseline mean falls below this")
    parser.add_argument("--output", type=Path, help="Write machine-readable JSON report")
    parser.add_argument("--html", type=Path, help="Write standalone HTML report")
    parser.add_argument("--csv", type=Path, help="Write per-query spreadsheet-safe CSV (excludes question text)")
    parser.add_argument("--streaming-summary", action="store_true",
                        help="Evaluate JSONL incrementally; output aggregate metrics without per-query rows")
    args = parser.parse_args(supplied)
    if args.streaming_summary:
        if args.baseline or args.qrels or args.graded_qrels or args.csv or args.html:
            parser.error("--streaming-summary supports JSONL summary only; no --baseline, --qrels, --csv or --html")
        if args.input_format == "json" or (args.input_format == "auto" and
             args.dataset.suffix.lower() not in (".jsonl", ".ndjson")):
            parser.error("--streaming-summary requires a .jsonl/.ndjson file or --input-format jsonl")
    if args.graded_qrels and not args.qrels:
        parser.error("--graded-qrels requires --qrels")
    if args.qrels and args.input_format != "auto":
        parser.error("--input-format applies to JSON/JSONL only; omit it with --qrels")
    if args.min_delta is not None and not args.baseline:
        parser.error("--min-delta requires --baseline")
    if args.min_delta is not None:
        import math
        if not math.isfinite(args.min_delta):
            parser.error("--min-delta must be finite")

    try:
        if args.streaming_summary:
            from .streaming import evaluate_jsonl_stream
            report = evaluate_jsonl_stream(args.dataset, args.k)
        elif args.qrels:
            from .trec import load_trec_run
            candidate = load_trec_run(args.dataset, args.qrels, graded=args.graded_qrels)
        else:
            from .io import read_rows
            candidate = read_rows(args.dataset, input_format=args.input_format)
        if args.streaming_summary:
            pass
        elif args.baseline:
            from .comparison import compare_rows
            if args.qrels:
                baseline = load_trec_run(args.baseline, args.qrels, graded=args.graded_qrels)
            else:
                baseline = read_rows(args.baseline, input_format=args.input_format)
            report = compare_rows(candidate, baseline, args.k)
        elif not args.streaming_summary:
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
    if args.csv:
        from .csv_report import render_csv
        args.csv.write_text(render_csv(report), encoding="utf-8-sig")
    print(rendered)
    if args.baseline and not report["gate"]["passed"]:
        parser.exit(2, f"Regression gate failed: {args.metric} delta "
                       f"{report['delta'][args.metric]:+.6f} < {args.min_delta:+.6f}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
