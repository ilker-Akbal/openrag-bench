# OpenRAG Bench v0.6.0 — Capture & Replay (GitHub alpha pre-release)

OpenRAG Bench v0.6.0 adds **deterministic, offline retrieval capture and
replay** that bridges human-labeled Golden Dataset Studio questions with
actual ranked document IDs from retrievers. It remains a retrieval
evaluation toolkit, **not** an answer-quality or LLM-safety evaluator.

## New commands

~~~powershell
openrag-bench capture openrag-golden-judgments.json --rankings baseline-rankings.json --output baseline.json --manifest baseline.manifest.json
openrag-bench capture openrag-golden-judgments.json --rankings candidate-rankings.json --output candidate.json --manifest candidate.manifest.json
openrag-bench replay candidate.json --baseline baseline.json --policy openrag-guard-policy.json --k 3 --html replay.html
~~~

- Exact query-ID pairing: rejects missing/extra/duplicate queries.
- Optional explicit raw-to-canonical document ID map; rejects missing mappings,
  duplicate or collapsed IDs.
- Preserve positive labels, graded judgments, category and critical metadata.
- Capture through an existing synchronous Python retriever via
  \`capture_from_retriever\`; no mandatory dependency, cloud API or LLM.
- Manifest with deterministic hashes and counts; no question content inside
  the manifest. **Captured dataset JSONs do include raw question text and
  ranked document IDs.**
- Exclusive output creation, rollback on failed manifest write; never replace
  an existing output on success.
- Replay is the existing Guard engine with its familiar exit codes and
  privacy-aware HTML report; it does not rerun a model.

## Verified real-data reproduction

The optional \`examples/scifact_capture_replay.py\` downloads the official
checksum-verified external BEIR SciFact archive only with \`--download\` and
runs real **TF-IDF cosine and BM25** lexical retrievers on all 5,183 corpus
documents and 300 judged test queries. Actual ranked IDs flow through
Capture and Guard Replay, then are checked against separately generated
standard TREC benchmark metrics.

- TF-IDF NDCG@10: 0.6329113317316912
- BM25 NDCG@10: 0.6604641499925741
- BM25 minus TF-IDF: +0.027552818260882638 (absolute)
- NDCG non-regression policy: PASSED
- Independently re-scored real-data CI workflow: passed (PR #47).
- **Only aggregate metrics and source checksum are published.** Third-party
  queries and retrieved document IDs are not committed or uploaded.

This experiment does not establish statistical significance, broad
generality or generated-answer truthfulness. SciFact labels are incomplete.

## Test and compatibility boundaries

- Python 3.10–3.13, protected Ruff and >=90% measured Python coverage.
- Automated negative tests for mapping collisions, duplicate labels, stale
  query IDs, bad results, file collision and partial manifest writes.
- Existing Guard, Studio, JSON/JSONL, TREC and SciFact workflows preserved.
- Build audited wheel/sdist, clean-install both distributions, and publish
  SHA256SUMS *before* considering this release verified.
- Optional models and external benchmark datasets **not included** in archives.
- v0.5.0 release and earlier tags must remain unchanged.
- Published on GitHub only, **not PyPI**.
- Independent outside user validation of broader Studio workflows remains open.

Full guide: https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/CAPTURE_REPLAY.md
