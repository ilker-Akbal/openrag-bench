# Changelog

## [v0.6.0] — 2026-10-14

[GitHub v0.6.0 alpha pre-release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.6.0) published with audited wheel, sdist and SHA256SUMS.

Capture & Replay connects human-labeled Golden Dataset Studio queries to
real ranked IDs from an external retriever, then reuses the existing Guard
engine for deterministic offline regression checks.

- `capture` binds explicitly observed JSON/JSONL rankings to golden judgments
  with strict query-ID and document-ID mapping validation.
- `replay` invokes existing Guard logic and pass/blocked return codes.
- Optional hash-only manifests and cleanup of partial capture/manifest writes.
- `capture_from_retriever` integrates a user-provided Python retrieval backend.
- Reproducible real-data SciFact BM25/TF-IDF example with CI checks of
  Capture/Replay parity against independently evaluated TREC metrics.
- Tests for invalid mappings, file safety and lexical retrieval integration.
- No new mandatory dependency, LLM API, hosted service or bundled corpus.
- v0.5.0 and older GitHub release tags/assets remain unchanged.

## [v0.5.0] — 2026-10-14

[GitHub v0.5.0 alpha pre-release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.5.0)
adds the offline, human-driven Golden Dataset Studio. This is early adopter
software with automated browser-logic smoke and Python security checks;
external usability testing is still pending.

- Add a dependency-free local browser editor for manual question/doc relevance
  grades, categories and critical query flags.
- Import existing evaluation rows or Studio drafts and export validated golden
  judgments, policy defaults and locally saved drafts.
- No server, automatic persistence, telemetry or external dependencies.
- Exported judgments have intentionally empty retrieval results: developers
  must run their own retriever before evaluation.
- v0.4.1 release artifacts are unaffected.



## [v0.4.1] — 2026-10-14

[GitHub v0.4.1 pre-release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.4.1)
improves the offline Guard report without altering retrieval metrics,
quality policy decisions, core dependencies or prior GitHub release assets.

- Decision-first PASS/BLOCK dashboard, explained policy failures and
  first-relevant-rank comparisons, with the detailed tables collapsed.
- Explicit warning when a **PASSED** policy still permits per-query NDCG@k
  regressions; includes the regressed-query count.
- Query diagnostics fixed-width desktop table with readable wrapped headers
  and the existing horizontally scrollable small-screen fallback.
- Original six-query k=3 example with varied metrics; offline privacy,
  accessibility and compatibility tests maintained.
- No changes to v0.4.0's published wheel, sdist, hashes or git tag.

## [v0.4.0] — 2026-10-14

[GitHub public pre-release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.4.0)
adds fail-closed scoped retrieval policies, onboarding and the read-only
GitHub Action. Previous releases remain unchanged; not published on PyPI.

- Add OpenRAG Guard deterministic, fail-closed global, critical and
  category-specific retrieval policy gates.
- Add original synthetic init, data/policy doctor, redacted guard reports,
  first-relevant rank diagnostics, and a reusable read-only GitHub Action.
- Demonstrate a blocked critical query despite positive macro NDCG.
- Released v0.3.0 artifacts and core mandatory dependencies are unchanged.

## [v0.3.0] — 2026-10-13

[GitHub public pre-release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.3.0):
new privacy-aware diagnostic HTML explorer, independently labeled Turkish
lexical benchmark, 100,000-query bounded-memory JSONL evaluation, genuine
pinned LangChain/LlamaIndex compatibility tests, and stricter quality gates.
This is a GitHub pre-release, **not** a PyPI publication.

- Add **enforced** Ruff static lint and measured test coverage to the
  protected Python 3.11 required status check, with optional developer-only
  tooling and Hypothesis property invariants.
- Upgrade GitHub workflow actions to Node.js 24-capable supported major
  versions. Preserve required check job names and avoid auto-release triggers.

- Add pinned CC BY-SA Turkish Wikipedia retrieval benchmark runner, consuming
  54 articles and 58 independently authored human-labeled questions from an
  external dataset **without bundling** third-party texts or questions.
- Compare identical BM25 settings with Unicode casefold versus Turkish-aware
  dotted/dotless-I casing; archive aggregate metrics and dataset checksums,
  not question text or article contents.

- Add offline, keyboard-accessible per-query diagnostic HTML explorer with
  safe filtering/sorting, top-k overlap and label coverage. Omit raw question
  text and document IDs from HTML to reduce accidental disclosures.
- Add optional per-query diagnostic counts to JSON reports, without changing
  retrieval metric calculations.

- Add explicit bounded-memory JSONL **aggregate-only** streaming evaluator;
  preserve all existing metrics and reject unsupported paired/reporting
  combinations rather than silently changing semantics.

- Add a separate GitHub Actions compatibility suite for actual installed
  LangChain and LlamaIndex vector index/retriever implementations, using a
  deterministic, offline, synthetic embedding and exact-label evaluation.
- Leave default dependency-free core installation unchanged; pinned
  framework integration dependencies are installed in isolated CI jobs.

## [v0.2.0] — 2026-10-13

[GitHub public pre-release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.2.0).
The release is additive but introduces extra metric keys in JSON reports;
integrations that expect an exact metric-key set should update their schemas.

- Add native JSONL/NDJSON evaluation input and spreadsheet-safe per-query CSV
  exports with physical-line parse diagnostics.
- Add MAP@k and exponential-gain graded NDCG@k; preserve binary NDCG and
  introduce opt-in TREC `--graded-qrels`.
- Add lightweight LangChain and LlamaIndex retriever interoperability
  adapters with stable-ID validation and dependency-free mocked tests.
- Publish verified v0.2.0 wheel and source archives without bundling
  SciFact documents or external model weights. The earlier v0.1.0 tag and
  its files remain immutable.

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
