# OpenRAG Bench roadmap

## Implemented in the standalone repository

- [x] Precision@k, Recall@k, Hit@k, MRR@k and binary NDCG@k
- [x] Validated JSON schema and transparent macro-averaged reporting
- [x] Paired baseline-versus-candidate comparisons by query ID
- [x] Seeded paired bootstrap descriptive confidence intervals
- [x] CLI gate for retrieval regressions in CI
- [x] HTML reporting with untrusted text escaped
- [x] Custom retriever protocol and optional FAISS adapter
- [x] Synthetic fixtures, unit tests, 3.10–3.13 CI and wheel build
- [x] TREC run/qrels format for externally maintained retrieval benchmarks
- [x] Independent repository, MIT license and provenance document

- [x] Reproducible BEIR SciFact BM25 versus TF-IDF benchmark *runner* with checksum validation, independent of cloud APIs
- [x] Offline fixture tests for SciFact dataset parsing and ranking

- [x] Optional pinned-model dense embeddings + FAISS SciFact runnable example, dependency isolated
- [x] Offline regression tests for dense versus lexical result alignment
- [x] Run pinned MiniLM dense model on real SciFact; independently verify metrics and record aggregate-only provenance
- [ ] Recruit independent outside developers to reproduce dense/lexical findings and file genuine feedback

- [x] v0.2.0: JSONL/NDJSON, spreadsheet-safe per-query CSV and improved diagnostics
- [x] v0.2.0: MAP@k and opt-in graded relevance with TREC qrels
- [x] v0.2.0: optional, dependency-free LangChain and LlamaIndex protocol adapters
- [x] v0.2.0: audited and tested wheel and source distribution, with reproducibility docs

## Next milestones

- [x] Run and independently verify SciFact on real BEIR data; commit aggregate-only metrics with provenance
- [x] Publish reproducible SciFact dense embedding + FAISS walkthrough with pinned model and retrieval settings
- [x] Publish an initial v0.1.0 GitHub pre-release with verified wheel/sdist archives and SHA256SUMS
- [ ] Review ownership/attribution continuously before future versions; PyPI publication is not yet planned
- [x] Audit wheel/sdist archives, clean-install release, and enable weekly Dependabot checks
- [x] Owner enabled GitHub private vulnerability reporting, secret protection, push protection and CodeQL defaults
- [ ] Establish a reliable maintainer contact for confidential issues
- [ ] Produce genuinely multilingual labeled evaluation resources
- [ ] Compare fairly with existing open-source evaluation tools
- [ ] Collect genuine outside user feedback and maintain issues/releases over time

## v0.3.0 — verified and shipped

**Priority 1: real user workflows and scalability**

1. [Genuine LangChain and LlamaIndex end-to-end compatibility](https://github.com/ilker-Akbal/openrag-bench/issues/19): real pinned framework vector-store CI added; complete only after both live integration jobs succeed, then seek independent user reproduction.
2. [Streaming and bounded-memory evaluation](https://github.com/ilker-Akbal/openrag-bench/issues/18): **implemented** summary-only JSONL; verified 100k synthetic queries with measured memory, wall time, and metric parity. Broader file formats and paired external-memory joins remain future work.
3. [Diagnostic report explorer](https://github.com/ilker-Akbal/openrag-bench/issues/21): **completed**, with offline searchable/filterable HTML query diagnostics and no raw question/document text.

**Priority 2: wider evidence and sustainable maintenance**

4. [Turkish-language retrieval benchmark with valid relevance labels](https://github.com/ilker-Akbal/openrag-bench/issues/20): **completed** external pinned Turkish Wikipedia human-labeled set, 54 docs/58 qrels and real CI; same 0.85445 NDCG@10 under both casefoldings.
5. [Quality gates and maintainable releases](https://github.com/ilker-Akbal/openrag-bench/issues/22): **completed** Ruff, measured 95% line coverage with enforced 90% minimum, Hypothesis property tests and Node.js 24-capable actions.
6. [Independent user reproduction and feedback](https://github.com/ilker-Akbal/openrag-bench/issues/4): collect **real** downstream examples and issues from non-maintainers.

Each issue has testable acceptance criteria. The new `v0.3.0` release
provides the working baseline; future experiments must not rewrite prior
published metric values or tags. Large optional frameworks and models must
not become required dependencies for the offline core.

## v0.4 — OpenRAG Guard (released 2026-10-14)

- [x] Versioned fail-closed quality policies: aggregate, critical and category rules
- [x] Five-minute onboarding with init and doctor
- [x] Reusable GitHub Action with safe step summary and deterministic failure status
- [x] CI proves a critical query regression is blocked despite improved aggregate score
- [x] Versioned pre-release only after independent audit and CI

## v0.5 — Golden Dataset Studio (alpha released 2026-10-14)

- [x] Local static HTML browser editor without third-party scripts or uploads
- [x] Import/export human-rated golden query/document judgments
- [x] Edit critical tags, categories and relevance grades 1–3
- [x] Export editable JSON drafts and default Guard policy v1
- [x] Validate duplicates, stale references, and missing labels on export
- [ ] Complete independent human UI and accessibility checks before declaring v0.5 production ready

## v0.6 — Capture & Replay (development, not released)

- [x] Strict offline capture from real ranked JSON/JSONL results onto Studio human labels
- [x] Optional explicit canonical document ID mapping and retriever protocol capture
- [x] Deterministic versioned hash-only capture manifest
- [x] Reuse existing Guard for offline replay, no new evaluation algorithm
- [x] Add actual BEIR SciFact retriever -> Capture -> Replay path and parity CI checks
- [ ] Confirm all GitHub CI results, including SciFact real-data run, before merging
- [ ] Review privacy, file-write failure scenarios and production readiness
- [ ] Audit and release v0.6 artifacts without altering past tags

## Next releases (proposed, not implemented)

- v0.5 — Golden Dataset Studio: privacy-aware local UI for human relevance labels.
- v0.6 — Capture & Replay: deterministic retrieval exports, stable ID mappings
  and optional adapters for reproducible evaluations.
- Later: latency/cost guardrails when independently measurable.

## Codex for Open Source application

An MIT license, public code and successful tests do not establish meaningful
external adoption by themselves. Use authentic maintainership history,
external usage and reproducible examples when making an application. Never
manufacture stars, reviewers, package downloads or benchmarks. This project's
acceptance is entirely at OpenAI's discretion.
