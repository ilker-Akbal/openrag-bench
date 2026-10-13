"""Example integration: python examples/custom_retriever.py"""
from openrag_bench.adapters import run_retriever

class KeywordRetriever:
    def __init__(self):
        self.documents = {"doc-1": "Retrieval finds relevant passages",
                          "doc-2": "Grounding connects answers to evidence"}
    def retrieve(self, query, k):
        tokens = set(query.lower().split())
        ranked = sorted(self.documents, key=lambda doc: len(tokens & set(self.documents[doc].lower().split())), reverse=True)
        return ranked[:k]

if __name__ == "__main__":
    questions = [{"question": "Retrieval passages", "relevant_ids": ["doc-1"]},
                 {"question": "Grounding evidence", "relevant_ids": ["doc-2"]}]
    print(run_retriever(KeywordRetriever(), questions, k=2))
