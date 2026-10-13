# LangChain and LlamaIndex — optional retriever adapters

OpenRAG Bench can evaluate **existing** LangChain and LlamaIndex retrievers
without depending on either framework at installation time. Only ranked
stable document IDs are passed into the same offline evaluation metrics.

The adapters have dependency-free mock-based contract tests. A separate
optional GitHub Actions suite now installs real, pinned LangChain and
LlamaIndex framework packages and builds actual in-memory vector indices,
using original synthetic vectors. **The live suite must pass before any
specific framework-version compatibility is claimed**. It does not prove
semantic embedding quality or compatibility with every framework release.

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
- The default Python 3.10–3.13 CI uses offline mock-based contract tests
- Optional CI uses real `langchain-core==1.6.5` and `llama-index-core==0.14.25`
  on Python 3.11, installed independently in separate GitHub Actions jobs
- Live full framework compatibility must be checked from the dedicated workflow;
  neither model quality nor cross-version certification is implied
- Independent external-user reproduction remains an open community task


## Actual vector-store compatibility smoke tests (no APIs, no downloads of weights)

The [real-framework integration workflow](../.github/workflows/framework-real-integration.yml)
runs two isolated optional Python 3.11 jobs. LangChain uses the real
InMemoryVectorStore; LlamaIndex uses the real VectorStoreIndex and TextNode.
Both use the same original, three-document synthetic mini-corpus and a
locally computed 3D keyword embedding. The benchmark asks three unambiguous
queries and checks top-1 document IDs and all reported OpenRAG Bench metrics.
This exercises *real library indexing and retrieval*, not mock return values.

**Reproduce the LangChain job** in a separate virtual environment:

~~~bash
python -m pip install -e .
python -m pip install "langchain-core==1.6.5" "numpy>=1.23,<3"
python examples/framework_real_integration.py --framework langchain
~~~

**Reproduce the LlamaIndex job** in a different virtual environment:

~~~bash
python -m pip install -e .
python -m pip install "llama-index-core==0.14.25"
python examples/framework_real_integration.py --framework llamaindex
~~~

For the dedicated optional unittest, set environment variable
OPENRAG_REAL_FRAMEWORK to langchain or llamaindex, then run:

~~~bash
python -m unittest discover -s tests -p framework_real_integration.py -v
~~~

On PowerShell use $env:OPENRAG_REAL_FRAMEWORK='llamaindex' (or 'langchain').
The workflow does this automatically and records installed version, Python
version, original corpus checksum, top-1 IDs and aggregates. This tiny
synthetic test proves API compatibility only; it cannot replace a real
labeled multilingual or large-scale retrieval benchmark. Nothing is uploaded
except synthetic numeric result metadata.
