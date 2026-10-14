# OpenRAG Guard — offline quality policy and GitHub CI

## 5-minute onboarding

OpenRAG Guard prevents damaging retrieval changes even when the aggregate
quality metric increases. No LLM model, API key, hosted service or external
dependency is needed for core operation.

~~~bash
python -m pip install -e .
openrag-bench init --directory openrag-demo
openrag-bench doctor openrag-demo/candidate.json --baseline openrag-demo/baseline.json --policy openrag-demo/guard-policy.json --k 1
openrag-bench guard openrag-demo/candidate.json --baseline openrag-demo/baseline.json --policy openrag-demo/guard-policy.json --k 1 --html guard.html --output guard.json
~~~

The original synthetic passing case returns exit 0. Replace candidate.json
with candidate-regression.json to reproduce a **failed critical privacy
query even as overall NDCG rises**. This returns exit 2. A malformed policy
or missing critical query also errors (exit 2) rather than silently passing.

Init refuses to overwrite any pre-existing generated file. Doctor checks
schema, duplicate query IDs, paired ground truth and policy applicability;
it warns about missing positive labels but cannot verify whether labels are
factually correct.

## Policy v1 schema

The JSON policy declares exactly a version and a nonempty rules list.
Each rule needs an ID, a selection, a metric and at least one threshold:

~~~json
{
  "version": 1,
  "rules": [
    {"id": "overall-quality", "select": {"type": "all"},
     "metric": "ndcg_at_k", "min_delta": 0},
    {"id": "critical-coverage", "select": {"type": "critical"},
     "metric": "hit_at_k", "min_query_score": 1,
     "max_regressed_queries": 0},
    {"id": "privacy-category", "select": {"type": "category", "value": "privacy"},
     "metric": "recall_at_k", "min_score": 1}
  ]
}
~~~

Selection types:
- all — all aligned queries;
- critical — queries explicitly marked critical true in both runs;
- category — exact matching category string in both runs;
- query_ids — an explicit nonempty unique list of query IDs.

Required paired metadata is checked across candidate and baseline; categories
and critical flags must match. Critical and category labels are set by
the dataset author and are NOT inferred from the question text. Policies
that match no queries, reference missing IDs, or select queries with no
positive judgments error instead of passing.

Thresholds:
- min_delta: candidate minus baseline mean among selected queries;
- min_score: absolute candidate mean, inclusive (0 to 1);
- min_query_score: every selected query must meet this score (0 to 1);
- max_regressed_queries: highest number of individually regressed queries.

All specified thresholds must pass. An absolute numeric tolerance of 1e-12
accommodates floating point noise. This is deterministic testing, NOT a
statistical hypothesis test or guarantee that any AI response is true.

## Reading the redesigned HTML report (current development branch)

The offline dashboard places the Guard PASS/BLOCK decision and explanation
first; next are highlighted failed queries, first-relevant baseline/candidate
ranks, readable policy failures and sortable query diagnostics. The long
metric tables (baseline, candidate and signed deltas) sit in a collapsed
native HTML details section. No external CSS, JS, font, network request,
tracking or API key is required.

Ranks and lost/gained top-k hits are **observations**, not proofs of what
caused them. A missing rank means no positive-labeled document was returned
in the recorded ranked results; the top-k hit decision still uses the
configured cutoff. The highlighted ID list has policy-defined limits;
the query table retains all per-query rows for local filtering.

Metrics use 0–1 scores and **absolute** differences. For example,
0.3333 → 0.6667 is a +0.3333 delta (33.33 percentage points),
not a 33% relative improvement. On minimal single-positive `k=1`
fixtures, multiple evaluation metrics can legitimately have equal values.
To explore more varied rankings and graded relevance at `k=3`:

~~~bash
openrag-bench guard examples/report_diverse_candidate.json --baseline examples/report_diverse_baseline.json --policy examples/guard_policy.json --k 3 --html report_diverse.html
~~~

The two example files are original and synthetic. The released v0.4.0 wheel
predates this HTML facelift; use a reviewed source checkout for the new UI.

## Evidence and privacy

The report includes query IDs, mean scores, failed policies, and
observational first-relevant rank / lost-or-gained top-k-hit diagnostics.
It does **not** include original question text or document IDs. Rankings
are observable, but cause attribution (embedding, chunking, indexing)
requires additional experimental evidence. Query IDs can themselves
contain sensitive data; treat full JSON and HTML files as potentially
private. The GitHub step summary omits even query IDs.

## GitHub Action, no write permission required

For testing within this repository on a pull request:

~~~yaml
name: RAG Retrieval Quality
on: [pull_request]
permissions:
  contents: read
jobs:
  guard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: ./.github/actions/guard
        with:
          candidate: examples/guard_candidate.json
          baseline: examples/guard_baseline.json
          policy: examples/guard_policy.json
          k: '1'
          report: guard-result.json
~~~

The action prepares Python 3.11, installs its checked-out OpenRAG Bench
package locally and invokes the same strict CLI. It reports aggregate
rule statuses to the GitHub Step Summary with escaped rule labels. It
does not create PR comments, obtain API credentials, upload private data
or execute an LLM. The workflow status can be marked required by repository
branch rules after users have verified it.

In **other repositories**, use an immutable SHA-pinned reference to
ilker-Akbal/openrag-bench/.github/actions/guard after a reviewed v0.4.0
release, not a moving main branch. The RAG pipeline itself must produce
candidate and baseline ranking outputs; the action evaluates these files
and does not run the retriever automatically.

Guard is published as a GitHub v0.4.0 pre-release (not on PyPI).
Previous release tags and assets remain immutable.
