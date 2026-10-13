# Optional SciFact dense embedding + FAISS tutorial

This tutorial extends the **real, verified** lexical benchmark in
[BENCHMARK_SCIFACT.md](BENCHMARK_SCIFACT.md) with a CPU-capable exact dense
embedding search. A user can now compare two *actual retriever families*
over the same 5,183 scientific documents and 300 judged queries.

**Status:** code and offline mock tests are provided, but full model inference
over the real SciFact dataset has **not yet been run and verified** as part
of the project. Do not cite or invent any dense scores.

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

Before publicly reporting dense scores:
1. Run on the complete SciFact **test** split, not on the mock test corpus.
2. Record Git commit, model revision, package versions, OS/CPU/GPU and runtime.
3. Independently re-score both generated runs with the TREC CLI.
4. Only commit aggregate results, not third-party document text or query text.
5. Avoid significance and cross-domain superiority claims.

The separate optional dependencies and external model weights are **not**
subject to this repository's MIT license.
