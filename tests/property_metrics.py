"""Hypothesis invariant tests, run in isolated optional quality CI.

Default 4-version CI remains stdlib-only; this file is intentionally named
property_metrics.py and requires the optional dev extra to run.
"""
import unittest

from hypothesis import given, settings, strategies as st
from openrag_bench.metrics import (
    average_precision_at_k, graded_ndcg_at_k, hit_at_k,
    ndcg_at_k, precision_at_k, recall_at_k, reciprocal_rank,
)
from openrag_bench.comparison import compare_rows


IDS = ("a", "b", "c", "d", "e", "f")
rankings = st.lists(st.sampled_from(IDS), min_size=0, max_size=6, unique=True)
labels = st.lists(st.sampled_from(IDS), min_size=0, max_size=6, unique=True)
cutoffs = st.integers(min_value=1, max_value=9)
quality = settings(max_examples=90, deadline=None, derandomize=True)


class MetricInvariants(unittest.TestCase):
    @quality
    @given(retrieved=rankings, relevant=labels, k=cutoffs)
    def test_all_metrics_are_bounded_and_label_order_independent(
        self, retrieved, relevant, k
    ):
        grades = {item: 2 for item in relevant}
        baseline = (
            precision_at_k(retrieved, relevant, k),
            recall_at_k(retrieved, relevant, k),
            hit_at_k(retrieved, relevant, k),
            reciprocal_rank(retrieved, relevant, k),
            ndcg_at_k(retrieved, relevant, k),
            average_precision_at_k(retrieved, relevant, k),
            graded_ndcg_at_k(retrieved, grades, k),
        )
        swapped = list(reversed(relevant))
        comparable = (
            precision_at_k(retrieved, swapped, k),
            recall_at_k(retrieved, swapped, k),
            hit_at_k(retrieved, swapped, k),
            reciprocal_rank(retrieved, swapped, k),
            ndcg_at_k(retrieved, swapped, k),
            average_precision_at_k(retrieved, swapped, k),
            graded_ndcg_at_k(retrieved, {item: 2 for item in swapped}, k),
        )
        for actual, reordered in zip(baseline, comparable):
            self.assertGreaterEqual(actual, 0)
            self.assertLessEqual(actual, 1 + 1e-12)
            self.assertAlmostEqual(actual, reordered, places=12)
        self.assertEqual(
            baseline[-1],
            ndcg_at_k(retrieved, relevant, k),
            "Identical positive grades should give binary-equivalent NDCG",
        )

    @quality
    @given(retrieved=rankings, relevant=labels, k=cutoffs)
    def test_recall_hit_and_reciprocal_rank_do_not_decrease_with_k(
        self, retrieved, relevant, k
    ):
        self.assertLessEqual(
            recall_at_k(retrieved, relevant, k),
            recall_at_k(retrieved, relevant, k + 1),
        )
        self.assertLessEqual(
            hit_at_k(retrieved, relevant, k),
            hit_at_k(retrieved, relevant, k + 1),
        )
        self.assertLessEqual(
            reciprocal_rank(retrieved, relevant, k),
            reciprocal_rank(retrieved, relevant, k + 1),
        )

    @settings(max_examples=35, deadline=None, derandomize=True)
    @given(
        first=rankings,
        second=rankings,
        positives=st.lists(st.sampled_from(IDS), min_size=1, max_size=6, unique=True),
    )
    def test_swapping_paired_runs_negates_macro_deltas(self, first, second, positives):
        a = [{"query_id": "q1", "retrieved_ids": first, "relevant_ids": positives}]
        b = [{"query_id": "q1", "retrieved_ids": second, "relevant_ids": positives}]
        ab = compare_rows(a, b, 3)
        ba = compare_rows(b, a, 3)
        for metric, value in ab["delta"].items():
            self.assertAlmostEqual(value, -ba["delta"][metric], places=12)


if __name__ == "__main__":
    unittest.main()
