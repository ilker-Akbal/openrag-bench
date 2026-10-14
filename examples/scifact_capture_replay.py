"""Real BEIR SciFact retrieval -> Capture -> Guard Replay, using no model/API key.

The verified external archive is downloaded only with --download; its texts,
questions and per-query judgments remain in ignored local output files.
This does NOT turn the Studio demo labels into a real benchmark.

Usage:
  python examples/scifact_capture_replay.py --download --k 10
"""
import argparse
import contextlib
import io
import json
from pathlib import Path
import sys

from openrag_bench.capture import capture, capture_from_retriever, replay

if __package__:
    from .scifact_benchmark import (DATASET_MD5, LexicalIndex, download_archive,
                                    file_digest, load_scifact)
else:
    from scifact_benchmark import (DATASET_MD5, LexicalIndex, download_archive,
                                   file_digest, load_scifact)

OUTPUT_FILES = (
    "golden.json", "tfidf-observed.json", "bm25-observed.json",
    "tfidf-captured.json", "bm25-captured.json",
    "tfidf-manifest.json", "bm25-manifest.json",
    "policy.json", "guard.json", "guard.html",
)


class LexicalRetriever:
    """Wrap the actual indexed BM25/TF-IDF search behind the Capture protocol."""

    def __init__(self, index, method):
        if method not in ("tfidf", "bm25"):
            raise ValueError("method must be tfidf or bm25")
        self.index = index
        self.method = method

    def retrieve(self, question, k):
        return [doc_id for doc_id, _score in self.index.search(question, k, self.method)]


def capture_real_search(documents, questions, judgments, k):
    """Run both real lexical retrievers against independently provided qrels.

    Returns golden rows (without results) and two observed ranked datasets.
    The ground truth is never inferred from the rankings.
    """
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")
    if not documents or not questions or set(questions) != set(judgments):
        raise ValueError("Nonempty matching questions/judgment query IDs required")
    golden = []
    for query_id in sorted(questions):
        if not isinstance(query_id, str) or not query_id.strip():
            raise ValueError("Query IDs must be nonempty strings")
        relevant = judgments[query_id]
        if not isinstance(relevant, list) or not relevant or any(
                not isinstance(doc_id, str) or not doc_id.strip() or
                doc_id not in documents for doc_id in relevant):
            raise ValueError(f"Missing/invalid human qrels for query {query_id!r}")
        golden.append({
            "query_id": query_id,
            "question": questions[query_id],
            "retrieved_ids": [],
            "relevant_ids": relevant,
        })
    index = LexicalIndex(documents)
    observed = {}
    for method in ("tfidf", "bm25"):
        # Calls LexicalIndex.search for EVERY query, never derived from qrels.
        captured = capture_from_retriever(LexicalRetriever(index, method), golden, k)
        observed[method] = [
            {"query_id": row["query_id"], "retrieved_ids": row["retrieved_ids"]}
            for row in captured
        ]
    return golden, observed


def _write_new_json(path, obj):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def run_capture_replay(documents, questions, judgments, *, k, output_dir):
    """Write real rankings, freeze with Capture, re-evaluate via Guard Replay."""
    output_dir = Path(output_dir)
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("Output directory points to a file")
    if any((output_dir / name).exists() or (output_dir / name).is_symlink()
           for name in OUTPUT_FILES):
        raise ValueError("Output exists; refusing to overwrite prior capture evidence")

    golden, observed = capture_real_search(documents, questions, judgments, k)
    output_dir.mkdir(parents=True, exist_ok=True)
    golden_path = output_dir / "golden.json"
    _write_new_json(golden_path, golden)
    for method in ("tfidf", "bm25"):
        _write_new_json(output_dir / f"{method}-observed.json", observed[method])

    # The default policy only checks the aggregate non-regression. SciFact's
    # existing qrels have NO designated critical queries or Studio categories.
    # Do not fabricate critical flags from corpus or subject matter.
    policy = {"version": 1, "rules": [
        {"id": "ndcg-non-regression", "select": {"type": "all"},
         "metric": "ndcg_at_k", "min_delta": 0},
    ]}
    policy_path = output_dir / "policy.json"
    _write_new_json(policy_path, policy)

    for method in ("tfidf", "bm25"):
        args = [str(golden_path),
                "--rankings", str(output_dir / f"{method}-observed.json"),
                "--output", str(output_dir / f"{method}-captured.json"),
                "--manifest", str(output_dir / f"{method}-manifest.json")]
        with contextlib.redirect_stdout(io.StringIO()):
            if capture(args) != 0:
                raise RuntimeError("Capture returned a nonzero status")

    with contextlib.redirect_stdout(io.StringIO()):
        status = replay([
            str(output_dir / "bm25-captured.json"),
            "--baseline", str(output_dir / "tfidf-captured.json"),
            "--policy", str(policy_path),
            "--k", str(k),
            "--output", str(output_dir / "guard.json"),
            "--html", str(output_dir / "guard.html"),
        ])
    report = json.loads((output_dir / "guard.json").read_text(encoding="utf-8"))
    if report["count"] != len(golden) or bool(status == 0) != report["guard"]["passed"]:
        raise RuntimeError("Replay status and Guard report are inconsistent")
    return {
        "benchmark": "BEIR SciFact external qrels (not redistributed)",
        "documents": len(documents),
        "queries": len(golden),
        "k": k,
        "baseline": "TF-IDF cosine",
        "candidate": "BM25",
        "baseline_ndcg_at_k": report["baseline"]["metrics"]["ndcg_at_k"],
        "candidate_ndcg_at_k": report["candidate"]["metrics"]["ndcg_at_k"],
        "delta_ndcg_at_k": report["delta"]["ndcg_at_k"],
        "guard_passed": report["guard"]["passed"],
        "exit_code": status,
        "note": "Real lexical retrieval over external data; incomplete binary qrels. "
                "No quality, privacy, or safety guarantee beyond configured policy.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/scifact.zip"))
    parser.add_argument("--download", action="store_true",
                        help="Explicitly download and checksum-verify external SciFact archive")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/scifact-capture"))
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args(argv)
    if args.k < 1:
        parser.error("--k must be positive")
    try:
        if args.download and not args.archive.exists():
            download_archive(args.archive)
        if not args.archive.is_file() or file_digest(args.archive, "md5") != DATASET_MD5:
            raise ValueError("SciFact archive missing or checksum does not match BEIR")
        documents, questions, qrels = load_scifact(args.archive)
        summary = run_capture_replay(documents, questions, qrels,
                                     k=args.k, output_dir=args.output_dir)
        summary["archive_sha256"] = file_digest(args.archive)
    except (ValueError, TypeError, OSError) as exc:
        parser.error(str(exc))
    # Only aggregate numbers and checksum: never print individual query/doc text.
    print(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False))
    return summary["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
