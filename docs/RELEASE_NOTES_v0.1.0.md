# OpenRAG Bench v0.1.0 — Initial public pre-release

OpenRAG Bench is an MIT-licensed, local Python evaluation tool for the
**retrieval** component of Retrieval-Augmented Generation (RAG).

### Highlights

- Dependency-free offline Precision@k, Recall@k, Hit@k, MRR@k and binary
  NDCG@k, per-query reports and macro averages
- Machine-readable JSON and escaped standalone HTML reports
- Paired candidate-versus-baseline evaluation with stable query IDs and
  deterministic CI regression gates
- Seeded paired-bootstrap intervals (descriptive, not significance tests)
- Standard TREC run/qrels file compatibility
- Optional FAISS adapter and pinned MiniLM + FAISS SciFact walkthrough
- Python 3.10–3.13 unit tests, wheel/sdist distribution audit

### Verified external dataset results (SciFact, test split, k=10)

5,183 scientific abstracts; 300 judged queries. Real GitHub Actions runs
used the official checksum-verified external dataset; **dataset files and
model weights are not included in this release**.

| Metric | TF-IDF | BM25 | MiniLM + FAISS |
| --- | ---: | ---: | ---: |
| Precision@10 | 0.0860 | 0.0870 | 0.0883 |
| Recall@10 | 0.7785 | 0.7876 | 0.7833 |
| MRR@10 | 0.5940 | 0.6270 | 0.6047 |
| NDCG@10 | 0.6329 | 0.6605 | 0.6451 |

These results are for a **single benchmark with incomplete binary qrels**.
They do not measure LLM answer truthfulness or establish statistically
significant superiority.

- [Lexical benchmark methodology](https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/BENCHMARK_SCIFACT.md)
- [Dense benchmark methodology](https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/DENSE_SCIFACT.md)
- [Verified lexical aggregate metrics](https://github.com/ilker-Akbal/openrag-bench/blob/main/benchmarks/scifact_2026-10-13.json)
- [Verified dense aggregate metrics](https://github.com/ilker-Akbal/openrag-bench/blob/main/benchmarks/scifact_dense_2026-10-13.json)

### Installing this pre-release

Download the matching wheel file from the GitHub Release assets, then:

```bash
python -m pip install openrag_bench-0.1.0-py3-none-any.whl
openrag-bench --help
```

Or clone the public repository and run `python -m pip install -e .`.
The core requires Python 3.10+ and does not require an API key.

**Integrity:** This release includes a `SHA256SUMS` asset for the wheel and
source distribution; verify checksums before installing.

**PyPI:** not claimed as published. Do not confuse a GitHub Release with a
PyPI distribution.

### Known limitations

- Evaluation requires reliable, pre-labeled relevance judgments.
- Dense embedding model dependencies and weights must be installed separately.
- No promises of production SLA, third-party adoption, or generalized quality.
- Metrics do not directly measure generated answers, cost or latency.

### Contributors and security

Public [contribution guide](https://github.com/ilker-Akbal/openrag-bench/blob/main/CONTRIBUTING.md),
[security guidance](https://github.com/ilker-Akbal/openrag-bench/blob/main/SECURITY.md)
and [issues](https://github.com/ilker-Akbal/openrag-bench/issues) are available.
