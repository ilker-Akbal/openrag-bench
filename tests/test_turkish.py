"""Offline tests for the external, human-labeled Turkish retrieval benchmark."""
import json
from pathlib import Path
import tempfile
import unittest

from examples.turkish_real_benchmark import BM25, load_dataset, run_benchmark, tokenize


class TurkishTests(unittest.TestCase):
    def test_turkish_dotted_dotless_i(self):
        self.assertEqual(tokenize("IŞIK ışıK İZMİR izmir", "turkish_case"),
                         ["ışık", "ışık", "izmir", "izmir"])
        self.assertEqual(tokenize("Öğrenci, çiçek, ŞÜPHE! ı", "turkish_case"),
                         ["öğrenci", "çiçek", "şüphe", "ı"])
        self.assertNotEqual(tokenize("IŞIK", "unicode_casefold"),
                            tokenize("IŞIK", "turkish_case"))
        for method in ("wrong", "other"):
            with self.assertRaises(ValueError):
                tokenize("some text", method)

    def test_bm25_ranks_turkish_documents(self):
        docs = {"d1":"İzmir şehrinde bir üniversite bulunmaktadır.",
                "d2":"Iğdır şehrinde bahçe ve ağaç bulunmaktadır.",
                "d3":"Bir veri tabanında sorgular çalışır."}
        result = BM25(docs, "turkish_case").search("İzmir üniversitesi", 2)
        self.assertEqual(result[0], "d1")
        self.assertEqual(len(result), 2)
        self.assertEqual(BM25(docs, "turkish_case").search("UNSEEN TOKEN", 2),
                         ["d1", "d2"])

    def test_small_original_labeled_dataset_and_metric_parity(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root/"qrels").mkdir()
            (root/"corpus.jsonl").write_text("\n".join(json.dumps({
                "_id":doc_id,"title":title,"text":text
            },ensure_ascii=False) for doc_id,title,text in [
                ("doc1","İzmir","İzmir'de üniversite bulunur."),
                ("doc2","Iğdır","Iğdır'da dağ bulunur.")]),encoding="utf-8")
            (root/"queries.jsonl").write_text("\n".join(json.dumps({
                "_id":query,"text":question
            },ensure_ascii=False) for query,question in [
                ("q1","İzmir"),("q2","Iğdır")]),encoding="utf-8")
            (root/"qrels/test.jsonl").write_text("\n".join(json.dumps({
                "query-id":q,"corpus-id":d,"score":1
            }) for q,d in [("q1","doc1"),("q2","doc2")]),encoding="utf-8")
            docs,qs,qrels=load_dataset(root)
            result=run_benchmark(docs,qs,qrels,k=1)
            self.assertEqual(result["documents"],2)
            self.assertEqual(result["queries"],2)
            self.assertEqual(result["judgments"],2)
            self.assertAlmostEqual(result["candidate"]["metrics"]["ndcg_at_k"],1)

    def test_no_unknown_qrels_or_duplicate_labels(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"qrels").mkdir()
            (root/"corpus.jsonl").write_text(
                '{"_id":"d","title":"Türkçe","text":"Işık"}\n',encoding="utf-8")
            (root/"queries.jsonl").write_text(
                '{"_id":"q","text":"ışık"}\n',encoding="utf-8")
            qrels=root/"qrels/test.jsonl"
            qrels.write_text('{"query-id":"q","corpus-id":"missing","score":1}\n',
                             encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"unknown"):
                load_dataset(root)
            qrels.write_text(
                '{"query-id":"q","corpus-id":"d","score":1}\n'*2,encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Duplicate"):
                load_dataset(root)
            qrels.write_text(
                '{"query-id":"q","corpus-id":"d","score":0}\n',encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"positive"):
                load_dataset(root)


if __name__ == "__main__":
    unittest.main()
