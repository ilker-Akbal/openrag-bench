# Changelog

All notable changes to OpenRAG Bench are documented here.

## Unreleased — working toward v0.2.0

- Add native JSONL/NDJSON evaluation input and spreadsheet-safe per-query CSV
  exports with physical-line parse diagnostics.
- Add MAP@k and exponential-gain graded NDCG@k; preserve binary NDCG and
  introduce opt-in TREC `--graded-qrels`.
- Add lightweight LangChain and LlamaIndex retriever interoperability
  adapters with stable-ID validation and dependency-free mocked tests.
- Maintain source-only development changes on `main`; published v0.1.0
  wheel and source distribution remain unchanged.

## [v0.1.0] — 2026-10-13

[GitHub public pre-release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.1.0)
includes tested wheel, source distribution and SHA256SUMS integrity file.
This is a **GitHub release, not a PyPI publication**.

### Added
- Dependency-free, offline Precision@k, Recall@k, Hit@k, MRR@k and NDCG@k
  evaluation, macro-averaged with per-query breakdowns.
- Strict input validation, JSON/HTML outputs, custom retriever protocol,
  TREC run/qrels compatibility and deterministic regression thresholds.
- Baseline vs candidate comparison with descriptive paired-bootstrap
  confidence intervals.
- Optional FAISS adapter and the pinned MiniLM + FAISS demonstration.
- Verified, independently re-scored **real SciFact** lexical BM25 vs TF-IDF
  experiment, with aggregate-only results and dataset provenance.
- Python 3.10–3.13 CI, isolated build/installer audits, security and
  contributor guidance.

### Limitations
- The first source and wheel GitHub release exists; no PyPI package is claimed.
- Verified MiniLM + FAISS SciFact results were also recorded from
  GitHub Actions (full CPU model inference and independent TREC re-scoring).
  This specific run's NDCG@10 was 0.6451, versus BM25 0.6605; no
  significance or cross-domain superiority is claimed.
- Synthetic tests are not evidence of third-party usage.
- Scores cover document retrieval, not generated answer truthfulness.

## References

- [Verified SciFact metrics](benchmarks/scifact_2026-10-13.json)
- [SciFact benchmark methodology](docs/BENCHMARK_SCIFACT.md)
- [Release checklist](docs/RELEASING.md)
