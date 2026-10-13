# OpenRAG Bench

[![CI](https://github.com/ilker-Akbal/openrag-bench/actions/workflows/ci.yml/badge.svg)](https://github.com/ilker-Akbal/openrag-bench/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10--3.13-blue.svg)](pyproject.toml)
[![GitHub pre-release](https://img.shields.io/github/v/release/ilker-Akbal/openrag-bench?include_prereleases)](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.1.0)

**Offline retrieval evaluation and regression testing for RAG pipelines.**

OpenRAG Bench is a small Python toolkit for comparing the ranked document results of retrieval-augmented generation systems. It helps developers catch regressions when they change an embedding model, chunking strategy, retriever or index configuration.

- **Measure** Precision@k, Recall@k, Hit@k, MRR@k and binary NDCG@k.
- **Compare** candidate and baseline outputs, aligned by stable query identifiers.
- **Guard** a CI pipeline with an explicit minimum metric delta and exit code 2.
- **Report** macro-averaged results, per-query metrics and standalone HTML/JSON output.
- **Integrate** custom retrievers through a tiny protocol or the optional FAISS adapter.
- **Reproduce** seeded, paired-bootstrap uncertainty intervals without a cloud API.

**Status:** [v0.1.0 public GitHub pre-release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.1.0), with SHA-256 checksums and tested wheel/source archives. This measures **retrieval relevance**, not LLM answer quality or factual correctness. The bundled quickstart fixtures are synthetic; separate, real **SciFact**
benchmark results are independently verified and published below. We do
not claim benchmark superiority or an established external user base.

**Language:** English documentation (primary) · [Türkçe hızlı başlangıç](docs/README_TR.md)

## Quick start

Requires Python 3.10 or newer. Install the **GitHub release wheel** (not
published on PyPI):

```bash
python -m pip install https://github.com/ilker-Akbal/openrag-bench/releases/download/v0.1.0/openrag_bench-0.1.0-py3-none-any.whl
openrag-bench --help
```

To run the examples and tests from source:

```bash
git clone https://github.com/ilker-Akbal/openrag-bench.git
cd openrag-bench
python -m pip install -e .
python -m unittest discover -s tests -v
openrag-bench examples/retrieval_results.json --k 2 --output report.json --html report.html
```

## Compare two retrieval versions

```bash
openrag-bench examples/comparison_candidate.json \
  --baseline examples/comparison_baseline.json \
  --k 2 --metric ndcg_at_k --min-delta 0 \
  --output comparison.json --html comparison.html
```

A negative delta means the candidate scored worse than the baseline. With `--min-delta 0`, the CLI exits with code `2` if that metric regresses. Use this as a deterministic engineering gate, **not** as a statistical significance test.

## Evaluate standard TREC run files

No custom JSON conversion needed for common information-retrieval datasets.
Given four-column `qrels` and six-column `run` files:

```bash
openrag-bench examples/trec_candidate.run \
  --qrels examples/trec.qrels \
  --baseline examples/trec_baseline.run \
  --k 2 --metric ndcg_at_k --min-delta 0
```

Each query from the qrels contributes to the score even when the run returns
nothing. Positive relevance grades count as relevant; zero and negative
judgments are not relevant. Unknown query IDs, duplicate docs, duplicate
ranks and invalid scores are rejected.

## Run against a real retriever

```python
from openrag_bench.adapters import run_retriever

class Retriever:
    def retrieve(self, query: str, k: int):
        return ["doc-1", "doc-2"][:k]

result = run_retriever(
    Retriever(),
    [{"query_id": "q1", "question": "What is RAG?", "relevant_ids": ["doc-2"]}],
    k=2,
)
print(result["metrics"])
```

An optional FAISS adapter and reproducible synthetic-vector example are provided:

```bash
python -m pip install '.[faiss]'
python examples/faiss_integration.py
```

## Reproduce a real dataset benchmark

Run two lexical retrieval baselines against the externally hosted **BEIR SciFact
test** split (5,183 scientific abstracts; 300 judged queries):

```bash
python examples/scifact_benchmark.py --download --k 10 --output-dir reports/scifact
```

The tool explicitly downloads the official 2.8 MB ZIP, verifies the checksum,
reads it without extracting files, builds a local inverted index, runs **TF-IDF
cosine** and **BM25**, and saves ranked TREC run files plus aggregate and
per-query comparisons. Python standard library is sufficient.

**Verified results are published:** BM25 NDCG@10 **0.6605**, versus TF-IDF
**0.6329** on 300 judged queries. See the exact
[reproduction, data attribution and limitations](docs/BENCHMARK_SCIFACT.md)
and [aggregate-only metrics](benchmarks/scifact_2026-10-13.json). The dataset
retains its respective licenses; no data is included in this code repository.

## How it works

Your RAG system supplies a ranked list of retrieved document IDs for each labeled question. OpenRAG Bench compares those rankings against explicitly documented relevant IDs. With a baseline and candidate JSON file, it reports per-query differences and seeded paired-bootstrap confidence intervals. Comparisons require matching query IDs and ground-truth labels.

No models are downloaded and the evaluation core makes no network calls.

## Dense embeddings + FAISS (optional)

A separate [CPU-capable real-data walkthrough](docs/DENSE_SCIFACT.md) compares
a pinned Sentence Transformers MiniLM embedding model with BM25 using FAISS
exact vector search:

```bash
python -m pip install -e '.[dense]'
python examples/scifact_dense_faiss.py --download --k 10
```

**Real dense model results have now been verified** on 5,183 SciFact
documents and 300 judged queries: MiniLM + FAISS NDCG@10 **0.6451** versus
BM25 **0.6605**. See the [provenance and limitations](docs/DENSE_SCIFACT.md)
and [verified aggregate metrics](benchmarks/scifact_dense_2026-10-13.json).
Ordinary unit CI does not download weights; a dedicated GitHub Actions
workflow performs the real model evaluation.

## Contribute, get support and verify results

The tool is maintained in the open. You can install the existing public
pre-release, reproduce the verified SciFact results, report bugs with tiny
synthetic fixtures, or suggest a new retriever adapter. Contributions and
issues must come from real users; no usage figures are claimed.

- [Reproduce independently or contribute](docs/GET_INVOLVED.md)
- [Ask a usage question or report a reproducible bug](SUPPORT.md)
- [Contributor guidelines](CONTRIBUTING.md)
- [Report a security concern](SECURITY.md)
- [Verified v0.1.0 release assets and checksums](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.1.0)

## Documentation

- [Input format, metric definitions and limitations](docs/USAGE.md)
- [Contributor guide](CONTRIBUTING.md)
- [Security guidance](SECURITY.md)
- [Provenance and third-party asset policy](docs/PROVENANCE.md)
- [Development roadmap](docs/ROADMAP.md)
- [Latest public GitHub release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.1.0)

This repository contains the standalone toolkit only, **not** the ROKETSAN workshop archive. Third-party material from that archive is deliberately excluded.

## License

MIT; see [LICENSE](LICENSE). No permission is claimed over third-party workshop content or externally supplied benchmark datasets.
