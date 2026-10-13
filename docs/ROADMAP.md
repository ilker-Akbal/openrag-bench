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

## v0.3.0 — planned measurable improvements

**Priority 1: real user workflows and scalability**

1. [Genuine LangChain and LlamaIndex end-to-end compatibility](https://github.com/ilker-Akbal/openrag-bench/issues/19): real pinned framework vector-store CI added; complete only after both live integration jobs succeed, then seek independent user reproduction.
2. [Streaming and bounded-memory evaluation](https://github.com/ilker-Akbal/openrag-bench/issues/18): **implemented** summary-only JSONL; verified 100k synthetic queries with measured memory, wall time, and metric parity. Broader file formats and paired external-memory joins remain future work.
3. [Diagnostic report explorer](https://github.com/ilker-Akbal/openrag-bench/issues/21): identify per-query failures without exposing private source text.

**Priority 2: wider evidence and sustainable maintenance**

4. [Turkish-language retrieval benchmark with valid relevance labels](https://github.com/ilker-Akbal/openrag-bench/issues/20): select or create a licensed test collection, validate tokenizer behavior and document methodology.
5. [Quality gates and maintainable releases](https://github.com/ilker-Akbal/openrag-bench/issues/22): measurable coverage, property tests, focused lint and versioned artifact publication.
6. [Independent user reproduction and feedback](https://github.com/ilker-Akbal/openrag-bench/issues/4): collect **real** downstream examples and issues from non-maintainers.

Each issue has testable acceptance criteria. The existing `v0.2.0` release
provides the working baseline; future experiments must not rewrite prior
published metric values or tags. Large optional frameworks and models must
not become required dependencies for the offline core.

## Codex for Open Source application

An MIT license, public code and successful tests do not establish meaningful
external adoption by themselves. Use authentic maintainership history,
external usage and reproducible examples when making an application. Never
manufacture stars, reviewers, package downloads or benchmarks. This project's
acceptance is entirely at OpenAI's discretion.
