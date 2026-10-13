"""Reproduce Turkish article retrieval on a real externally labeled dataset.

Data: RizgarOzan/turkish-rag-eval, 54 Wikipedia articles, 58 human-labeled
questions in its original health-only BEIR-compatible set.
Dataset CC BY-SA 4.0: this MIT code only downloads the data at runtime.
The repository deliberately DOES NOT redistribute its corpus or questions.

Default eval uses a local folder with corpus.jsonl, queries.jsonl and
qrels/test.jsonl. --download pulls a *pinned revision* into an ephemeral
TemporaryDirectory. Only aggregate measurements and hashes are emitted.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import tempfile
import unicodedata
from urllib.request import Request, urlopen

from openrag_bench.cli import evaluate
from openrag_bench.comparison import compare_rows

DATASET = "RizgarOzan/turkish-rag-eval"
DATASET_REVISION = "d166363bd8d906154b56fbb7009787f2a8591fbe"
DATA_FILES = ("corpus.jsonl", "queries.jsonl", "qrels/test.jsonl")
BASE = f"https://huggingface.co/datasets/{DATASET}/resolve/{DATASET_REVISION}"
MAX_BYTES = {"corpus.jsonl": 5_000_000, "queries.jsonl": 100_000,
             "qrels/test.jsonl": 100_000}
WORD = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(text, method):
    """Unicode-aware tokens; Turkish-mode folds dotted/dotless I deliberately."""
    if not isinstance(text, str):
        raise ValueError("Tokenized text must be a string")
    if method not in ("unicode_casefold", "turkish_case"):
        raise ValueError("Unknown tokenizer method")
    text = unicodedata.normalize("NFKC", text)
    if method == "turkish_case":
        text = text.replace("I", "ı").replace("İ", "i").lower()
    else:
        text = text.casefold()
    return WORD.findall(text)


def download_dataset(folder):
    """Download three pinned external files only; no data enters git artifacts."""
    folder = Path(folder)
    hashes = {}
    for relative in DATA_FILES:
        url = f"{BASE}/{relative}"
        request = Request(url, headers={"User-Agent": "OpenRAG-Bench/0.3 benchmark"})
        try:
            with urlopen(request, timeout=75) as response:
                content = response.read(MAX_BYTES[relative] + 1)
        except OSError as exc:
            raise RuntimeError(f"Cannot retrieve pinned dataset file {relative}: {exc}") from exc
        if len(content) > MAX_BYTES[relative]:
            raise ValueError(f"External file {relative} exceeds declared maximum size")
        content.decode("utf-8")
        target = folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        hashes[relative] = hashlib.sha256(content).hexdigest()
    return hashes


def _lines(path):
    with Path(path).open("r", encoding="utf-8-sig") as file:
        for number, line in enumerate(file, 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}: invalid JSON on line {number}") from exc
            if not isinstance(entry, dict):
                raise ValueError(f"{path}: expected JSON object on line {number}")
            yield entry


def load_dataset(folder):
    root = Path(folder)
    documents, questions, labels = {}, {}, {}
    for row in _lines(root / "corpus.jsonl"):
        doc_id = row.get("_id")
        if not isinstance(doc_id, str) or not doc_id or doc_id in documents:
            raise ValueError("Corpus document ID missing or duplicated")
        if not isinstance(row.get("text"), str) or not isinstance(row.get("title"), str):
            raise ValueError("Corpus title/text must be strings")
        documents[doc_id] = f'{row["title"]} {row["text"]}'
    for row in _lines(root / "queries.jsonl"):
        query_id = row.get("_id")
        if not isinstance(query_id, str) or not query_id or query_id in questions:
            raise ValueError("Query ID missing or duplicated")
        if not isinstance(row.get("text"), str) or not row["text"].strip():
            raise ValueError("Query text must be a nonempty string")
        questions[query_id] = row["text"]
    for row in _lines(root / "qrels/test.jsonl"):
        query_id, document = row.get("query-id"), row.get("corpus-id")
        grade = row.get("score")
        if not isinstance(query_id, str) or not isinstance(document, str):
            raise ValueError("Qrels IDs must be strings")
        if query_id not in questions or document not in documents:
            raise ValueError("Qrels references an unknown query or document")
        if not isinstance(grade, int) or isinstance(grade, bool):
            raise ValueError("Qrels score must be an integer")
        if (query_id, document) in labels:
            raise ValueError("Duplicate judgment in qrels")
        labels[(query_id, document)] = grade
    if not documents or not questions or not labels:
        raise ValueError("Corpus, queries or labels are missing")
    if any(not any(k[0] == query and grade > 0 for k, grade in labels.items())
           for query in questions):
        raise ValueError("All evaluated queries require at least one positive qrel")
    return documents, questions, labels


class BM25:
    """Dependency-free Okapi BM25, not an external library's tuned baseline."""
    def __init__(self, documents, method, *, k1=1.2, b=0.75):
        self.method = method
        self.lengths, self.postings = {}, {}
        for doc_id, text in sorted(documents.items()):
            counts = Counter(tokenize(text, method))
            self.lengths[doc_id] = sum(counts.values())
            for term, frequency in counts.items():
                self.postings.setdefault(term, {})[doc_id] = frequency
        self.ids = sorted(documents)
        self.avg_length = sum(self.lengths.values()) / len(documents)
        self.n = len(documents)
        self.k1, self.b = k1, b

    def search(self, query, k):
        score = Counter()
        for term in set(tokenize(query, self.method)):
            postings = self.postings.get(term, {})
            df = len(postings)
            if not df:
                continue
            idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            for doc_id, tf in postings.items():
                normalization = tf + self.k1 * (
                    1 - self.b + self.b * self.lengths[doc_id] / self.avg_length)
                score[doc_id] += idf * tf * (self.k1 + 1) / normalization
        return sorted(self.ids, key=lambda doc: (-score[doc], doc))[:k]


def run_benchmark(documents, questions, labels, k=10):
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("k must be positive")
    positives = {}
    for (query_id, doc_id), grade in labels.items():
        if grade > 0:
            positives.setdefault(query_id, []).append(doc_id)
    rows = {}
    for method in ("unicode_casefold", "turkish_case"):
        searcher = BM25(documents, method)
        rows[method] = [
            {"query_id": query_id, "retrieved_ids": searcher.search(query, k),
             "relevant_ids": sorted(positives[query_id])}
            for query_id, query in sorted(questions.items())
        ]
    base = evaluate(rows["unicode_casefold"], k)
    candidate = evaluate(rows["turkish_case"], k)
    paired = compare_rows(rows["turkish_case"], rows["unicode_casefold"], k)
    return {
        "documents": len(documents), "queries": len(questions),
        "judgments": len(labels), "k": k,
        "baseline": {"method": "unicode_casefold_bm25",
                     "metrics": base["metrics"]},
        "candidate": {"method": "turkish_case_bm25",
                      "metrics": candidate["metrics"]},
        "candidate_minus_baseline": paired["delta"],
        "paired_bootstrap_95pct_ci": paired["paired_bootstrap_95pct_ci"],
        "bootstrap_note": paired["bootstrap_note"],
        "scope": "Turkish health-domain Wikipedia article-level retrieval",
        "notes": "The same BM25 ranks are compared; only Turkish casing/tokenization differs. Positive article-level qrels are authored by the dataset's original human annotator. No claim of significance or universal generalization.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path)
    parser.add_argument("--download", action="store_true",
                        help="Download original licensed dataset to disposable folder")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--output", type=Path, help="Aggregate-only JSON result")
    args = parser.parse_args(argv)
    if args.download == (args.dataset_dir is not None):
        parser.error("Choose exactly one of --download or --dataset-dir")
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) if args.download else args.dataset_dir
        source_hashes = download_dataset(root) if args.download else {
            relative: hashlib.sha256((root / relative).read_bytes()).hexdigest()
            for relative in DATA_FILES
        }
        documents, questions, labels = load_dataset(root)
        report = run_benchmark(documents, questions, labels, k=args.k)
        report["dataset"] = DATASET
        report["dataset_revision"] = DATASET_REVISION
        report["dataset_license"] = "CC BY-SA 4.0; data not redistributed"
        report["source_sha256"] = source_hashes
        rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.write_text(rendered, encoding="utf-8")
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
