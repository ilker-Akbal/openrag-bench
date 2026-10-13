# Turkish Wikipedia retrieval benchmark — real human-labeled questions

## Source and rights

Dataset: **Rızgar Ozan, Turkish RAG Eval**,
https://huggingface.co/datasets/RizgarOzan/turkish-rag-eval

Pinned immutable Hugging Face dataset Git revision:

~~~text
d166363bd8d906154b56fbb7009787f2a8591fbe
~~~

The original dataset's **health-domain, human-annotated subset** contains
54 Turkish Wikipedia articles and 58 Turkish queries labeled against answer
articles. The external data is CC BY-SA 4.0. The corpus is *not* part of
OpenRAG Bench's MIT code or its distribution; the runner downloads the
three original data files only when explicitly given --download.

Original files and schema:
- corpus.jsonl: _id, title, text, url
- queries.jsonl: _id, text, answer_span
- qrels/test.jsonl: query-id, corpus-id, score

The dataset also contains a distinct expanded 296-query collection including
LLM drafts. **This benchmark deliberately does not use** those drafts.
Use the root files (54 articles/58 independently human-annotated queries),
not full/ or passages/.

Citation:
Ozan (2026), *Turkish RAG Eval: a retrieval test set for Turkish Wikipedia*,
https://github.com/RizgarOzan/turkish-rag-eval.

## Reproduce

Python 3.10+, standard-library-only evaluation core:

~~~bash
python examples/turkish_real_benchmark.py --download --k 10 --output turkish_aggregate.json
~~~

This accesses the fixed revision through Hugging Face, computes SHA-256 for
each downloaded file, validates IDs and relevance judgments, then computes
two **separately executed BM25** rankings on the same articles, queries and
judgments. The only difference between the two runs is token normalization:

- **Unicode casefold baseline:** NFKC text normalization + casefold() and
  Unicode-alphanumeric word extraction.
- **Turkish casing candidate:** NFKC + I→ı and İ→i before lowercasing,
  preserving ı/i distinctions, then identical Unicode word extraction.

Both use Okapi BM25 with k1=1.2, b=0.75, deterministic doc-ID tie breaks
and same top-k; no model weights, API keys, LLMs or paid services.

The results include Precision/Recall/Hit/MRR/MAP/binary NDCG/graded-NDCG
at k, candidate-minus-baseline paired deltas and seeded descriptive
bootstrap intervals. Qrels are article-level, not passage-level. Aggregated
metrics are computed by OpenRAG Bench itself; no copied upstream benchmark
scores are presented as our own.

### Verified results

**Verified** by [real pinned data GitHub Actions run](https://github.com/ilker-Akbal/openrag-bench/actions/runs/38459555733) on Python 3.11/Linux. The run checked exactly **54 documents, 58 human-labeled queries and 58 qrels**, and retained only an aggregate-only JSON artifact:

| Lexical method | NDCG@10 |
| --- | ---: |
| Unicode casefold BM25 | **0.8544543634421565** |
| Turkish-specific casing BM25 | **0.8544543634421565** |
| Candidate minus baseline | **0.0000000000000000** |

In this specific article-level health dataset, the selected casing change
**made no difference to NDCG@10**. This is a useful negative result, not
evidence of model superiority. It does not mean the two tokenizations are
equivalent across Turkish domains, or that suffix-aware morphological
processing would have no value.

The test artifact contains original source file SHA-256 digests, aggregate
scores and paired descriptive intervals; licensed articles and questions
are excluded. For exact checksums, inspect the numeric-only artifact from
the linked workflow.

## Limitations

- One health-related Wikipedia domain, 58 human questions, one annotator:
  limited representativeness and no inter-annotator agreement statistic.
- Relevance is judged at article level; passages and answer-span fidelity
  are outside this experiment.
- Casing normalization is not Turkish stemming, semantic embeddings,
  multilingual generalization, hallucination assessment or QA quality.
- Some non-relevant documents are unjudged rather than guaranteed negatives.
- Bootstrap intervals describe the sampled paired queries; they do not
  establish universal superiority or a formal significance test.
- Exact data availability and license remain controlled by the source author.
- Public artifacts hold **only numeric aggregates and file checksums**, never
  article text, query questions or answer spans.
