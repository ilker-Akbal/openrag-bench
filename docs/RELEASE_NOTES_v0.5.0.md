# OpenRAG Bench v0.5.0 — Golden Dataset Studio (public alpha pre-release)

This version introduces a standalone browser-based human labeling tool for
RAG retrieval evaluation. The editor runs entirely offline, with no HTTP
server, cloud service, API key, bundled model, automatic saving or telemetry.

## Golden Dataset Studio

Run from the installed wheel:

```powershell
python -m pip install openrag_bench-0.5.0-py3-none-any.whl
openrag-bench studio --output golden-dataset-studio.html
Start-Process .\golden-dataset-studio.html
```

- Create a local document-ID catalog and human-labeled queries.
- Mark graded positive relevance 1–3, categories and critical queries.
- Import existing JSON rows or editable Studio drafts.
- Download a portable draft, guarded policy version 1 and validated
  judgment rows. Browser data is not automatically persisted.
- Restrictive CSP, safe DOM text insertion, no network calls.
- Refuse duplicate IDs, stale labels and judgment export with no positives.

**Important:** Golden judgments intentionally export **retrieved_ids: []**.
They are **not measured retrieval results**. Your own retriever must create
candidate and baseline rankings for these query IDs before running Doctor
or Guard. Default Guard policy thresholds should be reviewed.

## Test evidence and scope limits

- Protected Python 3.10–3.13 CI and CodeQL checked.
- Python 3.11 Ruff, >=90% coverage threshold, property tests and
  isolated wheel/source installs.
- Automated Node JS syntax and DOM-logic smoke covering synthetic
  data import/export, duplicate IDs and generated Guard policy.
- Existing SciFact and 100k synthetic retrieval pipelines remain supported.
- Wheel/source contents audit plus verified SHA256SUMS.
- No third-party browser usability or mobile accessibility testing claimed.
  The editor is an **alpha** tool; data accuracy depends on human labels.

Full guide: https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/STUDIO.md

Previous pre-release tags/assets remain immutable. No PyPI publication.
