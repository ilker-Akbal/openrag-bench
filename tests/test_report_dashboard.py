"""Accessible, offline, privacy-aware Guard report dashboard regression tests."""
import unittest
from html.parser import HTMLParser

from openrag_bench.cli import evaluate
from openrag_bench.commands import _sample_files
from openrag_bench.comparison import compare_rows
from openrag_bench.guard import guard_comparison
from openrag_bench.html_report import render_html


class _DocumentAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.script_count = 0
        self.remote = []
        self.images = []
        self.link_targets = []
        self.external_styles = []
        self.details_count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "script":
            self.script_count += 1
            if "src" in attrs:
                self.remote.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "stylesheet":
            self.external_styles.append(attrs.get("href"))
        if tag == "img":
            self.images.append(attrs.get("src"))
        if tag == "details":
            self.details_count += 1
        if tag == "a":
            self.link_targets.append(attrs.get("href"))


class GuardDashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        samples = _sample_files()
        cls.blocked = guard_comparison(
            samples["candidate-regression.json"], samples["baseline.json"],
            samples["guard-policy.json"], k=1)
        cls.passed = guard_comparison(
            samples["candidate.json"], samples["baseline.json"],
            samples["guard-policy.json"], k=1)

    def test_critical_regression_explained_above_coverage(self):
        html = render_html(self.blocked)
        self.assertIn("Release blocked", html)
        self.assertIn("a critical query lost its relevant top-1 hit", html)
        self.assertIn("Overall retrieval quality improved", html)
        self.assertLess(html.index("Release blocked"), html.index("No positive labels"))
        self.assertLess(html.index("What needs attention?"), html.index("Quality checks"))
        self.assertLess(html.index("Query diagnostics"), html.index("Detailed retrieval metrics"))
        self.assertIn("Baseline NDCG@k", html)
        self.assertIn("Candidate NDCG@k", html)
        self.assertIn("0.3333", html)
        self.assertIn("0.6667", html)
        self.assertIn("+0.3333", html)
        self.assertIn("1 / 2", html)

    def test_failing_query_has_rank_comparison_and_focus_filter(self):
        html = render_html(self.blocked)
        self.assertIn("Relevant top-k hit lost", html)
        self.assertIn("Baseline first relevant", html)
        self.assertIn("Candidate first relevant", html)
        self.assertIn("Not retrieved", html)
        self.assertIn("Failed Guard queries", html)
        self.assertIn('data-guard-focus="true"', html)
        self.assertIn("First relevant rank · baseline → candidate", html)
        self.assertIn("Lost top-k hit", html)
        self.assertIn('id="query-diagnostics"', html)
        self.assertIn('href="#query-diagnostics"', html)
        self.assertLess(html.index("critical-privacy</h3>"), html.index(">q-pricing</th>"))

    def test_passing_report_has_no_failure_cards_and_keeps_queries(self):
        html = render_html(self.passed)
        self.assertIn("Quality checks passed", html)
        self.assertIn("PASSED", html)
        self.assertNotIn("What needs attention?", html)
        self.assertIn("Query diagnostics", html)
        self.assertIn("Show precise rule values and thresholds", html)
        self.assertIn('class="card metrics-panel"', html)
        self.assertIn('id="metric-select"', html)

    def test_non_guard_report_still_has_old_cli_explorer_contract(self):
        candidate = [
            {"query_id": "worse", "retrieved_ids": ["other"], "relevant_ids": ["a"]},
            {"query_id": "better", "retrieved_ids": ["a"], "relevant_ids": ["a"]},
        ]
        baseline = [
            {"query_id": "worse", "retrieved_ids": ["a"], "relevant_ids": ["a"]},
            {"query_id": "better", "retrieved_ids": ["other"], "relevant_ids": ["a"]},
        ]
        html = render_html(compare_rows(candidate, baseline, k=1))
        self.assertIn("Paired retrieval comparison", html)
        self.assertIn("Top-k overlap", html)
        self.assertIn("Worst first", html)
        self.assertNotIn("Release blocked", html)
        self.assertLess(html.index(">worse</th>"), html.index(">better</th>"))
        single = render_html(evaluate(candidate, 1))
        self.assertIn("Aggregate metrics", single)
        self.assertIn("No hit", single)
        self.assertIn('id="query-search"', single)

    def test_no_external_assets_and_sensible_responsive_semantics(self):
        html = render_html(self.blocked)
        doc = _DocumentAudit()
        doc.feed(html)
        self.assertEqual(doc.script_count, 1)
        self.assertEqual(doc.remote, [])
        self.assertEqual(doc.external_styles, [])
        self.assertEqual(doc.images, [])
        self.assertGreaterEqual(doc.details_count, 2)
        self.assertEqual(doc.link_targets, ["#query-diagnostics"])
        self.assertIn("@media(max-width:630px)", html)
        self.assertIn("prefers-reduced-motion", html)
        self.assertIn('aria-label="Reasons for blocking"', html)
        self.assertIn('type="search"', html)
        self.assertNotIn("sensitive-customer-document", html)

    def test_untrusted_query_and_rule_names_html_escaped(self):
        samples = _sample_files()
        bad = '</script><img src=x onerror=alert(1)><a href=https://host.example>'
        for key in ("baseline.json", "candidate-regression.json"):
            samples[key][0]["query_id"] = bad
        policy = samples["guard-policy.json"]
        policy["rules"][1]["id"] = bad
        report = guard_comparison(
            samples["candidate-regression.json"], samples["baseline.json"],
            policy, k=1)
        html = render_html(report)
        self.assertNotIn(bad, html)
        self.assertIn("&lt;/script&gt;", html)
        self.assertIn("&lt;img", html)
        doc = _DocumentAudit()
        doc.feed(html)
        self.assertEqual(doc.images, [])
        self.assertEqual(doc.link_targets, ["#query-diagnostics"])
        self.assertEqual(doc.script_count, 1)
        self.assertNotIn("How do I delete my account data?", html)
        self.assertNotIn("privacy-guide", html)
        self.assertNotIn("setup-guide", html)

    def test_policy_error_names_are_human_readable_not_removed(self):
        html = render_html(self.blocked)
        self.assertIn("A query failed its minimum score", html)
        self.assertIn("Too many queries got worse", html)
        self.assertIn("Average quality below minimum", html)
        self.assertIn("min_query_score", html)
        self.assertIn("max_regressed_queries", html)


if __name__ == "__main__":
    unittest.main()
