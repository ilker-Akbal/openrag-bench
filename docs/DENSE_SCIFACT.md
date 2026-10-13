# Optional SciFact dense embedding + FAISS tutorial

This tutorial extends the **real, verified** lexical benchmark in
[BENCHMARK_SCIFACT.md](BENCHMARK_SCIFACT.md) with a CPU-capable exact dense
embedding search. A user can now compare two *actual retriever families*
over the same 5,183 scientific documents and 300 judged queries.

**Status: FULL REAL-DATA RUN VERIFIED ON 13 OCTOBER 2026.**
The full 5,183-document, 300-test-query SciFact experiment completed on
GitHub Actions using the pinned MiniLM model (CPU) and exact FAISS indexing,
then was independently re-scored from the produced standard TREC files.

| Macro metric @ 10 | BM25 | MiniLM + FAISS |
| --- | ---: | ---: |
| Precision | 0.0870 | **0.0883** |
| Recall | **0.7876** | 0.7833 |
| Hit | **0.8067** | 0.7933 |
| MRR | **0.6270** | 0.6047 |
| NDCG | **0.6605** | 0.6451 |

- [Full passing real model run](https://github.com/ilker-Akbal/openrag-bench/actions/runs/38441972953)
- [Aggregate results and provenance](../benchmarks/scifact_dense_2026-10-13.json)
- Git SHA `a97846610b10723258d9b7e2eb618183c9d81020`
- Python 3.11, sentence-transformers 6.1.0, faiss-cpu 1.15.1, numpy 2.4.6
- Model revision `c21050a7ef692090620a6d037dd736908f9c7cf6`

**Interpretation:** BM25 achieved higher NDCG@10 and MRR@10, while the dense
model slightly exceeded BM25's Precision@10 on this specific run. Neither
method establishes general superiority, model answer factuality, or
statistical significance. Incomplete relevance labels limit interpretation.

## Dependencies and provenance

- SciFact: external archive, BEIR checksum verified; dataset not redistributed
- Embedding model: [sentence-transformers/all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)
- Model revision: `c21050a7ef692090620a6d037dd736908f9c7cf6`
- Model card license: Apache 2.0; weights downloaded on first run
- Optional packages: `sentence-transformers`, `torch`, `numpy`, `faiss-cpu`
- Similarity: cosine (L2 normalized embeddings + `faiss.IndexFlatIP`)
- Rank results: exact top-k nearest neighbors using FAISS
- Default device: CPU; explicit `--device cuda` possible with compatible local setup
- Data: publicly hosted BEIR SciFact corpus and test labels, not copied into repo

## Reproduce

```bash
python -m pip install -e '.[dense]'
python examples/scifact_dense_faiss.py --download \
    --archive data/scifact.zip --k 10 \
    --device cpu --batch-size 32 --output-dir reports/scifact-dense
```

This will download and use a pretrained embedding model (~90 MB of
weights plus dependencies), so allow significant local disk and memory.
No paid API keys are required. Do not upload the downloaded weights,
training materials or datasets into this project.

## Comparison

`bm25.run` and `dense.run` are generated from the same scored qrels.
`comparison.json` contains metrics and per-query details for each system,
and the embedding revision and archive checksum.

The model performs dense retrieval; it does **not** generate an answer or
measure hallucinations, factuality, latency or safety.

## Reproduction honesty

The verified GitHub Actions run above completed all model/relevance checks
and published *aggregate-only* numbers. Reproductions should record the
same model revision, Python/package versions, archive hash and hardware, and
should never upload third-party data. No statistical significance or
cross-domain superiority is claimed.

The separate optional dependencies and external model weights are **not**
subject to this repository's MIT license.
