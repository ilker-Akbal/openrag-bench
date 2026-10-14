<p align="center">
  <img src="assets/branding/openrag-bench-social-preview.png" alt="OpenRAG Bench — Offline retrieval evaluation and diagnostics" width="100%">
</p>

<p align="center">
  <img src="assets/branding/openrag-bench-logo.png" alt="OpenRAG Bench logo" width="125">
</p>

<h1 align="center">OpenRAG Bench</h1>

<p align="center">
  <strong>Measure · Compare · Diagnose · Improve</strong>
</p>

<p align="center">
  <a href="https://github.com/ilker-Akbal/openrag-bench/actions/workflows/ci.yml"><img src="https://github.com/ilker-Akbal/openrag-bench/actions/workflows/ci.yml/badge.svg" alt="CI status"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="pyproject.toml"><img src="https://img.shields.io/badge/python-3.10--3.13-blue.svg" alt="Python 3.10 to 3.13"></a>
  <a href="https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.6.0"><img src="https://img.shields.io/badge/release-v0.6.0-orange.svg" alt="Latest published GitHub pre-release v0.6.0"></a>
</p>

**Offline retrieval evaluation and regression testing for RAG pipelines.**

OpenRAG Bench is a small Python toolkit for comparing the ranked document results of retrieval-augmented generation systems. It helps developers catch regressions when they change an embedding model, chunking strategy, retriever or index configuration.

- **Measure** Precision@k, Recall@k, Hit@k, MRR@k, MAP@k, binary and graded NDCG@k.
- **Compare** candidate and baseline outputs, aligned by stable query identifiers.
- **Guard** a CI pipeline with an explicit minimum metric delta and exit code 2.
- **Report** macro-averaged results, per-query metrics and HTML, JSON or spreadsheet-safe CSV output.
- **Integrate** custom, LangChain, LlamaIndex and optional FAISS retrievers using stable document IDs.
- **Reproduce** seeded, paired-bootstrap uncertainty intervals without a cloud API.

**Latest published version:** [v0.6.0 GitHub alpha pre-release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.6.0) (audited wheel, source archive and SHA-256 checksums; **not on PyPI**). This tool evaluates **retrieval relevance**, not generated-answer correctness or hallucination rates. The real SciFact results were cross-checked using a separate TREC scoring path in CI; they do not prove broad model superiority or independent external adoption.

**Language:** English documentation (primary) · [Türkçe hızlı başlangıç](docs/README_TR.md)

**Start here:** [Run the short Guard demo](docs/DEMO_60_SECONDS.md) · [Use your own RAG retriever](docs/OWN_RAG_QUICKSTART.md) · [Türkçe hızlı başlangıç](docs/README_TR.md) · [Report a real setup problem](https://github.com/ilker-Akbal/openrag-bench/issues/4)

**Package vs. repository:** The published **v0.6.0 wheel** includes Guard, Golden Dataset Studio and Capture & Replay. The newer `examples/quickstart_capture_replay.py` demonstration is available in the current **`main` source checkout**, not inside that published wheel. Self-authored CI checks are not evidence of external adoption.


**Read by topic:** [Setup](#get-started) · [Guard / Studio / Capture](#what-the-toolkit-does) · [Evaluation formats](#evaluation-formats-and-metrics) · [Retriever integrations](#retriever-integrations) · [Real-data benchmarks](#reproducible-real-data-benchmarks) · [Quality gates](#development-quality-gates--current-source) · [Contributing](#contribute-get-support-and-verify-results)

## Get started

Tested in CI on **Python 3.10–3.13**. The package declares Python >=3.10;
newer interpreter versions are not yet part of our tested matrix.

**Option A — install the published v0.6.0 wheel** (offline evaluation after installation; downloading the wheel requires network access):

~~~bash
python -m pip install https://github.com/ilker-Akbal/openrag-bench/releases/download/v0.6.0/openrag_bench-0.6.0-py3-none-any.whl
openrag-bench --help
openrag-bench init --directory openrag-demo
openrag-bench guard openrag-demo/candidate.json --baseline openrag-demo/baseline.json --policy openrag-demo/guard-policy.json --k 1 --html guard.html
~~~

Open `guard.html` in your browser (Windows PowerShell: `Start-Process .\guard.html`). The sample candidate passes its configured Guard policy. To see an **intentional BLOCK** (exit code **2**) without clobbering any files:

~~~bash
openrag-bench guard openrag-demo/candidate-regression.json --baseline openrag-demo/baseline.json --policy openrag-demo/guard-policy.json --k 1 --html guard-blocked.html
~~~

**Option B — clone `main` for examples, tests and the newer Capture/Replay demo:**

~~~bash
git clone https://github.com/ilker-Akbal/openrag-bench.git
cd openrag-bench
python -m pip install -e .
python examples/quickstart_capture_replay.py --output-dir reports/first-demo
~~~

Open `reports/first-demo/guard.html` (Windows: `Start-Process .\reports\first-demo\guard.html`). This synthetic demo **correctly blocks** a critical loss despite an aggregate score increase. Its **wrapper exits 0** when the expected blocked result is verified; an ordinary blocked `guard` or `replay` CLI call returns **2**. Use a fresh output directory on subsequent runs; the demo refuses to overwrite captures.

See [step-by-step demo](docs/DEMO_60_SECONDS.md), [versioned v0.6.0 release assets](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.6.0), and [bring-your-own-retriever integration](docs/OWN_RAG_QUICKSTART.md).

## What the toolkit does

### OpenRAG Guard — critical-query regression policies

OpenRAG Guard checks **scoped retrieval quality policies**. It can block
an update when the overall NDCG improves but a critical privacy question
loses its relevant document.

~~~bash
# Run after the one-time "init" step in Get started.
openrag-bench doctor openrag-demo/candidate.json --baseline openrag-demo/baseline.json --policy openrag-demo/guard-policy.json --k 1
openrag-bench guard openrag-demo/candidate.json --baseline openrag-demo/baseline.json --policy openrag-demo/guard-policy.json --k 1 --html guard.html
~~~

Run the `candidate-regression.json` example from **Get started** to see the critical loss correctly **blocked** (exit status 2). All bundled demo inputs are original synthetic data. See the [OpenRAG Guard policy and Action guide](docs/GUARD.md). Guard is included in the published v0.6.0 wheel.

### Golden Dataset Studio — offline human relevance labels

Generate a **standalone offline browser editor** without a server, account or API key:

    openrag-bench studio --output golden-dataset-studio.html

Open the generated HTML file in any local browser (on Windows: Start-Process .\golden-dataset-studio.html).
Add document IDs, create human-reviewed questions, grade relevant documents 1–3,
mark critical queries, import existing JSON rows, and explicitly download
editable drafts, positive-judgment rows and a versioned Guard policy.

**No automatic saving or uploads.** Save an editable draft before closing the tab.
The exported golden labels intentionally have empty retrieved_ids: the user's
actual retriever must fill rankings in candidate and baseline before evaluation.
See [Studio documentation](docs/STUDIO.md).

**Status:** Studio was introduced in v0.5.0 and is included in the published **v0.6.0** wheel. Python, CLI and JavaScript UI smoke tests pass; **independent human browser and accessibility testing remains open**. It is an alpha tool, not an audited production collaboration or document management platform.

### Capture & Replay — record real rankings and replay Guard

The published v0.6.0 release adds offline `capture` for joining actual ranked
retriever results with human-reviewed Golden Dataset Studio labels. A strict
optional raw-to-canonical document ID mapping prevents silent ID mismatches.
`replay` uses the existing Guard engine to compare saved baseline/candidate
snapshots without rerunning a model. Both commands are included in the
published v0.6.0 wheel; older v0.5.0 wheels do not include them.

See [Capture & Replay design and usage](docs/CAPTURE_REPLAY.md).

A reproducible real-data example uses actual SciFact TF-IDF and BM25 ranked
searches (external dataset, checksum verified) with Capture and Guard Replay:

~~~bash
python examples/scifact_capture_replay.py --download --k 10
~~~

The dataset is not checked into this repository; only aggregate numbers are
published, and locally generated per-query data must remain private.

### First Capture & Replay report without cloud access

Run an original, small lexical retrieval example with real ranked IDs and a
deliberate **critical-query release block**, even though overall retrieval
NDCG improves. After the source checkout is installed, this synthetic demo needs no model, API key or network access:

~~~bash
python examples/quickstart_capture_replay.py --output-dir reports/quickstart
~~~

Open `reports/quickstart/guard.html`. A **BLOCKED** policy is the expected result, and the demo wrapper returns 0 because it verified that block. The dataset is synthetic and does **not** establish independent adoption. For LangChain, LlamaIndex or custom retrievers, see the [bring-your-own-RAG walkthrough](docs/OWN_RAG_QUICKSTART.md).

### Offline HTML diagnostic explorer

Standalone interactive HTML reports show per-query worst regressions, judgment coverage, empty retrieval cases, top-k overlap, and local metric filtering. Reports contain query IDs, **not raw question text or document IDs**.

They use no external scripts or trackers.

The v0.6.0 package includes a report-first dashboard
with a clear **release decision**, critical-query before/after ranking
evidence, plain-English policy failures, an explicit warning when a passed
policy permits individual regressions, filters, and collapsed technical
metrics. The query diagnostics table now fits a desktop viewport and remains
horizontally scrollable on narrow screens.

A more diverse, original six-query demo at `k=3` helps distinguish metrics:

~~~bash
openrag-bench guard examples/report_diverse_candidate.json --baseline examples/report_diverse_baseline.json --policy examples/guard_policy.json --k 3 --html report_diverse.html
~~~

This scenario has multiple positive documents and differing rankings; it
does not represent an independent production benchmark.

~~~bash
openrag-bench examples/comparison_candidate.json --baseline examples/comparison_baseline.json --k 2 --html diagnostics.html
~~~

## Evaluation formats and metrics

### JSONL input and CSV diagnostics

Use newline-delimited retrieval records directly and export spreadsheet-safe, query-level metric comparisons:

```bash
openrag-bench examples/retrieval_results.json --csv per_query.csv --k 2
openrag-bench examples/comparison_candidate.json --baseline examples/comparison_baseline.json --csv deltas.csv --k 2
```

CSV reports exclude raw question text and protect against spreadsheet formula injection. See [data formats](docs/USAGE.md).

### Bounded-memory JSONL summary mode

For large labeled JSONL datasets, evaluate without materializing the complete input or per-query report:

~~~bash
openrag-bench your-labeled-queries.jsonl --streaming-summary --k 5 --output summary.json
~~~

The `your-labeled-queries.jsonl` path above is a **placeholder for your own labeled JSONL input**, not a file bundled with this repository. This mode writes only aggregate metrics and rejects baselines, HTML, CSV and TREC inputs. Normal JSONL/JSON/TREC behavior remains unchanged. See the [streaming guide](docs/USAGE.md) and [100k-query synthetic benchmark evidence](benchmarks/streaming_100k_2026-10-13.json).

On one Python 3.11 GitHub runner, Python peak allocations were 0.302 MiB streaming versus 121.297 MiB batch, while streaming took 12.46 s versus 9.42 s batch. This is a **memory-for-speed tradeoff**, not a production throughput or total system RAM claim.

### Graded judgments and MAP@k

Beyond binary relevance, evaluate documents labeled with positive integer relevance grades, including standard graded TREC qrels:

```bash
openrag-bench examples/trec_candidate.run --qrels examples/trec_graded.qrels \
  --graded-qrels --k 2 --metric graded_ndcg_at_k
```

The original binary NDCG definition remains unchanged. See [metric definitions and graded JSON input](docs/USAGE.md).

### Compare two retrieval versions

```bash
openrag-bench examples/comparison_candidate.json \
  --baseline examples/comparison_baseline.json \
  --k 2 --metric ndcg_at_k --min-delta 0 \
  --output comparison.json --html comparison.html
```

A negative delta means the candidate scored worse than the baseline. With `--min-delta 0`, the CLI exits with code `2` if that metric regresses. Use this as a deterministic engineering gate, **not** as a statistical significance test.

### Evaluate standard TREC run files

No custom JSON conversion needed for common information-retrieval datasets.

Given four-column `qrels` and six-column `run` files:

```bash
openrag-bench examples/trec_candidate.run \
  --qrels examples/trec.qrels \
  --baseline examples/trec_baseline.run \
  --k 2 --metric ndcg_at_k --min-delta 0
```

Each query from the qrels contributes to the score even when the run returns nothing. Positive relevance grades count as relevant; zero and negative judgments are not relevant. Unknown query IDs, duplicate docs, duplicate ranks and invalid scores are rejected.

## Retriever integrations

### How it works

Your RAG system supplies a ranked list of retrieved document IDs for each labeled question. OpenRAG Bench compares those rankings against explicitly documented relevant IDs. With a baseline and candidate JSON file, it reports per-query differences and seeded paired-bootstrap confidence intervals. Comparisons require matching query IDs and ground-truth labels.

No models are downloaded and the evaluation core makes no network calls.

### Integrate a retriever using the Python protocol

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

The code above is a **protocol illustration using fixed returned IDs**, not a real search benchmark. Replace the example retriever with your own ranking system. An optional FAISS adapter and a reproducible synthetic-vector example are provided (run from a source checkout):

```bash
python -m pip install '.[faiss]'
python examples/faiss_integration.py
```

### Use existing LangChain or LlamaIndex retrievers

Plug in LangChain `invoke(query)` retrievers or LlamaIndex `retrieve(query)` retrievers without installing those frameworks as mandatory package dependencies. Both adapters extract stable document/node IDs and reject duplicates.

See the [framework integration guide](docs/FRAMEWORK_INTEGRATIONS.md).

In addition to offline contract mocks, an [optional actual-framework vector-store test](examples/framework_real_integration.py) uses LangChain InMemoryVectorStore and LlamaIndex VectorStoreIndex with original synthetic keyword embeddings. The [dedicated integration workflow](.github/workflows/framework-real-integration.yml) checks specific pinned framework versions; this is not a semantic quality benchmark or proof of compatibility across all releases.

#### Verified installed-framework compatibility

Both pinned packages passed true offline vector-store integration on GitHub Actions: LangChain core **1.6.5** and LlamaIndex core **0.14.25** (Python 3.11.17). See the [actual passing framework run](https://github.com/ilker-Akbal/openrag-bench/actions/runs/38456230435).

The tiny synthetic keyword-vector exercise is a compatibility check, not semantic retrieval benchmarking.

## Reproducible real-data benchmarks

### Reproduce a real dataset benchmark

Run two lexical retrieval baselines against the externally hosted **BEIR SciFact test** split (5,183 scientific abstracts; 300 judged queries):

```bash
python examples/scifact_benchmark.py --download --k 10 --output-dir reports/scifact
```

The tool explicitly downloads the official 2.8 MB ZIP, verifies the checksum, reads it without extracting files, builds a local inverted index, runs **TF-IDF cosine** and **BM25**, and saves ranked TREC run files plus aggregate and per-query comparisons. Python standard library is sufficient.

**Verified results are published:** BM25 NDCG@10 **0.6605**, versus TF-IDF **0.6329** on 300 judged queries. See the exact [reproduction, data attribution and limitations](docs/BENCHMARK_SCIFACT.md) and [aggregate-only metrics](benchmarks/scifact_2026-10-13.json). The dataset retains its respective licenses; no data is included in this code repository.

### Dense embeddings + FAISS (optional)

A separate [CPU-capable real-data walkthrough](docs/DENSE_SCIFACT.md) compares a pinned Sentence Transformers MiniLM embedding model with BM25 using FAISS exact vector search:

```bash
python -m pip install -e '.[dense]'
python examples/scifact_dense_faiss.py --download --k 10
```

**Real dense model results have now been verified** on 5,183 SciFact documents and 300 judged queries: MiniLM + FAISS NDCG@10 **0.6451** versus BM25 **0.6605**. See the [provenance and limitations](docs/DENSE_SCIFACT.md) and [verified aggregate metrics](benchmarks/scifact_dense_2026-10-13.json).

Ordinary unit CI does not download weights; a dedicated GitHub Actions workflow performs the real model evaluation.

### Human-labeled Turkish retrieval benchmark

A dedicated offline Python evaluator measures BM25 under Unicode casefolding versus Turkish-specific dotted/dotless-I casing on an **external** dataset of 54 Turkish Wikipedia articles and **58 human-annotated Turkish questions**.

The corpus is CC BY-SA 4.0 and **is downloaded at test time only**, not redistributed with our MIT package. No third-party question/article content is written to published GitHub reports.

~~~bash
python examples/turkish_real_benchmark.py --download --k 10 --output turkish_summary.json
~~~

See [provenance, exact pinned revision, data limitations and results](docs/TURKISH_BENCHMARK.md).

These are article-level lexical retrieval baselines on a single health-domain set, not multilingual model certification.

## Development quality gates — current source

The Python 3.11 CI job runs Ruff lint, measured line coverage with a **90% minimum**, and Hypothesis property tests alongside ordinary unit tests. The CI matrix also checks Python 3.10, 3.12 and 3.13; historical coverage percentages should not be mistaken for current measurements.

Development tooling remains an **optional** install, not a mandatory runtime dependency.

~~~bash
python -m pip install -e '.[dev]'
python -m ruff check openrag_bench tests
python -m coverage run --source=openrag_bench -m unittest discover -s tests -v
python -m coverage report -m
python -m unittest discover -s tests -p property_metrics.py -v
~~~

See [quality requirements and actual measured coverage](docs/QUALITY.md).

## Contribute, get support and verify results

The tool is maintained in the open. You can install the existing public pre-release, reproduce the verified SciFact results, report bugs with tiny synthetic fixtures, or suggest a new retriever adapter. Contributions and issues must come from real users; no usage figures are claimed.

- [Reproduce independently or contribute](docs/GET_INVOLVED.md)
- [EN/TR community introduction](docs/COMMUNITY_OUTREACH.md) and [public feedback issue](https://github.com/ilker-Akbal/openrag-bench/issues/4)
- [Ask a usage question or report a reproducible bug](SUPPORT.md)
- [Contributor guidelines](CONTRIBUTING.md)
- [Report a security concern](SECURITY.md)
- [Verified v0.6.0 release assets and checksums](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.6.0)

## Documentation

- [First-run demonstration and expected BLOCKED report](docs/DEMO_60_SECONDS.md)
- [Golden Dataset Studio](docs/STUDIO.md) · [Capture & Replay](docs/CAPTURE_REPLAY.md) · [Guard policy](docs/GUARD.md)
- [Connect your own retriever](docs/OWN_RAG_QUICKSTART.md) · [LangChain/LlamaIndex adapters](docs/FRAMEWORK_INTEGRATIONS.md)
- [Türkçe hızlı başlangıç](docs/README_TR.md)
- [Input format, metric definitions and limitations](docs/USAGE.md)
- [Contributor guide](CONTRIBUTING.md)
- [Security guidance](SECURITY.md)
- [Provenance and third-party asset policy](docs/PROVENANCE.md)
- [Development roadmap](docs/ROADMAP.md)
- [Latest public GitHub release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.6.0)

This repository contains the standalone toolkit only, **not** the ROKETSAN workshop archive. Third-party material from that archive is deliberately excluded.

## License

MIT; see [LICENSE](LICENSE). No permission is claimed over third-party workshop content or externally supplied benchmark datasets.
