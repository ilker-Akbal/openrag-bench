"""End-to-end SciFact dense-embedding + FAISS retrieval against a BM25 baseline.

Heavy dependencies and pretrained model weights are OPTIONAL and downloaded
only when a user invokes this example. See docs/DENSE_SCIFACT.md.

Install: python -m pip install -e '.[dense]'
Run:     python examples/scifact_dense_faiss.py --archive data/scifact.zip

Outputs contain no dataset corpus. Result JSON includes questions; keep private.
"""
import argparse
import json
from pathlib import Path
import sys

from openrag_bench.cli import evaluate
from openrag_bench.comparison import compare_rows
from examples.scifact_benchmark import (
    DATASET_MD5, LexicalIndex, download_archive, file_digest, load_scifact,
)

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
MODEL_REVISION = "c21050a7ef692090620a6d037dd736908f9c7cf6"


def build_rows(questions, relevance, rankings, k):
    """Shared alignment contract for dense and BM25 result lists."""
    if set(questions) != set(relevance) or set(questions) != set(rankings):
        raise ValueError("Query IDs must match between questions, labels and rankings")
    rows = []
    for query_id in sorted(questions):
        pairs = rankings[query_id]
        ids = [item[0] for item in pairs]
        if len(ids) != len(set(ids)) or any(
            not isinstance(doc_id, str) or not doc_id for doc_id in ids
        ):
            raise ValueError(f"Invalid or duplicate retrieved IDs for {query_id}")
        rows.append({"query_id": query_id, "question": questions[query_id],
                     "retrieved_ids": ids[:k], "relevant_ids": relevance[query_id]})
    return rows


def dense_search(documents, questions, k, *, model_id=MODEL_ID,
                 model_revision=MODEL_REVISION, batch_size=32, device="cpu"):
    """Return sorted top-k document IDs using dense MiniLM + exact FAISS IP."""
    try:
        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:
        raise RuntimeError("Install dense extras first: python -m pip install -e '.[dense]'") from exc

    model = SentenceTransformer(model_id, revision=model_revision,
                                device=device, trust_remote_code=False)
    document_ids = sorted(documents)
    query_ids = sorted(questions)
    corpus_texts = [documents[doc_id] for doc_id in document_ids]
    query_texts = [questions[query_id] for query_id in query_ids]
    vectors = np.asarray(model.encode(
        corpus_texts, batch_size=batch_size, normalize_embeddings=True,
        convert_to_numpy=True, show_progress_bar=True), dtype="float32")
    if vectors.ndim != 2 or vectors.shape[0] != len(document_ids):
        raise ValueError("Invalid corpus embeddings")
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(np.ascontiguousarray(vectors))
    query_vectors = np.asarray(model.encode(
        query_texts, batch_size=batch_size, normalize_embeddings=True,
        convert_to_numpy=True, show_progress_bar=True), dtype="float32")
    scores, positions = index.search(np.ascontiguousarray(query_vectors), k)
    result = {}
    for index, query_id in enumerate(query_ids):
        pairs = [(document_ids[int(position)], float(score))
                 for score, position in zip(scores[index], positions[index])
                 if 0 <= int(position) < len(document_ids)]
        result[query_id] = sorted(pairs, key=lambda pair: (-pair[1], pair[0]))
    return result


def run_dense(docs, questions, relevant, k, *, dense_function=dense_search, **kwargs):
    """Compare dense retrieval and BM25 with the identical query labels."""
    lexical = LexicalIndex(docs)
    bm25 = {qid: lexical.search(question, k, "bm25")
            for qid, question in sorted(questions.items())}
    dense = dense_function(docs, questions, k, **kwargs)
    bm25_rows = build_rows(questions, relevant, bm25, k)
    dense_rows = build_rows(questions, relevant, dense, k)
    report = compare_rows(dense_rows, bm25_rows, k)
    return {"bm25": bm25, "dense": dense, "comparison": report}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/scifact.zip"))
    parser.add_argument("--download", action="store_true",
                        help="Download checksum-verified official SciFact archive if missing")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/scifact-dense"))
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--model-id", default=MODEL_ID)
    parser.add_argument("--revision", default=MODEL_REVISION)
    args = parser.parse_args(argv)
    if args.k < 1 or args.batch_size < 1:
        parser.error("--k and --batch-size must be positive")
    if args.download and not args.archive.exists():
        download_archive(args.archive)
    if not args.archive.is_file() or file_digest(args.archive, "md5") != DATASET_MD5:
        parser.error("SciFact archive missing or its MD5 differs from the official BEIR dataset")
    docs, queries, relevant = load_scifact(args.archive)
    result = run_dense(docs, queries, relevant, args.k,
                       model_id=args.model_id, model_revision=args.revision,
                       batch_size=args.batch_size, device=args.device)
    dest = args.output_dir
    dest.mkdir(parents=True, exist_ok=True)
    comparison = result["comparison"]
    metadata = {
        "dataset": "BEIR SciFact test",
        "dataset_sha256": file_digest(args.archive),
        "documents": len(docs), "queries": len(queries), "k": args.k,
        "embedding_model": args.model_id, "embedding_revision": args.revision,
        "embedding_normalization": "l2",
        "index": "FAISS IndexFlatIP (exact cosine similarity)",
        "baseline": "BM25 (k1=1.2,b=0.75)",
        "comparison": comparison,
        "limitations": "Retrieval relevance, incomplete binary qrels, no significance claim"
    }
    (dest / "comparison.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for method in ("bm25", "dense"):
        with (dest / f"{method}.run").open("w", encoding="utf-8") as writer:
            for query_id in sorted(queries):
                for rank, (doc_id, score) in enumerate(result[method][query_id], 1):
                    writer.write(f"{query_id} Q0 {doc_id} {rank} {score:.10f} {method}\n")
    print(json.dumps({
        "documents": len(docs), "queries": len(queries), "k": args.k,
        "baseline_bm25": comparison["baseline"]["metrics"],
        "dense_minilm": comparison["candidate"]["metrics"],
        "delta_dense_minus_bm25": comparison["delta"],
        "report_directory": str(dest)
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
