# Changelog

All notable changes to OpenRAG Bench will be documented here.
The project follows semantic versioning for **tagged releases**; the Python
package metadata currently indicates 0.1.0 but **no GitHub release/tag is
claimed by this file**.

## Unreleased (release candidate work, 13 October 2026)

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
- No public source/wheel release or PyPI availability is claimed until a
  signed-off release is explicitly made.
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
