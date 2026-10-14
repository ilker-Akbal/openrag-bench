# Code quality and repeatable maintenance gates

OpenRAG Bench's ordinary dependency-free runtime has **zero mandatory
third-party Python dependencies**. Its *optional* dev extra isolates
the following pinned developer tools:

- ruff==0.17.0 — focused syntax errors, undefined/unused imports and E4/E7/E9/F checks
- coverage==7.16.2 — measure executed Python lines in openrag_bench
- hypothesis==6.168.5 — randomized but reproducible invariant tests for
  metric bounds, label order and paired candidate/baseline symmetry

## Reproduce

~~~bash
python -m pip install -e '.[dev]'
python -m ruff check openrag_bench tests
python -m coverage run --source=openrag_bench -m unittest discover -s tests -v
python -m coverage report -m --fail-under=90
python -m coverage xml -o coverage.xml
python -m unittest discover -s tests -p property_metrics.py -v
~~~

The optional Hypothesis file deliberately uses the
tests/property_metrics.py naming convention, so the ordinary four-version
unit test matrix can continue to run **without** installing any dev extras.
The existing **Python 3.11** status check in ci.yml executes these commands
and must pass under the active main-branch ruleset. The other 3.10, 3.12
and 3.13 jobs still run standard library unit tests and package smoke tests.

An earlier Python 3.11 CI report measured **95% line coverage**
(555 measured statements, 26 missed). More recent releases add further modules
and must be checked against the **current** CI coverage report rather than
reusing that historical count. The enforced threshold is set to
**90%**, leaving a small margin while catching substantial regressions.
This is actual line coverage under that test environment, **not** branch
coverage, production correctness or whole application security.
See the associated GitHub Actions quality job logs.

### Limitations

- Current lint selection E4/E7/E9/F catches selected actionable defects,
  not all style, security or typing issues.
- Property tests assert bounds, ground-truth permutation invariance,
  monotonic Recall/Hit/MRR across cutoffs, and paired-delta antisymmetry
  only. They cannot establish total correctness or model retrieval quality.
- Ruff is a linter, not a type checker; Python static type coverage remains
  future work.
- GitHub code scanning/Dependabot settings supplement but do not replace
  dependency audits or human code review.
- Data experiments and optional framework jobs may be network-dependent,
  while the package's core functions remain offline.

Node.js 24-compatible hosted action majors replace earlier versions.
Historical v0.1/v0.2 publish workflows remain **manual-only**, and this
quality change never creates a new public GitHub release.
