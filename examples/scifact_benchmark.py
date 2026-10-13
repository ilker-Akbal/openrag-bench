"""Reproducible local SciFact retrieval benchmark (BM25 versus TF-IDF).

Downloads the **official BEIR SciFact archive only if --download is requested**.
The archive is checked against the BEIR-published MD5. Nothing from the dataset
is copied into this source repository. See docs/BENCHMARK_SCIFACT.md.

Usage:
  python examples/scifact_benchmark.py --download --k 10 --output-dir reports/scifact

Only Python's standard library + the installed openrag_bench package are used.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import re
import sys
from urllib.request import urlopen
from zipfile import ZipFile

from openrag_bench.cli import evaluate
from openrag_bench.comparison import compare_rows

DATASET_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip"
# Published in https://github.com/beir-cellar/beir/wiki/Datasets-available
DATASET_MD5 = "5f7d1de60b170fc8027bb7898e2efca1"
TOKEN_RE = re.compile(r"[a-z0-9]+")
MAX_DOWNLOAD_BYTES = 20_000_000
MAX_UNCOMPRESSED_BYTES = 30_000_000


def tokens(text):
    return TOKEN_RE.findall(text.lower())


def file_digest(path, algorithm="sha256"):
    digest = hashlib.new(algorithm)
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1_048_576), b""):
            digest.update(chunk)
    return digest.hexdigest()


def download_archive(destination):
    """Fetch the BEIR archive, writing only after checksum verification."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing archive: {destination}")
    candidate = destination.with_suffix(destination.suffix + ".download")
    if candidate.exists():
        raise FileExistsError(f"Temporary download already exists: {candidate}")
    digest = hashlib.md5()  # nosec: checksum of known public dataset, not authentication
    count = 0
    try:
        with urlopen(DATASET_URL, timeout=45) as remote, candidate.open("xb") as output:
            while True:
                chunk = remote.read(262_144)
                if not chunk:
                    break
                count += len(chunk)
                if count > MAX_DOWNLOAD_BYTES:
                    raise ValueError("Download exceeds maximum expected dataset size")
                digest.update(chunk)
                output.write(chunk)
        if digest.hexdigest() != DATASET_MD5:
            raise ValueError("Official BEIR SciFact checksum mismatch")
        candidate.replace(destination)
    finally:
        candidate.unlink(missing_ok=True)
    return destination


def _archive_member(archive, name):
    candidates = [member for member in archive.infolist()
                  if member.filename.strip("/") in (name, "scifact/" + name)]
    if len(candidates) != 1:
        raise ValueError(f"Expected exactly one {name!r} in SciFact archive")
    member = candidates[0]
    if member.is_dir() or member.file_size > MAX_UNCOMPRESSED_BYTES:
        raise ValueError(f"Unexpected size or type for archive member {name}")
    return member


def _jsonl(archive, path):
    data = {}
    raw = archive.read(_archive_member(archive, path))
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        item = json.loads(line)
        doc_id = str(item["_id"])
        if not doc_id or doc_id in data:
            raise ValueError(f"Invalid or duplicate ID in {path} line {line_number}")
        data[doc_id] = item
    return data


def load_scifact(path):
    """Read corpus, test queries and qrels from the official BEIR ZIP format."""
    with ZipFile(path) as archive:
        corpus_data = _jsonl(archive, "corpus.jsonl")
        query_data = _jsonl(archive, "queries.jsonl")
        raw_qrels = archive.read(_archive_member(archive, "qrels/test.tsv"))
    qrels = defaultdict(dict)
    for line_number, line in enumerate(raw_qrels.decode("utf-8").splitlines(), 1):
        if line_number == 1 and line.startswith("query-id"):
            continue
        if not line.strip():
            continue
        fields = line.split("\t")
        if len(fields) != 3:
            raise ValueError(f"qrels line {line_number}: expected three tab-separated fields")
        query_id, doc_id, score_text = fields
        score = int(score_text)
        if query_id not in query_data or doc_id not in corpus_data:
            raise ValueError(f"qrels line {line_number}: unknown query or document ID")
        if doc_id in qrels[query_id]:
            raise ValueError(f"qrels line {line_number}: duplicate judgment")
        qrels[query_id][doc_id] = score
    if not corpus_data or not qrels:
        raise ValueError("SciFact corpus or test qrels are empty")
    documents = {
        doc_id: (str(doc.get("title") or "") + " " + str(doc.get("text") or "")).strip()
        for doc_id, doc in corpus_data.items()
    }
    questions = {query_id: str(query_data[query_id]["text"]) for query_id in qrels}
    relevant = {query_id: sorted(doc_id for doc_id, grade in judgments.items() if grade > 0)
                for query_id, judgments in qrels.items()}
    return documents, questions, relevant


class LexicalIndex:
    """Inverted-index TF-IDF and BM25 with deterministic document-ID tie breaks."""

    def __init__(self, corpus):
        if not corpus:
            raise ValueError("Corpus cannot be empty")
        self.ids = sorted(corpus)
        self.postings = defaultdict(list)
        self.lengths = []
        self.doc_tf = []
        self.n = len(self.ids)
        for index, doc_id in enumerate(self.ids):
            freq = Counter(tokens(corpus[doc_id]))
            self.doc_tf.append(freq)
            self.lengths.append(sum(freq.values()))
            for term, tf in freq.items():
                self.postings[term].append((index, tf))
        self.avgdl = max(sum(self.lengths) / self.n, 1e-9)
        self.idf_tfidf = {t: math.log((self.n + 1) / (len(p) + 1)) + 1
                          for t, p in self.postings.items()}
        self.idf_bm25 = {t: math.log(1 + (self.n - len(p) + 0.5) / (len(p) + 0.5))
                         for t, p in self.postings.items()}
        self.norms = []
        for freq in self.doc_tf:
            square = sum(((1 + math.log(tf)) * self.idf_tfidf[term]) ** 2
                         for term, tf in freq.items())
            self.norms.append(math.sqrt(square))

    def search(self, query, k, method):
        if method not in ("tfidf", "bm25"):
            raise ValueError("Unsupported retrieval method")
        if not isinstance(k, int) or k < 1:
            raise ValueError("k must be positive")
        qtf = Counter(tokens(query))
        scores = defaultdict(float)
        if method == "bm25":
            for term in qtf:
                idf = self.idf_bm25.get(term, 0.0)
                for doc_idx, tf in self.postings.get(term, ()):
                    denom = tf + 1.2 * (0.25 + 0.75 * self.lengths[doc_idx] / self.avgdl)
                    scores[doc_idx] += idf * tf * 2.2 / denom
        else:
            qweights = {term: (1 + math.log(freq)) * self.idf_tfidf[term]
                        for term, freq in qtf.items() if term in self.idf_tfidf}
            qnorm = math.sqrt(sum(value ** 2 for value in qweights.values()))
            for term, weight in qweights.items():
                idf = self.idf_tfidf[term]
                for doc_idx, tf in self.postings[term]:
                    scores[doc_idx] += weight * (1 + math.log(tf)) * idf
            if qnorm:
                for doc_idx in scores:
                    norm = self.norms[doc_idx] * qnorm
                    scores[doc_idx] = scores[doc_idx] / norm if norm else 0
        ranked = sorted(scores, key=lambda index: (-scores[index], self.ids[index]))
        return [(self.ids[index], scores[index]) for index in ranked[:k]]


def run_scifact(documents, questions, relevant, k=10):
    """Generate comparable rows and scored TREC runs over exactly the same qrels."""
    index = LexicalIndex(documents)
    outputs = {}
    rows_by_method = {}
    for method in ("tfidf", "bm25"):
        rows = []
        rankings = {}
        for query_id in sorted(questions):
            ranked = index.search(questions[query_id], k, method)
            rankings[query_id] = ranked
            rows.append({"query_id": query_id, "question": questions[query_id],
                         "retrieved_ids": [doc for doc, score in ranked],
                         "relevant_ids": relevant[query_id]})
        outputs[method] = evaluate(rows, k)
        rows_by_method[method] = rows
        outputs[method + "_rankings"] = rankings
    comparison = compare_rows(rows_by_method["bm25"], rows_by_method["tfidf"], k)
    return outputs, comparison


def save_results(output_dir, documents, questions, relevant, outputs, comparison, archive):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = {
        "benchmark": "BEIR SciFact test",
        "dataset_source": DATASET_URL,
        "dataset_archive_md5": file_digest(archive, "md5"),
        "dataset_archive_sha256": file_digest(archive),
        "documents": len(documents),
        "queries": len(questions),
        "k": comparison["k"],
        "baseline": "TF-IDF cosine",
        "candidate": "BM25 (k1=1.2, b=0.75)",
        "comparison": comparison,
        "limitations": "Lexical retrieval only. Binary qrels; unjudged documents "
                       "are treated as nonrelevant; no significance claim.",
    }
    (output_dir / "comparison.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    for method in ("tfidf", "bm25"):
        with (output_dir / f"{method}.run").open("w", encoding="utf-8") as handle:
            for query_id in sorted(questions):
                for rank, (doc_id, score) in enumerate(outputs[method + "_rankings"][query_id], 1):
                    handle.write(f"{query_id} Q0 {doc_id} {rank} {score:.10f} {method}\n")
    with (output_dir / "test.qrels").open("w", encoding="utf-8") as handle:
        for query_id in sorted(relevant):
            for doc_id in relevant[query_id]:
                handle.write(f"{query_id} 0 {doc_id} 1\n")
    return output_dir


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path("data/scifact.zip"))
    parser.add_argument("--download", action="store_true",
                        help="Download official SciFact ZIP if it does not exist")
    parser.add_argument("--output-dir", type=Path, default=Path("reports/scifact"))
    parser.add_argument("--k", type=int, default=10)
    args = parser.parse_args(argv)
    if args.k < 1:
        parser.error("--k must be positive")
    if args.download and not args.archive.is_file():
        print(f"Downloading verified SciFact archive to {args.archive}")
        download_archive(args.archive)
    if not args.archive.is_file():
        parser.error(f"Dataset missing: {args.archive}. Use --download or provide --archive")
    if file_digest(args.archive, "md5") != DATASET_MD5:
        parser.error("Archive MD5 does not match BEIR's published SciFact checksum")
    docs, queries, qrels = load_scifact(args.archive)
    outputs, comparison = run_scifact(docs, queries, qrels, args.k)
    folder = save_results(args.output_dir, docs, queries, qrels, outputs, comparison,
                          args.archive)
    print(json.dumps({"documents": len(docs), "queries": len(queries), "k": args.k,
                      "tfidf": outputs["tfidf"]["metrics"],
                      "bm25": outputs["bm25"]["metrics"],
                      "delta": comparison["delta"],
                      "output_dir": str(folder)}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
