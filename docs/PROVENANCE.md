# Source provenance and licensing boundary

This standalone repository contains only the independently developed
**OpenRAG Bench** retrieval evaluation toolkit, unit tests, synthetic input
fixtures and its own documentation.

The initial prototype was developed inside a separate personal workshop
practice repository. It was extracted **without importing that repository's
Git history or third-party educational materials**.

Excluded on purpose:
- ROKETSAN training exercises, notebooks and class notes
- Third-party PDFs, photos, datasets, video and model weights
- Secrets, cached embeddings and local FAISS indexes
- Any unspecified third-party code or external benchmark dataset

All files in this repository are presented as purpose-built project code and
documentation under MIT, not as a grant over other parties' works. Before
publishing formal binary distributions or accepting externally contributed
source, the maintainer should verify authorship, permissions and needed
attribution file by file. This is not a legal opinion.

Third-party dependencies such as FAISS and NumPy retain their own licenses.
Do not claim benchmark efficacy or adoption based on synthetic sample data.


## Optional real Turkish benchmark dataset

The new Turkish benchmark runtime refers to
[RizgarOzan/turkish-rag-eval](https://huggingface.co/datasets/RizgarOzan/turkish-rag-eval)
at revision d166363bd8d906154b56fbb7009787f2a8591fbe. The external
dataset credits Rızgar Ozan, uses Turkish Wikipedia article extracts
and human-authored query judgments under **CC BY-SA 4.0**.

Only metadata, observed file hashes and aggregate scores may be committed in
this repository. Actual articles, questions and answer spans remain external
and are never relicensed under OpenRAG Bench's MIT license. See
[docs/TURKISH_BENCHMARK.md](TURKISH_BENCHMARK.md).
