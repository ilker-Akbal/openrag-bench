# Reproducible BEIR SciFact retrieval benchmark

## Status

This is a **runnable real-dataset benchmark recipe**. It compares TF-IDF
cosine to BM25 using BEIR SciFact's official **test** split.

**Important:** No live benchmark scores are claimed in this repository until
someone runs the download, verifies the archive and commits the exact
reproduction manifest and results. CI tests use **synthetic miniature
fixtures** and do not download or evaluate real SciFact. This prevents
network-dependent tests and unsupported accuracy claims.

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

Before publishing metric numbers, record the tested Git commit, Python version,
SciFact archive SHA-256, number of queries and documents, k, exact commands,
hardware, methods, dataset limitations, output metrics and any deviations.
Never confuse the CI's synthetic fixture scores with genuine SciFact metrics.

A future follow-up will compare dense embeddings + FAISS against these lexical
baselines with separately pinned models and explicit compute requirements.
