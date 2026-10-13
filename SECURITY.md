# Security policy

OpenRAG Bench is an experimental command-line development toolkit. No stable
release or security-response-time guarantee is currently offered.

## Reporting vulnerabilities

Please use GitHub's private vulnerability reporting from the
[Security page](https://github.com/ilker-Akbal/openrag-bench/security) if
available. If it is not enabled, open a non-sensitive issue asking the
maintainer to provide a private reporting channel. Never post exploits,
private documents, credentials or personally identifiable information.

## Data handling

The evaluation core makes no network requests and requires no API key.
Benchmark question strings and document identifiers are copied into reports,
so treat outputs as potentially sensitive. Do not serve the CLI directly on
the public internet without resource limits, validation and isolation.

HTML output escapes untrusted display strings. Optional FAISS support does
not download models, send telemetry or persist indexes.

## Current maintainer setup

The repository owner should enable **Private vulnerability reporting** under
GitHub repository Settings → Security → Code security and analysis (where
available). This setting is managed on GitHub, not by the files in this
repository. Do not assume it is enabled merely because `SECURITY.md`
exists. Do not attach confidential exploit details to a public issue.
