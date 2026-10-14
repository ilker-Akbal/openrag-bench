# Non-LinkedIn community outreach — ready-to-review publication kit

Status: **PREPARED, NOT PUBLISHED EXTERNALLY**. The maintainer-authorized
GitHub feedback request is live at https://github.com/ilker-Akbal/openrag-bench/issues/4.
No public Reddit, Hacker News, DEV Community post, or personal invitation is
claimed here. These drafts are only for the owner's accounts and final review.

For latest instructions and product scope, see
[the short demo](DEMO_60_SECONDS.md),
[community introduction](COMMUNITY_OUTREACH.md), and
[v0.6.0 GitHub alpha](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.6.0).

**Important distinction:** v0.6.0 is the latest published *wheel*, while
\`examples/quickstart_capture_replay.py\` currently lives in the **main
source checkout**, not in that release wheel. Never promise that the demo
script can be run from the wheel alone.

## Channel 1 — r/github self-promotion megathread

**Verified destination (2026-10-14):**
https://www.reddit.com/r/github/comments/1jy8rea/promote_your_projects_here_selfpromotion/

The thread explicitly welcomes software projects and asks for a description
and GitHub repository link. Post a **single comment to the existing
megathread**, not a standalone self-promotion post. Confirm the thread
remains open before sending, and follow the latest community rules. Link to
the repo only; avoid repeated promotion or vote requests.

### Reddit comment — English (paste after personal review)

I maintain **OpenRAG Bench**, an MIT-licensed Python tool for evaluating
RAG *retrieval* quality offline.

Why I made it: upgrading an embedding model or retriever can improve
average metrics while losing an important answer-supporting document for a
specific question. OpenRAG Bench compares ranked document IDs against
human-reviewed judgments and uses configurable quality policies to block
these regressions.

It includes a local Golden Dataset Studio, Capture & Replay, and offline
HTML/JSON reports. The latest public **alpha** is v0.6.0; the core requires
no cloud LLM, API key or GPU. There is a runnable **synthetic** source-checkout
demo where aggregate NDCG improves but the Guard blocks a lost critical
privacy hit.

Repo: https://github.com/ilker-Akbal/openrag-bench
Try-it guide:
https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/DEMO_60_SECONDS.md

I'd particularly appreciate real setup/CLI feedback from people who use
LangChain, LlamaIndex or custom retrievers. Please share redacted bugs or
questions in https://github.com/ilker-Akbal/openrag-bench/issues/4 .

The tool measures retrieval relevance, **not** LLM answer factuality.
This is my project, and I have no independently verified adopters to cite yet.

## Channel 2 — Hacker News: Show HN

**Official guidelines:** https://news.ycombinator.com/showhn.html
**Submission UI:** https://news.ycombinator.com/submit

The official instructions require a project people can try, a title that
begins \`Show HN\`, and active participation by its maker. Link directly
to the **GitHub repository**, not this outreach document. Do not ask
others to upvote/comment and do not use multiple accounts.

### Submission fields

**Title:**
Show HN: OpenRAG Bench – Offline regression checks for RAG retrieval

**URL:**
https://github.com/ilker-Akbal/openrag-bench

**Optional first explanatory comment (review and post as the maintainer):**

I built OpenRAG Bench because I wanted to compare changes to RAG retrieval
pipelines without needing a hosted LLM judge. The core is standard-library
Python: it scores ranked document IDs against labeled relevance judgments
and checks regression policies in CI.

One failure mode I wanted to expose: the candidate can improve macro NDCG
but stop retrieving the required document for a critical query. The
synthetic demo in the repo intentionally produces that outcome. You can
run it after cloning the main branch and installing in editable mode:

\`python examples/quickstart_capture_replay.py --output-dir reports/first-demo\`

Open \`reports/first-demo/guard.html\` for the offline decision report. The
demo wrapper returns 0 after verifying the expected **blocked** policy; the
raw blocked Guard/Replay exits 2.

I also tested actual BM25 and TF-IDF retrieval on the 300-query SciFact
test set, where BM25 achieved 0.6605 vs 0.6329 NDCG@10 (one dataset,
not a universal quality claim). The v0.6.0 alpha release includes Capture
& Replay and Golden Dataset Studio. It measures retrieval quality,
not LLM answers or hallucinations.

I'd appreciate feedback on stable document IDs, the evaluation schema,
and the setup steps. Real use/production adoption has not been verified.

**Before submitting:** Confirm you can answer technical questions soon after
publication and that the current repository instructions still work.
If you cannot participate, save this draft rather than posting and leaving.

## Channel 3 — DEV Community: hands-on Python tutorial

**DEV Python tag:** https://dev.to/t/python
**DEV tutorial tag:** https://dev.to/t/tutorial
**Open Source tag cautions:** https://dev.to/t/opensource

The DEV \`#tutorial\` guidance encourages teaching by example; the
\`#opensource\` tag explicitly says **not** to use it for simple project
promotion. Suggested tags: \`#python\`, \`#tutorial\`, \`#testing\`,
\`#ai\` (only tags that exist and fit the final article). Verify before
publishing. This is a tutorial, not a release announcement.

### Draft tutorial — Markdown

# When Your RAG Retriever Improves Overall but Breaks an Important Query

Changing an embedding model, chunk strategy or retriever can move
aggregate retrieval scores in the right direction while losing a document
required by a particular question. Here's a tiny, reproducible Python
demonstration of why *query-level regression checks* matter.

## A concrete failure mode

Imagine three queries: privacy, setup and warranty. A baseline finds the
privacy guide but misses setup and warranty. A candidate finds the latter
two but no longer finds the privacy guide.

At cutoff \`k=1\`, the simple binary-relevance illustration gives:

| Query | Baseline hit@1 | Candidate hit@1 |
| --- | ---: | ---: |
| Privacy — critical | 1 | 0 |
| Setup | 0 | 1 |
| Warranty | 0 | 1 |
| **Macro average** | **1/3** | **2/3** |

The candidate's average improves, but the **critical query regresses**.
A single overall score doesn't encode which query must never lose a hit.

## Reproduce with a tiny actual lexical retriever

I maintain an open-source Python project, **OpenRAG Bench** (MIT).
Its demonstration uses original **synthetic** documents and performs
a basic keyword-overlap retrieval for each query. It does not copy the
expected labels into the retrieved rankings.

~~~bash
git clone https://github.com/ilker-Akbal/openrag-bench.git
cd openrag-bench
python -m pip install -e .
python examples/quickstart_capture_replay.py --output-dir reports/first-demo
~~~

Open \`reports/first-demo/guard.html\`.

Expected: the Guard decision is **BLOCKED**, even though the candidate's
aggregate NDCG@1 improves. The demo wrapper exits with 0 because it
correctly detected the intentional block; a direct replay of that same
blocked comparison returns 2.

This newer example is shipped in the **current main source checkout**.
The published v0.6.0 GitHub wheel supports Capture/Replay but doesn't
include this example script.

## What gets checked?

- **Golden judgments:** a person designates the relevant document ID
  for each query, with an optional critical flag.
- **Observed rankings:** the baseline and candidate retrievers return
  actual ordered document IDs. Neither the model nor the benchmark may
  invent "correct" rankings from golden labels.
- **Capture:** records each observed run with the same query IDs and
  canonical stable document IDs.
- **Replay/Guard:** compares results and enforces a critical hit rule
  in addition to the macro non-regression rule.
- **Report:** displays the decision and query-level diagnostic changes.

The protected privacy query is a **policy choice**, not an LLM safety
certification. A passing check says only that the chosen policy passed
for the evaluated data.

## Bringing your own retriever

A real integration must supply query text and ranked document IDs that
remain stable between indexing versions. The tool offers adapters for
LangChain and LlamaIndex, but framework-specific retrieval behavior must
be tested in your environment.

Guide: https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/OWN_RAG_QUICKSTART.md

For real retrieval evidence, BEIR SciFact was evaluated separately with
5,183 abstracts and 300 judged test queries. TF-IDF NDCG@10 was 0.6329;
BM25 was 0.6605 for this particular evaluation. This does not prove
general superiority or statistical significance.

Repository: https://github.com/ilker-Akbal/openrag-bench
Reproducible mini-demo:
https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/DEMO_60_SECONDS.md

I'd appreciate **actual installation friction and schema feedback**, positive
or negative. Please don't share private prompts, corpora or credentials.
Feedback issue: https://github.com/ilker-Akbal/openrag-bench/issues/4

## Optional fourth route — two or three genuine developer contacts

This is not a mass-DM campaign. Ask only developers you already know, or
people **who explicitly invited review of their own RAG pipeline**.

**Short personal invitation:**

I'm maintaining OpenRAG Bench, an offline retrieval evaluation tool. Would
you be willing to try a tiny synthetic baseline/candidate demo on your own
machine and tell me what is confusing or breaks? It should work with no
LLM API key. Repo: https://github.com/ilker-Akbal/openrag-bench
Instructions: https://github.com/ilker-Akbal/openrag-bench/blob/main/docs/DEMO_60_SECONDS.md
Any negative feedback is welcome; no need to share private RAG data.

Do not claim private invitations were sent unless they actually were.

## Actual distribution and feedback log

| Destination | Status | Proof / next action |
| --- | --- | --- |
| GitHub issue #4 | **PUBLIC** | https://github.com/ilker-Akbal/openrag-bench/issues/4 |
| r/github megathread | **NOT POSTED** | Requires signed-in Reddit account and final user submission |
| Hacker News Show HN | **NOT POSTED** | Requires signed-in HN account and maker's participation |
| DEV Community | **NOT POSTED** | Requires signed-in DEV account and tutorial publication |
| Invited developers | **NOT CONTACTED** | Requires developer contact and consent to receive invitation |
| LinkedIn | **EXCLUDED BY REQUEST** | Do not prepare or publish under this outreach plan |

Only after a real post is submitted should its date and permalink be
added to this log. Do not fabricate audience size, replies, installs,
reviews, stars or benchmark reproductions.
