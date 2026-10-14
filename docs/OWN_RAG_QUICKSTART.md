# Capture & Replay — first report with your own RAG retriever

OpenRAG Bench v0.6.0 evaluates **ranked retrieval**, not generated LLM answers.
This guide has two intentionally separate stages:

1. Reproduce a tiny **original synthetic** end-to-end demonstration without
   cloud, model weights or keys, so that you can see what a blocked release looks like.
2. Bind **your actual retriever** to human-reviewed Studio labels and run the
   same evaluation privately. No real-user adoption is claimed by step 1.

## A. A first offline report (no model, no API key)

Install from the GitHub repository and run from its root:

~~~powershell
git clone https://github.com/ilker-Akbal/openrag-bench.git
cd openrag-bench
python -m pip install -e .
python examples/quickstart_capture_replay.py --output-dir reports/quickstart
~~~

On Windows:

~~~powershell
Start-Process .\reports\quickstart\guard.html
~~~

The two deliberately tiny lexical retrievers use different original synthetic
document sets. Their results are computed from **token overlap with the query**,
not looked up from the golden judgments.

The baseline finds the critical privacy guide and misses ordinary questions.
The candidate finds two ordinary guides but loses the privacy guide.
Therefore **aggregate NDCG@1 increases and the Guard must BLOCK** the change,
with failed policy \`critical-privacy-hit\`.

\`reports/quickstart/\` contains the local synthetic golden data, observed
rankings, captured baseline/candidate JSON, SHA-256 manifests, policy and an
offline HTML report. The folder is gitignored. A second run with the same
output directory refuses to overwrite evidence; use a fresh directory.

**This verifies the integration contract, not real-world RAG quality.** A
passing test does not demonstrate user adoption, tool safety certification
or LLM factual accuracy.

## B. Move to your own retriever and real judgments

First create or import human-reviewed questions and document IDs in Studio:

~~~powershell
openrag-bench studio --output golden-dataset-studio.html
Start-Process .\golden-dataset-studio.html
~~~

Export **Golden Judgments** and the **Guard Policy**. Remember that Studio's
\`retrieved_ids: []\` means *not yet measured*, not failed retrieval.

Your application must expose a retriever whose
\`retrieve(question: str, k: int)\` method returns an ordered list of
**stable document IDs**, not passages or text and not the expected labels.
For example, in an application with real LangChain vector retrievers
already configured:

~~~python
import json
from pathlib import Path

from openrag_bench.capture import capture_from_retriever
from openrag_bench.integrations.frameworks import LangChainAdapter

golden = json.loads(Path("openrag-golden-judgments.json").read_text(encoding="utf-8"))
k = 5

# Replace both variables with EXISTING, configured LangChain retrievers.
# Their returned Documents must expose stable metadata["doc_id"] values.
# baseline_retriever = previous_vector_store.as_retriever(search_kwargs={"k": k})
# candidate_retriever = new_vector_store.as_retriever(search_kwargs={"k": k})

def save(path, retriever):
    rows = capture_from_retriever(
        LangChainAdapter(retriever, metadata_id_key="doc_id",
                         allow_document_id=False),
        golden,
        k,
    )
    # Exclusive-create avoids silently replacing a previous capture.
    with Path(path).open("x", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
        f.write("\n")

save("baseline.json", baseline_retriever)
save("candidate.json", candidate_retriever)
~~~

**The snippet above is an integration template**, not a standalone command:
\`baseline_retriever\` and \`candidate_retriever\` must be created from your
own configured application (or use a \`LlamaIndexAdapter\` or a custom object
implementing the same protocol). The module imports no cloud service by
itself, but **your retriever may make network calls**; audit its behavior.

For non-Python retrieval services that already export actual ranked IDs, use:

~~~powershell
openrag-bench capture openrag-golden-judgments.json --rankings baseline-observed.json --output baseline.json
openrag-bench capture openrag-golden-judgments.json --rankings candidate-observed.json --output candidate.json
~~~

Then check metadata/pairing before evaluating:

~~~powershell
openrag-bench doctor candidate.json --baseline baseline.json --policy openrag-guard-policy.json --k 5
openrag-bench replay candidate.json --baseline baseline.json --policy openrag-guard-policy.json --k 5 --html guard.html
~~~

The replay exits with **0** when policies pass, or **2** when release quality
is blocked. Missing/misaligned labels and invalid IDs fail closed; they do
not count as a legitimate "zero-hit result". The Guard's status also depends
on **your** policy thresholds.

## Stable ID and privacy checklist

- Map raw retrieval IDs to the *same canonical stable IDs* used in Studio.
  Use explicit \`id_map\` in \`capture_from_retriever\` or \`--id-map\` in
  the CLI if necessary; never silently assume chunk IDs remain stable after
  re-indexing.
- Preserve the **same question IDs, graded labels, category and critical
  metadata** across baseline and candidate. Do not infer ground truth from
  any candidate's retrieved result.
- Capture only on **authorized** sources. Private JSON captures include raw
  user questions and document IDs. Keep them out of issues, logs, releases,
  Git commits and third-party artifact storage.
- Verify your actual retriever's timeouts, dependencies and remote data
  handling yourself. OpenRAG Bench cannot guarantee arbitrary retriever
  determinism or private API behavior.
- Treat generated Guard policies as **editable starting points**, not
  universal acceptance thresholds. A global average can improve while
  individual queries regress.

See [Capture & Replay details](CAPTURE_REPLAY.md),
[LangChain/LlamaIndex adapters](FRAMEWORK_INTEGRATIONS.md), and
[request real-user feedback](GET_INVOLVED.md).

## What we still need

A new developer should try these instructions without maintainer coaching
and, voluntarily, report their platform, Python version, actual workflow,
elapsed time, and *redacted* friction notes. Until that happens, we make no
claim about a proven five-minute setup or external production adoption.
