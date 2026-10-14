# OpenRAG Bench v0.4.1 — report usability maintenance release

This GitHub **pre-release** makes the v0.4 Guard evaluation easier to
understand, without changing metrics, data format semantics, policy
pass/block behavior, required dependencies, or prior release artifacts.

## Report improvements

- Immediately visible PASS/BLOCK decision, baseline/candidate NDCG, query
  ranking changes and comprehensible policy failures.
- A **PASSED** policy now displays a separate warning when one or more
  individual queries regress on NDCG@k within the policy limits.
- Fixed desktop table layout prevents the Outcome column from disappearing
  off the right edge; narrow viewports retain accessible horizontal scrolling.
- Original six-query diverse-ranking demonstration at k=3 and regression
  tests for passing-with-regressions, blocked queries, offline safety and XSS.

## Tested and auditable

Python 3.10–3.13, enforced Python 3.11 Ruff, unit tests, Hypothesis
invariants, >=90% coverage gate, SciFact benchmark workflow, CodeQL,
clean wheel and source installs, verified SHA256SUMS. Does **not** claim
any independent production user adoption. Reports contain query IDs but
not raw question text or document IDs; keep query IDs private if sensitive.

## Installation

Download the attached wheel from the v0.4.1 release and verify SHA256SUMS.

```bash
python -m pip install openrag_bench-0.4.1-py3-none-any.whl
openrag-bench init --directory openrag-demo
openrag-bench guard openrag-demo/candidate-regression.json --baseline openrag-demo/baseline.json --policy openrag-demo/guard-policy.json --k 1 --html blocked.html
```

The negative fixture exits with code 2, as designed. The positive fixture
passes with code 0. Version v0.4.0 remains available and immutable.
No PyPI publication is claimed.
