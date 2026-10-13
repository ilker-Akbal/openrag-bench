# OpenRAG Bench v0.2.0 — Retrieval diagnostics and RAG framework interoperability

**This is a public GitHub pre-release**, not a PyPI publication. Python 3.10–3.13
and the dependency-free core CLI are tested by GitHub Actions.

## What's new since v0.1.0

### Data formats and diagnostics — [PR #13](https://github.com/ilker-Akbal/openrag-bench/pull/13)

- Evaluate JSON arrays, JSONL and NDJSON files directly.
- Select formats explicitly when file extensions are ambiguous.
- Export one row per query as spreadsheet-safe **CSV**, including candidate,
  baseline and signed metric differences.
- Protect untrusted CSV query IDs from spreadsheet formulas, omit question text,
  and include exact physical line numbers in JSONL parsing errors.

### New evaluation metrics — [PR #14](https://github.com/ilker-Akbal/openrag-bench/pull/14)

- **MAP@k**: macro-averaged per-query average precision with denominator
  `min(k, number of relevant documents)`.
- **Graded NDCG@k**: exponential gains `2**grade-1` for positive integer
  relevance grades 1..31, supplied through JSON/JSONL or TREC
  `--graded-qrels`.
- Existing binary `ndcg_at_k` is **not redefined**, preserving its earlier
  interpretation. Candidate/baseline qrels must match in both IDs and grades.

### Integrations — [PR #15](https://github.com/ilker-Akbal/openrag-bench/pull/15)

- Dependency-free adapter for existing **LangChain** retrievers exposing
  `invoke(query)` and stable document IDs.
- Dependency-free adapter for existing **LlamaIndex** retrievers exposing
  `retrieve(query)` and stable node IDs.
- Strict duplicate/missing-ID checks and mock-based adapter unit tests.
- Not a guarantee of compatibility with every framework release, and not
  a claim of live third-party framework performance.

## Install

Obtain the wheel from this GitHub Release, verify its checksum against
`SHA256SUMS`, and install:

```bash
python -m pip install openrag_bench-0.2.0-py3-none-any.whl
openrag-bench --help
```

Or install from a tagged source checkout (`v0.2.0`).

The core has no runtime dependencies, cloud calls or required API key.
Extra FAISS/dense model dependencies must be installed separately.

## Compatibility and scope

- Report JSON now includes `map_at_k` and `graded_ndcg_at_k`; clients
  validating an **exact fixed list** of metric keys must adapt their schemas.
- Existing JSON array inputs, binary TREC qrels and original metrics retain
  their original definitions.
- `--graded-qrels` is opt-in; no implicit switch to graded scoring.
- No model weights, copyrighted workshop files or SciFact dataset corpus are
  bundled. The source distribution includes reproducibility tests, examples
  and documentation.

## Prior real-world SciFact evidence

The independently verified GitHub Actions experiments for 5,183 scientific
documents and 300 test queries remain available. Previously published
NDCG@10 (binary) values: TF-IDF 0.6329, BM25 0.6605,
MiniLM + FAISS 0.6451. New graded metrics are **not** claimed to have
been validated on newly graded SciFact labels.

- [Lexical benchmark documentation](https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/BENCHMARK_SCIFACT.md)
- [Dense model benchmark documentation](https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/DENSE_SCIFACT.md)
- [Data format and metric definitions](https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/USAGE.md)
- [Framework adapter guide](https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/FRAMEWORK_INTEGRATIONS.md)

No statistics-based superiority, production SLA, established external
community usage or PyPI availability is claimed.
