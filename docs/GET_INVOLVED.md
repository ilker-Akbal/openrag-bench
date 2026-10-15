# Help improve OpenRAG Bench

We welcome **genuine, independent** use, reproducible feedback, fixes and
documentation contributions. This project is young; its technical tests and
benchmarks are not evidence of a broad user base.

For Reddit, Hacker News or DEV Community feedback requests (LinkedIn excluded),
see the [channel-specific review-and-publish kit](OUTREACH_NO_LINKEDIN.md).
Published GitHub feedback issue #4 is the single place to report findings.

For a short first-run demonstration, see
[Capture & Replay demo](DEMO_60_SECONDS.md). If you try it without prior
involvement in the project, please report a **real** installation result,
environment and any blockers via
[our independent reproduction request](https://github.com/ilker-Akbal/openrag-bench/issues/4).
You can also read the [English/Türkçe feedback invitation](COMMUNITY_OUTREACH.md).

## 10-minute no-cloud quickstart

```bash
git clone https://github.com/ilker-Akbal/openrag-bench.git
cd openrag-bench
python -m pip install -e .
python -m unittest discover -s tests -v
openrag-bench examples/retrieval_results.json --k 2 --html report.html
openrag-bench examples/comparison_candidate.json \
  --baseline examples/comparison_baseline.json --k 2 --min-delta 0
```

Then open `report.html` locally; no GPU or API key is needed.

## First Capture & Replay report with an intentional critical-query block

After cloning and installing above:

~~~bash
python examples/quickstart_capture_replay.py --output-dir reports/quickstart
~~~

Open `reports/quickstart/guard.html`. The candidate improves aggregate
NDCG@1 while dropping a designated critical privacy guide, so the Guard
**must block** the update. This is a synthetic integration demonstration,
not independent retrieval evidence or a speed-of-onboarding measurement.

For your **own retriever**, follow
[Own RAG quickstart](OWN_RAG_QUICKSTART.md). Report true time-to-first-report,
environment, unexpected failures and only **redacted** logs. No production
secrets or private question/document text should be shared.

## Verified first-party integration in a separate RAG repository

OpenRAG Bench v0.6.0 has now been installed as a **real downstream
dependency** in the maintainer's separate, existing
[local Sentence Transformers + FAISS RAG practice repository](https://github.com/ilker-Akbal/roketsan-level-up-ai-2026).
The [merged integration PR #2](https://github.com/ilker-Akbal/roketsan-level-up-ai-2026/pull/2)
and [actual-model GitHub Actions run](https://github.com/ilker-Akbal/roketsan-level-up-ai-2026/actions/runs/38748708363)
verify real embedding inference, FAISS ranked document IDs, Capture & Replay
against the published v0.6.0 wheel, and a redacted Guard report.
An intentional overrestrictive threshold also caused a measured regression
that Guard rejected (exit code 2), as verified by that CI run.

**Exact observed first-run result:** six short original synthetic documents,
six author-labeled questions, BM25 **not involved**; NDCG@3 was 1.0000
for both FAISS score thresholds (0.35 and 0.20), with no quality gain.
The [full integration limits and commands](https://github.com/ilker-Akbal/roketsan-level-up-ai-2026/blob/main/docs/OPENRAG_BENCH_INTEGRATION.md)
make clear why this tiny exercise is not a broad benchmark.

**Integrity boundary:** This is a first-party cross-repository software
integration performed by the **same maintainer**, not an independent
external user, production deployment, third-party adoption, or evidence
of general model superiority. It does demonstrate that the installable
public release works in a separate repository with a real model and index.
We still need genuinely independent developers to test their own systems.

## Useful first contributions

1. Reproduce the [real SciFact experiment](BENCHMARK_SCIFACT.md) and compare
   the published metrics against your independently generated results.
2. Try the [dense FAISS integration](DENSE_SCIFACT.md), note hardware and versions.
3. Use your *own permitted data*, describe a case in which the metrics are
   surprising or difficult to interpret, and file a minimal synthetic repro.
4. Improve docs for non-English users or edge-case examples.
5. Submit regression tests and bug fixes as small, reviewable pull requests.

## Feedback we can act on

Please include installation method, Python/OS version, command, smallest
synthetic reproducer and expected versus actual behavior. Avoid sharing
non-public text, private questions, API keys or unlicensed benchmark data.

See [CONTRIBUTING.md](../CONTRIBUTING.md) and [bug report form](../.github/ISSUE_TEMPLATE/bug_report.yml).

A maintainer will review genuine issues and explain accepted/rejected changes;
reviews are not promised within a fixed period.
