# OpenRAG Bench v0.4.0 — OpenRAG Guard

GitHub **pre-release**, MIT, Python 3.10–3.13; no paid LLM API and **not on PyPI**.

## Catch a critical RAG retrieval regression before deployment

OpenRAG Guard prevents a new retrieval configuration from being accepted when
a critical question fails even though the overall macro-averaged NDCG improves.
This is deterministic testing against *human-assigned* positive document IDs,
not a claim about the quality of generated LLM answers.

New features:
- Versioned and strict JSON quality policies for all, critical, category and
  explicitly selected query IDs; per-query minimum scores and allowable
  regressions as well as macro-score thresholds.
- Five-minute init / doctor / guard CLI, original synthetic example,
  redacted machine/HTML reports, observed lost/gained top-k hits and rank changes.
- Reusable read-only GitHub composite Action with fail-closed PR status and
  escaped aggregate Step Summary; no external API or PR write permission.
- A real CI negative test verifies that a critical privacy query causes
  status 2 despite increasing the overall macro NDCG@1.

Verified Python 3.10–3.13 matrix, **77 standard unit tests**, three Hypothesis
properties, **93% line coverage** in tested Python 3.11 build (>=90% CI gate),
real SciFact and 100k-query synthetic benchmark CI. This does not establish
independent users, production SLAs, causal model diagnosis or answer factuality.

## Install and try

Download the attached wheel and check its digest against SHA256SUMS:

~~~bash
python -m pip install openrag_bench-0.4.0-py3-none-any.whl
openrag-bench init --directory openrag-demo
openrag-bench guard openrag-demo/candidate.json --baseline openrag-demo/baseline.json --policy openrag-demo/guard-policy.json --k 1 --html guard.html
~~~

Replace candidate.json with candidate-regression.json to reproduce a failure.
See [OpenRAG Guard documentation](https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/GUARD.md).

The source and wheel are verified from clean installations. Core runtime
dependencies remain empty. Prior versions and benchmark evidence are intact.
No private data, workshop source, third-party corpus or model weights are bundled.
