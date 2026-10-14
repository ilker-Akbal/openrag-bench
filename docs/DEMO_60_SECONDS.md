# A short, reproducible OpenRAG Bench demo

[GitHub repository](https://github.com/ilker-Akbal/openrag-bench) ·
[Latest GitHub alpha release, v0.6.0](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.6.0) ·
[Turkish quickstart / Türkçe rehber](README_TR.md)

## The problem: "better on average" may still break a critical query

Suppose a retrieval pipeline is changed. It improves ordinary support queries,
but an important privacy query no longer retrieves its required document.

OpenRAG Bench evaluates **ranked document IDs** against human-reviewed relevance
judgments. Its Guard policy can block this candidate despite a higher **average
NDCG@1** score. It does **not** measure generated answer truthfulness or LLM
hallucinations.

## Try the example locally

Requirements: Git, Python 3.10–3.13, and internet access for the initial
clone/package installation. **The demo itself** requires no cloud model, GPU,
account, API key, downloaded dataset, or third-party Python runtime package.

~~~bash
git clone https://github.com/ilker-Akbal/openrag-bench.git
cd openrag-bench
python -m pip install -e .
python examples/quickstart_capture_replay.py --output-dir reports/first-demo
~~~

This example is in the **current main source checkout**. The latest published
wheel is v0.6.0, which has Capture & Replay but **does not include the newer
quickstart example**. Do not attempt to run the example from the wheel alone.

Open the locally created file \`reports/first-demo/guard.html\` in a browser.
Windows PowerShell:

~~~powershell
Start-Process .\reports\first-demo\guard.html
~~~

macOS and Linux: open the file using your normal browser/file manager.

### Expected outcome

- A tiny **original synthetic** corpus and three labeled questions are used.
- Two actual simple lexical retrievers calculate rankings from query/document
  word overlap; the results are **not generated from the relevance labels**.
- The candidate improves the overall mean NDCG@1.
- A critical \`privacy\` document disappears from its query's top-1 result.
- The Guard report shows **BLOCKED**, failing the
  \`critical-privacy-hit\` policy.
- The example process exits with **0** because the intentional block was
  correctly detected. Running the \`replay\` CLI directly on the blocked
  candidate returns **2**. This distinction is important for CI.
- The script writes local \`golden.json\`, \`*-observed.json\`,
  \`baseline.json\`, \`candidate.json\`, manifests, \`guard.json\` and \`guard.html\`
  under the chosen output directory.

The script **refuses to overwrite an existing output directory**; choose
\`reports/first-demo-2\` for another run. Keep local captures private:
real-world captures can contain raw user questions and document identifiers.

## What does the demo prove?

It demonstrates the software's evaluation *workflow*: observed retrieval,
capture, comparison, and release decision. This is not a production system,
a comparison with competitors, an independent adoption result, or a claim
that all important queries have been identified correctly.

For a real data example, use
[BEIR SciFact reproduction](BENCHMARK_SCIFACT.md): 5,183 documents,
300 judged queries, with external dataset/license and checksum verification.
Verified results at NDCG@10 are 0.6329 for TF-IDF and 0.6605 for BM25 on
this **one** dataset; the improvement does not mean every query improves.
A separate [Capture & Replay SciFact example](CAPTURE_REPLAY.md) records and
re-evaluates these real rankings.

## Want to try it with your own RAG pipeline?

See the [bring-your-own-retriever guide](OWN_RAG_QUICKSTART.md).
Existing LangChain, LlamaIndex and custom retriever adapters are supported
subject to stable IDs and version-specific compatibility. Our independent
setup and usability evidence is still limited.

To help improve the tool, please follow the
[independent test invitation](COMMUNITY_OUTREACH.md#independent-reproduction-request)
and leave **real** feedback in
[GitHub issue #4](https://github.com/ilker-Akbal/openrag-bench/issues/4).
Provide the exact commit and environment, and a **synthetic or redacted**
reproduction only. Never upload private corpora, user prompts or API keys.
