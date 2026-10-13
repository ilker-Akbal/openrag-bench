# OpenRAG Bench usage and metric definitions

## Installation

Python 3.10–3.13 are tested in CI. The evaluation core has no runtime
dependencies.

```bash
python -m pip install -e .
openrag-bench --help
python -m unittest discover -s tests -v
```

For the optional FAISS integration:

```bash
python -m pip install '.[faiss]'
python examples/faiss_integration.py
```

The FAISS example uses **synthetic, manually specified vectors**, not
semantic embeddings or a production benchmark. The adapter assumes
positional document IDs aligned to rows of the FAISS index; an `IndexIDMap`
with arbitrary custom IDs requires its own mapping.

## Input schema

A nonempty JSON array of objects:

```json
[
  {
    "query_id": "q-001",
    "question": "What is retrieval?",
    "retrieved_ids": ["doc-a", "doc-b"],
    "relevant_ids": ["doc-b"]
  }
]
```

`retrieved_ids` is a ranked list of unique nonempty string document IDs;
`relevant_ids` is a set-like list of unique nonempty string IDs that
represent manually labeled ground truth. Either can be empty.
`question` is optional display text.

`query_id` is optional for a single retriever, but **required and unique**
in both baseline and candidate datasets when comparing. The query ID sets
and each query's ground truth must match (row ordering can differ).

## Metrics and corner cases

| Metric | Meaning |
|---|---|
| Precision@k | Top-k relevant unique documents / k, even if fewer than k were returned |
| Recall@k | Top-k relevant documents / number of distinct relevant documents |
| Hit@k | 1 if any relevant result appears among top-k, else 0 |
| MRR@k | Reciprocal rank of first relevant document **within top-k**, macro-averaged |
| NDCG@k | Binary relevance, discounted by rank and normalized against ideal ordering |
| reciprocal_rank | Legacy untruncated reciprocal rank, not an at-k metric |

Empty ground-truth lists yield zero recall and NDCG.
Duplicate returned IDs are rejected for trustworthy evaluation.
All aggregate scores are unweighted **macro averages** over queries.

## Single-run evaluation

```bash
openrag-bench examples/retrieval_results.json --k 2 --output results.json --html results.html
```

## Paired regression testing

```bash
openrag-bench examples/comparison_candidate.json \
  --baseline examples/comparison_baseline.json \
  --k 2 --metric ndcg_at_k --min-delta 0 \
  --output comparison.json --html comparison.html
```

The signed delta is candidate minus baseline. The CI gate exits `2`
when the chosen delta is below `--min-delta` (after reports are emitted).
This is a deterministic engineering threshold, not a significance test.
Confidence intervals are computed from 1,000 seeded paired bootstrap samples,
and are descriptive; small or biased datasets undermine generalization.

## Standard TREC input

`--qrels FILE` enables evaluation of classic four-column qrels files
(`query_id iteration doc_id relevance`) and six-column run files
(`query_id Q0 doc_id rank score run_id`):

```bash
openrag-bench examples/trec_candidate.run --qrels examples/trec.qrels \
  --baseline examples/trec_baseline.run --k 2 --min-delta 0
```

Scores are sorted by the provided **rank**, not score. Every judged query is
evaluated, including queries omitted from a run. Positive integer grades are
treated as binary relevance. Unknown query IDs in a run and malformed or
repeated rank/document entries are errors.

## Existing retriever integration

```python
from openrag_bench.adapters import run_retriever

class MyRetriever:
    def retrieve(self, query: str, k: int):
        return ["doc-a", "doc-b"][:k]

report = run_retriever(
    MyRetriever(),
    [{"query_id": "q1", "question": "Example", "relevant_ids": ["doc-b"]}],
    2,
)
print(report["metrics"])
```

OpenRAG Bench measures retrieved **document relevance**. It does not directly
evaluate hallucination rates, answer factuality, grounding, latency or cost.
No cloud API, Ollama service or model downloads are required for the core.
