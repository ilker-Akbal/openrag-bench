# OpenRAG Bench v0.3.0 — Diagnostic evaluation, verified Turkish qrels and quality gates

**MIT software on GitHub (pre-release), not PyPI.**

## New: privacy-aware offline HTML query explorer

Search query IDs, sort regressions, change metric selection and filter outcomes.
See summary cards for coverage, empty results and hits; paired reports additionally
show top-k document overlap counts. The HTML does **not** embed raw question
text, document IDs or remote scripts. Query IDs may still be sensitive.

## New: human-labeled Turkish retrieval benchmark

Independent external author Rızgar Ozan's **CC BY-SA 4.0** dataset is pinned by
commit and loaded **only on demand**. Evaluated 54 health-domain Turkish
Wikipedia articles, 58 human-annotated queries and 58 relevance judgments.
Both Unicode casefold and Turkish-aware casing BM25 variants scored
**NDCG@10 = 0.8544543634**; the difference was **zero**. We do not claim
a quality improvement from this change. External texts/questions are **not
included in this release**. See docs/TURKISH_BENCHMARK.md.

## New: bounded-memory JSONL streaming summary

`openrag-bench large.jsonl --streaming-summary --k 5` evaluates an
aggregate of many labeled queries without materializing all rows. A verified
100,000-query synthetic experiment observed **0.302 MiB** Python peak
allocations compared with **121.297 MiB** for the previous batch path; it
was **slower** (12.46 s versus 9.42 s). `tracemalloc` does not
measure total process RAM/RSS. Paired baselines, CSV and HTML are rejected
in this streaming-only mode.

## New: genuine pinned LangChain/LlamaIndex integration checks

Actual installed LangChain core **1.6.5** and LlamaIndex core **0.14.25**
vector store/retriever APIs exercised via synthetic offline keyword vectors,
verified under Python 3.11.17. This proves specific compatibility, not
semantic retrieval quality or cross-version support. The optional framework
dependencies are **not required** by the core package.

## Maintenance/QA

- Python 3.10–3.13 matrix;
- **67 standard unit tests** plus **3 Hypothesis property tests** (measured before packaging);
- Ruff lint and enforced **90% minimum line coverage** in required Python 3.11 check;
  the baseline report observed **95%** line coverage;
- Node.js 24-compatible hosted Actions versions;
- Clean source/wheel installs, archive audit, SHA256SUMS.

## Install

Download and verify the attached wheel against `SHA256SUMS`:

~~~bash
python -m pip install openrag_bench-0.3.0-py3-none-any.whl
openrag-bench --help
~~~

The GitHub wheel URL can also be used directly. No paid LLM API or cloud
service required for the core metrics.

## Compatibility

This is a **pre-release**. HTML no longer includes raw `question`
strings by design; JSON per-query results have **additive diagnostic fields**,
which may affect clients validating exact JSON schemas. Original metric
formulas and optional tool contract remain intact.

No proprietary corpus, copyrighted workshop content, third-party dataset
text or model weights are bundled. No claims of independent external users
or production SLAs.
