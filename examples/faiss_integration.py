"""Run: pip install numpy faiss-cpu && python examples/faiss_integration.py

Self-contained FAISS plumbing example using explicitly constructed vectors.
These tiny synthetic vectors are not a semantic embedding benchmark.
"""
import faiss
import numpy as np

from openrag_bench.adapters import run_retriever
from openrag_bench.integrations.faiss import FaissRetriever

documents = ["intro", "vectors", "grounding"]
vectors = np.array([[1.0, 0.0, 0.0],
                    [0.0, 1.0, 0.0],
                    [0.0, 0.0, 1.0]], dtype="float32")

index = faiss.IndexFlatIP(vectors.shape[1])
index.add(vectors)
query_vectors = {
    "vector search": [0.0, 1.0, 0.0],
    "grounding": [0.0, 0.0, 1.0],
}
retriever = FaissRetriever(index, documents, lambda question: query_vectors[question])
report = run_retriever(
    retriever,
    [{"question": "vector search", "relevant_ids": ["vectors"]},
     {"question": "grounding", "relevant_ids": ["grounding"]}],
    k=2,
)
print(report["metrics"])
