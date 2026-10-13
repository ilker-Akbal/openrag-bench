"""Query-level interactive diagnostic report regression and security tests."""
import json
import re
import unittest

from openrag_bench.cli import evaluate
from openrag_bench.comparison import compare_rows
from openrag_bench.html_report import _coverage, render_html


class ExplorerTests(unittest.TestCase):
    def test_per_query_diagnostic_counts(self):
        report = evaluate([
            {"query_id":"q1", "retrieved_ids":["x","a"],"relevant_ids":["a","b"]},
            {"query_id":"q2", "retrieved_ids":[], "relevant_ids":[]},
        ], k=2)
        self.assertEqual(report["per_query"][0]["diagnostics"],
                         {"retrieved_count":2,"judged_positive_count":2,"hits_at_k":1})
        self.assertEqual(_coverage(report["per_query"]),{
            "queries":2,"no_positive_labels":1,"empty_candidate_results":1,
            "queries_with_hit":1})
        html=render_html(report)
        self.assertIn("No positive labels",html)
        self.assertIn("Query diagnostics",html)
        self.assertIn("Filter query ID",html)
        self.assertIn("Worst first",html)
        self.assertIn("No hit",html)
        self.assertNotIn("https://",html)

    def test_paired_overlap_and_worst_first(self):
        candidate=[
            {"query_id":"worse","retrieved_ids":["x","z"],"relevant_ids":["a"]},
            {"query_id":"better","retrieved_ids":["a","x"],"relevant_ids":["a"]}]
        baseline=[
            {"query_id":"better","retrieved_ids":["z","x"],"relevant_ids":["a"]},
            {"query_id":"worse","retrieved_ids":["a","z"],"relevant_ids":["a"]}]
        report=compare_rows(candidate,baseline,2)
        by_id={row["query_id"]:row for row in report["per_query_delta"]}
        self.assertEqual(by_id["worse"]["diagnostics"]["top_k_overlap_count"],1)
        self.assertEqual(by_id["better"]["diagnostics"]["top_k_overlap_count"],1)
        html=render_html(report)
        self.assertLess(html.index(">worse</th>"),html.index(">better</th>"))
        self.assertIn("Regressed",html)
        self.assertIn("bootstrap intervals",html)
        self.assertNotIn("document IDs are not included in this HTML", "")

    def test_escaped_ids_and_no_raw_question_or_doc_ids(self):
        malicious='</script><img src=x onerror=alert(1)>'
        text='my secret prompt and password string'
        doc='sensitive-customer-document'
        report=evaluate([{"query_id":malicious,"question":text,
                         "retrieved_ids":[doc],"relevant_ids":[doc]}],1)
        html=render_html(report)
        self.assertIn("&lt;/script&gt;",html)
        self.assertNotIn(malicious,html)
        self.assertNotIn(text,html)
        self.assertNotIn(doc,html)
        self.assertNotIn("onerror=alert(1)>",html)
        self.assertIn("<script type=",html)
        self.assertNotIn("<script>",html)

    def test_metric_payloads_remain_escaped_attributes(self):
        report=compare_rows([{"query_id":'" data-attack="x', "retrieved_ids":["x"],"relevant_ids":["a"]}],
                            [{"query_id":'" data-attack="x', "retrieved_ids":["a"],"relevant_ids":["a"]}],1)
        report["gate"]={"metric":"map_at_k","passed":False}
        html=render_html(report)
        self.assertNotIn('data-attack="x',html)
        self.assertIn("&quot; data-attack=",html)
        self.assertIn('value="map_at_k" selected',html)
        self.assertIn("data-scores=",html)
        self.assertTrue(re.search(r"<th scope=\"row\">&quot; data-attack=",html))


if __name__=="__main__":
    unittest.main()
