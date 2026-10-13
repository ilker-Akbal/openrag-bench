# OpenRAG Bench support and troubleshooting

OpenRAG Bench is an early-stage, volunteer-maintained open-source project.
There is no paid support contract, guaranteed response time, or production SLA.

## Choose the right place

- **Usage question:** open a [GitHub issue](https://github.com/ilker-Akbal/openrag-bench/issues/new/choose)
  with your goal, Python/OS versions and the command you used.
- **Reproducible bug:** use the repository's Bug report template, including
  minimal *synthetic* JSON or TREC input (never private data).
- **Feature suggestion:** use the Feature request template and describe the
  retrieval workflow that would benefit.
- **Security concern:** follow [SECURITY.md](SECURITY.md); do not disclose
  vulnerability details in a public issue.
- **First contribution:** read [CONTRIBUTING.md](CONTRIBUTING.md) and
  [GET_INVOLVED.md](docs/GET_INVOLVED.md).

## Common checks

```bash
python --version
python -m pip install -e .
python -m unittest discover -s tests -v
openrag-bench --help
openrag-bench examples/retrieval_results.json --k 2
```

Use Python 3.10–3.13, the supported and CI-tested versions. The core uses
no paid API or runtime model downloads. For optional FAISS integration,
install `python -m pip install -e '.[faiss]'`; the dense SciFact walkthrough
uses `'.[dense]'` and downloads model weights from an external source.

If output metrics are unexpected, check document-ID alignment, labeling
coverage, duplicate IDs, the rank cutoff and metric definitions in
[docs/USAGE.md](docs/USAGE.md). Real SciFact benchmark results and
reproduction details are linked from the README.

For release verification, obtain `SHA256SUMS` from the
[v0.1.0 GitHub Release](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.1.0).
The project is **not** claiming distribution through PyPI.

## Data safety

Never attach proprietary corpora, confidential questions, customer data,
API keys or copied third-party PDF content to public GitHub issues.
