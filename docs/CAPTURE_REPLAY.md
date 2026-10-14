# Capture & Replay — proposed v0.6 (development branch)

**Status:** under development; not part of the published v0.5.0 pre-release.
This is an offline capture-to-evaluation workflow, not an HTTP traffic recorder,
retrieval engine, LLM evaluator, or a claim of live end-to-end integration.

## From Golden Dataset Studio to real retrieval evidence

1. Export `openrag-golden-judgments.json` from Studio. Its `retrieved_ids`
   intentionally remain empty: these are human labels, not observations.
2. Run *your own retriever* separately, recording the ranked document IDs it
   actually returns for each labeled query. Preserve the exact `query_id`.
3. Prepare a JSON array (or JSONL file) of **observed rankings**:

~~~json
[
  {"query_id": "q-privacy", "retrieved_ids": ["raw-19", "raw-42"]},
  {"query_id": "q-install", "retrieved_ids": []}
]
~~~

An empty ranking is a legitimate observed no-hit result; a missing query is not.
The capture command cannot verify whether external rankings are truthful.
Do not synthesize ranked IDs from the golden answers.

4. If your retriever uses different IDs than Studio, create an *explicit*
   raw-to-canonical JSON mapping (no implicit fallback):

~~~json
{"raw-19": "privacy-guide", "raw-42": "unrelated-doc"}
~~~

Mappings must cover **every** returned ID. Distinct raw IDs cannot collapse
into the same canonical ID within one query's ranking.

5. Bind real rankings and human judgments into a deterministic, existing-format
   OpenRAG Bench input:

~~~powershell
openrag-bench capture openrag-golden-judgments.json --rankings baseline-rankings.json --id-map ids.json --output baseline.json --manifest baseline.manifest.json

openrag-bench capture openrag-golden-judgments.json --rankings candidate-rankings.json --id-map ids.json --output candidate.json --manifest candidate.manifest.json
~~~

The command rejects missing/extra/duplicate query IDs, malformed ranking rows,
duplicate documents, unknown ID mappings, nonempty golden rankings, invalid
metadata and unlabeled queries. It **never overwrites** an output file.

Captured rows preserve each Studio query's question, query ID, category,
critical flag, positive relevance labels and graded judgments. Rows are ordered
as they appeared in the golden dataset, regardless of ranking input order.

An optional `openrag-capture/v1` manifest stores deterministic SHA-256 hashes,
row counts and observed nonempty-result counts, without embedding question
content. **The captured JSON dataset itself contains the original question
text and ranked document IDs.** Protect these local files as private data.

## Capture directly from a synchronous Python retriever

~~~python
import json
from pathlib import Path
from openrag_bench.capture import capture_from_retriever

golden = json.loads(Path("openrag-golden-judgments.json").read_text(encoding="utf-8"))

class MyRetriever:
    def retrieve(self, question: str, k: int):
        # Replace with a real call to your own retrieval system.
        return ["privacy-guide"][:k]

rows = capture_from_retriever(MyRetriever(), golden, k=5)
Path("candidate.json").write_text(
    json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
~~~

`capture_from_retriever` calls the supplied retriever once per query, validates
the returned ranking (maximum `k` IDs), and does not evaluate the result.
The caller controls setup, credentials, execution, and any optional integration
adapters. There is no bundled LLM/API service or network requirement.

## Replay the captured comparison through the existing Guard

~~~powershell
openrag-bench replay candidate.json --baseline baseline.json --policy openrag-guard-policy.json --k 3 --html replay-report.html
~~~

Replay intentionally delegates to the **existing Guard engine**. It performs
the same paired label/ID checks and versioned quality-policy enforcement, with
the same exit status (0 accepted; 2 quality blocked). Raw query text is not
published in the Guard HTML report. No retriever is run during replay.

`capture` freezes evidence; `replay` recalculates evaluation on that evidence.
This separation enables offline deterministic comparison without claiming that
replay itself executes the original retrieval model.

## Reproduce Capture & Replay with a real external retriever

The repository contains a **real BEIR SciFact** path using the official,
checksummed 5,183-document/300-judged-query dataset. Both TF-IDF cosine and
BM25 are implemented lexical retrievers that rank corpus documents based on
actual query/doc terms, **not** copied golden labels. The same output is
independently scored through the existing TREC benchmark.

From the repository checkout, after installing the development branch:

~~~powershell
python examples/scifact_capture_replay.py --download --k 10 --output-dir reports/scifact-capture
~~~

To avoid network access use a previously verified \`data/scifact.zip\`
with \`--archive data/scifact.zip\` and **omit** \`--download\`.
When the archive checksum does not match the official BEIR publication,
the program refuses to run.

What happens:

1. Build human-supplied golden judgments from official SciFact test qrels,
   leaving \`retrieved_ids\` empty; no Studio critical flags are fabricated.
2. Run real TF-IDF and BM25 searches against the external corpus for all queries.
3. Feed actual ranked IDs to the new \`capture\` command (twice).
4. \`replay\` uses the existing Guard engine to check aggregate NDCG non-regression.
5. Independently compare the captured metrics with the original SciFact TREC
   benchmark results in GitHub Actions; the CI artifact includes **aggregate
   numbers only**.

Locally generated \`reports/scifact-capture/*.json\` include third-party
question texts, relevance labels and document IDs; the directory is gitignored
and **must not be committed or attached as a public workflow artifact**. The
console summary and uploaded CI summary contain only aggregate measurements,
dataset counts, and the archive SHA-256.

This is a real-data lexical retrieval integration. It is **not** evidence
of LangChain/LlamaIndex production adoption or of LLM answer quality. Human
Studio workflows with private source documents still require a user-owned
retriever and matching stable IDs.


## Reproducibility and boundaries

- Existing v0.5.0 evaluation JSON format and Guard policy v1 remain unchanged.
- Outputs contain no invented scores, ranking results, or model identifiers.
- Stable document IDs are a user-provided contract, not automatically inferred.
- Golden data must contain at least one human positive judgment per query.
- Python standard library only; no new mandatory packages.
- Hashes are for local reproducibility checks, not cryptographic attestations
  of who generated the source rankings.
- Manifest hashes do not replace a signature, dataset review, or source auditing.
- Keep original v0.5.0 release artifacts immutable.
