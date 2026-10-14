"""Offline, no-API Capture & Replay quickstart using original synthetic documents.

Run:
  python examples/quickstart_capture_replay.py --output-dir reports/quickstart

This demonstrates the workflow, NOT independently verified RAG quality.
The two simple retrievers rank their actual input documents; the human labels
are separate and never consulted to construct rankings.
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import re

from openrag_bench.capture import capture, capture_from_retriever, replay


TOKEN_RE = re.compile(r"[a-z0-9]+")

GOLDEN = [
    {"query_id": "q-privacy", "question": "delete my data", "category": "privacy",
     "critical": True, "relevant_ids": ["privacy-guide"], "retrieved_ids": [],
     "relevance_grades": {"privacy-guide": 2}},
    {"query_id": "q-setup", "question": "install application", "category": "support",
     "critical": False, "relevant_ids": ["setup-guide"], "retrieved_ids": [],
     "relevance_grades": {"setup-guide": 2}},
    {"query_id": "q-warranty", "question": "warranty duration", "category": "support",
     "critical": False, "relevant_ids": ["warranty-guide"], "retrieved_ids": [],
     "relevance_grades": {"warranty-guide": 2}},
]
POLICY = {"version": 1, "rules": [
    {"id": "aggregate-non-regression", "select": {"type": "all"},
     "metric": "ndcg_at_k", "min_delta": 0},
    {"id": "critical-privacy-hit", "select": {"type": "critical"},
     "metric": "hit_at_k", "min_query_score": 1, "max_regressed_queries": 0},
]}

# Changing retrieval source ownership is realistic: an index update may drop
# a privacy guide while improving normal search coverage. Every document
# description is original and intentionally tiny.
BASELINE_DOCUMENTS = {
    "privacy-guide": "delete my data",
    "misc-guide": "general customer contact",
}
CANDIDATE_DOCUMENTS = {
    "setup-guide": "install application",
    "warranty-guide": "warranty duration",
    "misc-guide": "general customer contact",
}


class KeywordRetriever:
    """A real (small) lexical retriever; does not consult relevance judgments."""

    def __init__(self, documents):
        self.documents = dict(documents)

    def retrieve(self, question, k):
        terms = set(TOKEN_RE.findall(question.lower()))
        ranked = []
        for doc_id, text in self.documents.items():
            overlap = len(terms.intersection(TOKEN_RE.findall(text.lower())))
            if overlap:
                ranked.append((-overlap, doc_id))
        return [doc_id for _negative_score, doc_id in sorted(ranked)[:k]]


def _write_new_json(path, value):
    with path.open("x", encoding="utf-8") as writer:
        json.dump(value, writer, indent=2, ensure_ascii=False, allow_nan=False)
        writer.write("\n")


def run_demo(output_dir):
    """Freeze observed results twice, replay Guard, and assert the expected block."""
    output_dir = Path(output_dir)
    # Never clobber old evidence. The directory is owned by this one demo.
    output_dir.mkdir(parents=True, exist_ok=False)
    golden_path = output_dir / "golden.json"
    policy_path = output_dir / "policy.json"
    _write_new_json(golden_path, GOLDEN)
    _write_new_json(policy_path, POLICY)

    for name, documents in (
        ("baseline", BASELINE_DOCUMENTS),
        ("candidate", CANDIDATE_DOCUMENTS),
    ):
        real_results = capture_from_retriever(KeywordRetriever(documents), GOLDEN, 1)
        observations = [
            {"query_id": row["query_id"], "retrieved_ids": row["retrieved_ids"]}
            for row in real_results
        ]
        observed_path = output_dir / f"{name}-observed.json"
        _write_new_json(observed_path, observations)
        with contextlib.redirect_stdout(io.StringIO()):
            status = capture([
                str(golden_path), "--rankings", str(observed_path),
                "--output", str(output_dir / f"{name}.json"),
                "--manifest", str(output_dir / f"{name}.manifest.json"),
            ])
        if status != 0:
            raise RuntimeError(f"{name} capture failed")

    report_path = output_dir / "guard.json"
    with contextlib.redirect_stdout(io.StringIO()):
        status = replay([
            str(output_dir / "candidate.json"),
            "--baseline", str(output_dir / "baseline.json"),
            "--policy", str(policy_path),
            "--k", "1",
            "--output", str(report_path),
            "--html", str(output_dir / "guard.html"),
        ])
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if (status != 2 or report["guard"]["passed"]
            or "critical-privacy-hit" not in report["guard"]["failed_rules"]
            or report["delta"]["ndcg_at_k"] <= 0):
        raise RuntimeError("Demo contract violated: macro improvement must be BLOCKED")

    return {
        "scenario": "original synthetic lexical retrieval only",
        "queries": report["count"],
        "baseline_ndcg_at_1": report["baseline"]["metrics"]["ndcg_at_k"],
        "candidate_ndcg_at_1": report["candidate"]["metrics"]["ndcg_at_k"],
        "overall_improved": report["delta"]["ndcg_at_k"] > 0,
        "guard_passed": report["guard"]["passed"],
        "failed_rules": report["guard"]["failed_rules"],
        "report": str(output_dir / "guard.html"),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/quickstart"),
                        help="New directory for synthetic local output (never overwritten)")
    args = parser.parse_args(argv)
    try:
        result = run_demo(args.output_dir)
    except (OSError, ValueError, RuntimeError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2, ensure_ascii=False))
    # A Guard block is the intentional *success* outcome of this demo.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
