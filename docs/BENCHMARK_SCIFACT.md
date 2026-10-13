# Reproducible BEIR SciFact retrieval benchmark

## Verified real-dataset result — 13 October 2026

The benchmark ran on **5,183 scientific abstracts and 300 judged test
queries**, and the generated TREC files were independently re-evaluated
using OpenRAG Bench. The two methods require no GPU or cloud API.

| Macro metric @ k=10 | TF-IDF cosine | BM25 (k1=1.2, b=0.75) |
| --- | ---: | ---: |
| Precision@10 | 0.0860 | **0.0870** |
| Recall@10 | 0.7785 | **0.7876** |
| Hit@10 | 0.8000 | **0.8067** |
| MRR@10 | 0.5940 | **0.6270** |
| NDCG@10 | 0.6329 | **0.6605** |

- **Verified run:** https://github.com/ilker-Akbal/openrag-bench/actions/runs/38440711430
- **Exact code commit:** `b9ccbfab1ddc1b0de0df01afba36f1bd9364a098`
- **Dataset SHA-256:** `536e14446a0ba56ed1398ab1055f39fe852686ecad24a6306c80c490fa8e0165`
- **Python:** 3.11 (GitHub Actions Ubuntu runner).
- **Machine-readable aggregate-only metrics:** [JSON](../benchmarks/scifact_2026-10-13.json)
- **Verification:** independent standard TREC run/qrels evaluation matched all metric
  values within `1e-9`; the workflow passed.

**Interpretation:** On this exact retrieval configuration and test collection,
BM25 achieved NDCG@10 0.6605 versus 0.6329 for TF-IDF (absolute difference
+0.0276). This is **not** evidence of statistical significance, BM25's
superiority on other datasets, or LLM answer quality. The relevance judgments
are incomplete; unlabeled documents are treated as nonrelevant. Only
aggregate results (no third-party texts) were added to the repository.

## Dataset sources and rights

- Original authors: David Wadden et al., *Fact or Fiction: Verifying
  Scientific Claims* (EMNLP 2020), Allen Institute for AI.
- Original SciFact project: https://github.com/allenai/scifact
- Original licensing details:
  https://github.com/allenai/scifact/blob/master/LICENSE.md
  - Scientific claims and evidence annotations: **CC BY 4.0**
  - Scientific abstracts from S2ORC: **ODC-By 1.0**
- BEIR benchmark: Nandan Thakur et al., *BEIR: A Heterogeneous Benchmark
  for Zero-shot Evaluation of Information Retrieval Models* (NeurIPS 2021).
- Official download archive:
  https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip
- BEIR dataset listing and published MD5 checksum:
  https://github.com/beir-cellar/beir/wiki/Datasets-available
- Published official BEIR SciFact ZIP MD5:
  `5f7d1de60b170fc8027bb7898e2efca1`

Certain third-party mirrors assign different license metadata to repackaged
datasets. The **upstream primary-source licensing statements** above should
be consulted. The original dataset license is **not** the license of this
repository's MIT-licensed code. Attribution must be retained; do not
redistribute upstream data without confirming the relevant license terms.

**No dataset contents are checked in.** The script downloads only when
explicitly passed `--download`; it verifies bytes against the published
MD5 and records SHA-256 for reproducibility. An HTTPS connection and
`urlopen` are used, and the archive is read in memory without extracting
potentially unsafe paths.

## Step-by-step reproduction

```bash
git clone https://github.com/ilker-Akbal/openrag-bench.git
cd openrag-bench
python -m pip install -e .
python -m unittest discover -s tests -v
python examples/scifact_benchmark.py --download --k 10 \
  --archive data/scifact.zip --output-dir reports/scifact
```

No GPU, model weights, FAISS, paid API or ChatGPT subscription is required.

The script builds a **lexical inverted index over title + abstract**;
queries are lowercased and tokenized with `[a-z0-9]+`. There is no
stop-word list or stemming.

- Baseline: **TF-IDF cosine**, smooth IDF
  `log((N+1)/(df+1))+1`, sublinear term frequency `1+log(tf)`.
- Candidate: **BM25**, `k1=1.2, b=0.75`, positive smoothed IDF.
- Documents ranked by decreasing score, with stable ID-based tie-breaking.
- Scores are calculated only for documents matching at least one query term.
  For queries without matching terms, the run emits **zero retrieved IDs**.
- Evaluation uses all queries in `qrels/test.tsv`, even when a run has no hit.
- A qrel grade greater than zero means relevant (binary judgment).
- Metrics: Precision@k, Recall@k, Hit@k, MRR@k, NDCG@k, plus untruncated
  reciprocal rank for compatibility.
- Unjudged documents are treated as nonrelevant; incomplete judgments
  limit interpretation. Scores are macro-averaged over judged queries.
- Paired-bootstrap uncertainty bounds (seed 42, 1,000 resamples) are
  **descriptive**, not evidence of statistical significance.

The methods are chosen as interpretable, CPU-only baselines. This is not
a claimed improvement over state-of-the-art neural retrievers.

## Output files (created locally, ignored by Git)

- `reports/scifact/tfidf.run` — standard 6-column ranked TREC run
- `reports/scifact/bm25.run` — standard 6-column ranked TREC run
- `reports/scifact/test.qrels` — 4-column judged positive labels
- `reports/scifact/comparison.json` — dataset MD5+SHA256, both metrics,
  per-query results, differences and paired-bootstrap bounds

Independently re-evaluate with:

```bash
openrag-bench reports/scifact/bm25.run --qrels reports/scifact/test.qrels \
  --baseline reports/scifact/tfidf.run --k 10 --output reports/scifact/trec_verified.json
```

The JSON report includes query texts and may disclose source content. Store it
privately when using non-public datasets; generated files are gitignored.

## Honest benchmark reporting checklist

The verified 2026-10-13 aggregate numbers are captured above, with the code
commit, environment and archive checksum. Record future runs with the same
provenance fields; do not confuse unit-test fixture scores with real SciFact
measurements.

A future follow-up will compare dense embeddings + FAISS against these lexical
baselines with separately pinned models and explicit compute requirements.
