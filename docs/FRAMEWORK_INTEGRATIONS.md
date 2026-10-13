# LangChain and LlamaIndex — optional retriever adapters

OpenRAG Bench can evaluate **existing** LangChain and LlamaIndex retrievers
without depending on either framework at installation time. Only ranked
stable document IDs are passed into the same offline evaluation metrics.

These adapters are **thin interoperability wrappers** tested with offline
framework-shaped mocks. A real user's framework version, vector index and
ground-truth labels may require additional integration verification. We do
not claim a live third-party framework benchmark result based on these mocks.

## LangChain retriever

Construct your own LangChain retriever first, and make sure its returned
`Document` objects contain stable IDs in `metadata["doc_id"]`, or in
`Document.id` when available:

```python
from openrag_bench.adapters import run_retriever
from openrag_bench.integrations.frameworks import LangChainAdapter

# Configure and populate `your_vector_store` in your existing application:
# retriever = your_vector_store.as_retriever(search_kwargs={"k": 5})
adapter = LangChainAdapter(retriever, metadata_id_key="doc_id")
report = run_retriever(
    adapter,
    [{"query_id": "q-1", "question": "What is RAG?",
      "relevant_ids": ["your-stable-doc-id"]}],
    k=5,
)
print(report["metrics"]["ndcg_at_k"])
```

Use `allow_document_id=False` to require IDs in document metadata (to catch
missing metadata rather than silently falling back to framework-assigned IDs).
The adapter **does not change** the number of results configured in the
underlying LangChain retriever; it truncates excess ranked results to `k`.

## LlamaIndex retriever

LlamaIndex retrievers commonly return `NodeWithScore` wrappers. We obtain
the stable ID from `item.node.node_id` or `item.node.id_`:

```python
from openrag_bench.adapters import run_retriever
from openrag_bench.integrations.frameworks import LlamaIndexAdapter

# index: your existing populated LlamaIndex VectorStoreIndex
# retriever = index.as_retriever(similarity_top_k=5)
adapter = LlamaIndexAdapter(retriever)
report = run_retriever(
    adapter,
    [{"query_id": "q-1", "question": "What is RAG?",
      "relevant_ids": ["your-stable-node-id"]}],
    k=5,
)
print(report["metrics"]["recall_at_k"])
```

Both adapters reject missing, non-string or duplicate IDs. They preserve the
retriever's original ranking and take at most `k` results.

## Compare actual baselines

Generate candidate and baseline JSON/JSONL retrieval outputs with consistent
`query_id` values and ground-truth IDs, then:

```bash
openrag-bench candidate.jsonl --baseline baseline.jsonl \\
  --k 5 --min-delta 0 --csv results.csv --html report.html
```

**Data handling:** do not include confidential questions or source text in
public GitHub issues. The adapters do not automatically make any network
calls; configured third-party retrievers may have their own API behavior,
dependencies, pricing and data retention. Inspect those separately.

## Compatibility status

- Core OpenRAG Bench library: no dependency on either framework
- LangChain-style retriever API: `invoke(query)` returning documents
- LlamaIndex-style retriever API: `retrieve(query)` returning node wrappers
- Tested with offline shape-contract mocks, not every framework release
- Full end-to-end independently reproduced integrations are a future
  community milestone, not a claim made here
