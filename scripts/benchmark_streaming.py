"""Reproducible synthetic workload for JSONL summary peak-memory measurements.

No customer input and no model downloads. Reports time + tracemalloc peak
allocated Python memory for BOTH exact modes on the same file.
"""
import argparse
import json
import os
from pathlib import Path
import platform
import tempfile
import time
import tracemalloc

from openrag_bench.cli import evaluate
from openrag_bench.io import read_rows
from openrag_bench.streaming import evaluate_jsonl_stream


def profile(run):
    tracemalloc.start()
    start = time.perf_counter()
    try:
        result = run()
        seconds = time.perf_counter() - start
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, {"seconds": round(seconds, 5),
                    "python_peak_bytes": peak,
                    "python_peak_mib": round(peak / (1024 * 1024), 3)}


def run_benchmark(queries):
    if queries < 1:
        raise ValueError("queries must be positive")
    with tempfile.TemporaryDirectory() as workspace:
        path = Path(workspace) / "original_synthetic.jsonl"
        with path.open("w", encoding="utf-8") as dest:
            for index in range(queries):
                ids = ["a", "b"] if index % 2 else ["b", "a"]
                row = {"query_id": f"q-{index:09d}", "retrieved_ids": ids,
                       "relevant_ids": ["a"]}
                dest.write(json.dumps(row, separators=(",", ":")) + "\n")
        streamed, stream_stats = profile(lambda: evaluate_jsonl_stream(path, 2))
        batched, batch_stats = profile(lambda: evaluate(read_rows(path), 2))
    for metric in batched["metrics"]:
        if abs(streamed["metrics"][metric] - batched["metrics"][metric]) > 1e-9:
            raise AssertionError(f"Metric parity failed for {metric}")
    if streamed["count"] != queries or batched["count"] != queries:
        raise AssertionError("Query count changed")
    if not stream_stats["python_peak_bytes"] < batch_stats["python_peak_bytes"]:
        raise AssertionError("Streaming did not use less Python peak memory than full batch")
    return {
        "synthetic_queries": queries, "python": platform.python_version(),
        "runner": os.getenv("RUNNER_OS", "local"),
        "run_commit": os.getenv("GITHUB_SHA", "local"),
        "streaming": stream_stats,
        "in_memory": batch_stats,
        "python_peak_memory_ratio": round(
            stream_stats["python_peak_bytes"] / batch_stats["python_peak_bytes"], 6),
        "metric_parity_tolerance": 1e-9,
        "tests_passed": True,
        "caveat": "Synthetic workload; tracemalloc tracks Python allocations, not OS RSS. Timings are run/environment-specific.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=int, default=100000)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    result = run_benchmark(args.queries)
    payload = json.dumps(result, indent=2) + "\n"
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
