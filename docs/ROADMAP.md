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
- [ ] Run the real dense model, verify metrics and collect independent outside reproduction

## Next milestones

- [x] Run and independently verify SciFact on real BEIR data; commit aggregate-only metrics with provenance
- [ ] Publish reproducible full-pipeline RAG case study with embeddings and retrieval settings
- [ ] Package/publish tagged releases after verifying source attributions
- [ ] Harden release workflows, automate security/dependency checks and enable private reporting
- [ ] Produce genuinely multilingual labeled evaluation resources
- [ ] Compare fairly with existing open-source evaluation tools
- [ ] Collect genuine outside user feedback and maintain issues/releases over time

## Codex for Open Source application

An MIT license, public code and successful tests do not establish meaningful
external adoption by themselves. Use authentic maintainership history,
external usage and reproducible examples when making an application. Never
manufacture stars, reviewers, package downloads or benchmarks. This project's
acceptance is entirely at OpenAI's discretion.
