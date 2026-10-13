# Contributing to OpenRAG Bench

Thanks for helping developers make RAG retrieval evaluation reproducible.

## Development

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
openrag-bench examples/retrieval_results.json --k 2
```

Python 3.10–3.13 is tested in CI.

Please open an issue before undertaking large changes. Every fix should include
a deterministic test (preferably demonstrating the failure before the fix).
Describe any changes to metric semantics, dataset schema, backwards
compatibility or optional dependencies.

Never submit API keys, customer data, proprietary documents, unlicensed
workshop assets, or copied benchmark datasets. Explain data sources and labels
in any proposed evaluation. Synthetic fixtures are tests, not evidence of
production benchmark performance.

This project's source code is available under MIT; dependencies and
third-party datasets retain their respective licenses.

Be constructive, respectful and specific when reporting issues and reviewing PRs.
