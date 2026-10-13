"""True bounded-memory JSONL summary evaluation.

The module retains only a running sum of fixed-size metric names and one
decoded JSONL row. It intentionally does NOT provide paired comparisons,
bootstrap intervals, per-query reports or HTML/CSV exports.
"""
from pathlib import Path

from .cli import METRICS, evaluate
from .io import iter_jsonl


def evaluate_jsonl_stream(path, k):
    """Accumulate exact macro metrics from JSONL without storing all queries.

    Complexity: memory O(max input row + output metrics); time linear in
    the number of retrieved IDs, judged IDs and queries.
    """
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be a positive integer")
    totals = {metric: 0.0 for metric in METRICS}
    count = 0
    source = Path(path)
    for lineno, row in iter_jsonl(source):
        try:
            result = evaluate([row], k)
        except ValueError as exc:
            raise ValueError(f"{source}: invalid evaluation row on line {lineno}: {exc}") from exc
        count += 1
        scores = result["metrics"]
        for metric in METRICS:
            totals[metric] += scores[metric]

    return {
        "count": count,
        "k": k,
        "metrics": {metric: score / count for metric, score in totals.items()},
        "evaluation_mode": "streaming_jsonl_summary",
        "limitations": "No per-query export or paired bootstrap; metrics use ordinary floating-point running sums.",
    }
