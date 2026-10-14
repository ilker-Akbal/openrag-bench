"""OpenRAG Guard policy, onboarding and diagnostic security regression suite."""
import contextlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from openrag_bench.cli import main
from openrag_bench.commands import _sample_files
from openrag_bench.guard import guard_comparison, validate_policy


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name)
        self.samples = _sample_files()

    def command(self, args):
        with contextlib.redirect_stdout(StringIO()):
            return main(args)

    def save(self, name, value):
        path = self.folder / name
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
        return path

    def test_critical_regression_blocks_despite_positive_overall_score(self):
        candidate = self.samples["candidate-regression.json"]
        baseline = self.samples["baseline.json"]
        report = guard_comparison(candidate, baseline, self.samples["guard-policy.json"], 1)
        self.assertGreater(report["delta"]["ndcg_at_k"], 0)
        self.assertFalse(report["guard"]["passed"])
        self.assertTrue(report["guard"]["rules"][0]["passed"])
        self.assertEqual(report["guard"]["failed_rules"],
                         ["critical-coverage", "privacy-category"])
        critical = next(x for x in report["per_query_delta"]
                        if x["query_id"] == "critical-privacy")
        self.assertTrue(critical["diagnostics"]["lost_top_k_hit"])
        self.assertEqual(critical["diagnostics"]["baseline_first_relevant_rank"], 1)
        self.assertIsNone(critical["diagnostics"]["candidate_first_relevant_rank"])
        self.assertFalse(critical["diagnostics"]["gained_top_k_hit"])
        self.assertNotIn("question", str(report))
        self.assertNotIn("How do I delete", str(report))
        self.assertNotIn("privacy-guide", str(report))

    def test_healthy_candidate_passes(self):
        report = guard_comparison(self.samples["candidate.json"],
                                  self.samples["baseline.json"],
                                  self.samples["guard-policy.json"], 1)
        self.assertTrue(report["guard"]["passed"])
        self.assertEqual(report["guard"]["failed_rules"], [])
        self.assertTrue(all(x["passed"] for x in report["guard"]["rules"]))

    def test_init_is_idempotent_safe_and_can_run_guard(self):
        output = self.folder / "sample"
        self.assertEqual(self.command(["init", "--directory", str(output)]), 0)
        self.assertEqual(len(list(output.glob("*.json"))), 4)
        original = (output / "baseline.json").read_bytes()
        with contextlib.redirect_stderr(StringIO()), self.assertRaises(SystemExit):
            self.command(["init", "--directory", str(output)])
        self.assertEqual((output / "baseline.json").read_bytes(), original)
        params = ["--baseline", str(output / "baseline.json"), "--policy",
                  str(output / "guard-policy.json"), "--k", "1"]
        safe = output / "candidate.json"
        unsafe = output / "candidate-regression.json"
        path = self.folder / "guard-result.json"
        self.assertEqual(self.command(["guard", str(safe), *params,
                                       "--output", str(path)]), 0)
        self.assertEqual(json.loads(path.read_text())["guard"]["passed"], True)
        self.assertEqual(self.command(["guard", str(unsafe), *params,
                                       "--output", str(path)]), 2)
        self.assertEqual(json.loads(path.read_text())["guard"]["passed"], False)

    def test_doctor_validates_alignment_and_warns_on_missing_labels(self):
        output = self.folder / "doctor"
        self.command(["init", "--directory", str(output)])
        p = ["doctor", str(output / "candidate.json"), "--baseline",
             str(output / "baseline.json"), "--policy",
             str(output / "guard-policy.json"), "--k", "1"]
        self.assertEqual(self.command(p), 0)
        empty_labels = self.samples["candidate.json"]
        empty_labels[1]["relevant_ids"] = []
        path = self.save("empty.json", empty_labels)
        result = self.folder / "doctor.json"
        self.assertEqual(self.command(["doctor", str(path),
                                       "--output", str(result)]), 0)
        note = json.loads(result.read_text())
        self.assertEqual(note["positive_label_coverage"], 2)
        self.assertEqual(note["no_positive_label_ids"], ["q-setup"])
        self.assertTrue(note["warnings"])
        self.assertEqual(self.command(["doctor", str(path),
                                       "--baseline", str(output / "baseline.json"),
                                       "--output", str(result)]), 2)
        self.assertFalse(json.loads(result.read_text())["passed"])

    def test_mismatched_critical_and_categories_fail_closed(self):
        for key, value in [("critical", False), ("category", "other")]:
            candidate = [dict(row) for row in self.samples["candidate.json"]]
            candidate[0][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "differs"):
                guard_comparison(candidate, self.samples["baseline.json"],
                                 self.samples["guard-policy.json"], 1)

    def test_unknown_and_empty_selectors_rejected(self):
        policy = {"version": 1, "rules": [{
            "id": "missing", "select": {"type": "query_ids", "ids": ["absent"]},
            "metric": "hit_at_k", "min_score": 1,
        }]}
        with self.assertRaisesRegex(ValueError, "query IDs are missing"):
            guard_comparison(self.samples["candidate.json"],
                             self.samples["baseline.json"], policy, 1)
        policy["rules"][0]["select"] = {"type": "category", "value": "absent"}
        with self.assertRaisesRegex(ValueError, "selector matched no queries"):
            guard_comparison(self.samples["candidate.json"],
                             self.samples["baseline.json"], policy, 1)
        policy["rules"][0]["select"] = {"type": "critical"}
        candidate = [{**row, "critical": False}
                     for row in self.samples["candidate.json"]]
        baseline = [{**row, "critical": False}
                    for row in self.samples["baseline.json"]]
        with self.assertRaisesRegex(ValueError, "selector matched no queries"):
            guard_comparison(candidate, baseline, policy, 1)

    def test_policy_schema_rejects_nonfinite_unknown_and_boolean_values(self):
        policy = self.samples["guard-policy.json"]
        for value in (float("nan"), float("inf"), True, "0", None):
            changed = json.loads(json.dumps(policy))
            changed["rules"][0]["min_delta"] = value
            with self.subTest(value=str(value)), self.assertRaises(ValueError):
                validate_policy(changed)
        changed = json.loads(json.dumps(policy))
        changed["rules"][0]["unknown_action"] = "skip"
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            validate_policy(changed)
        changed = json.loads(json.dumps(policy))
        changed["rules"][0]["id"] = changed["rules"][1]["id"]
        with self.assertRaisesRegex(ValueError, "unique"):
            validate_policy(changed)

    def test_query_min_score_and_allowed_regressions(self):
        policy = {"version": 1, "rules": [{
            "id": "all-zero-failures", "select": {"type": "all"},
            "metric": "hit_at_k", "min_query_score": 1,
            "max_regressed_queries": 0,
        }]}
        report = guard_comparison(self.samples["candidate-regression.json"],
                                  self.samples["baseline.json"], policy, 1)
        item = report["guard"]["rules"][0]
        self.assertEqual(item["regressed_count"], 1)
        self.assertEqual(item["below_min_query_score_count"], 1)
        self.assertEqual(item["regressed_query_ids"], ["critical-privacy"])
        self.assertEqual(item["failed_thresholds"],
                         ["max_regressed_queries", "min_query_score"])

    def test_guard_html_contains_no_unescaped_policy_script(self):
        sample = self.folder / "candidate.json"
        baseline = self.folder / "baseline.json"
        policy = self.folder / "policy.json"
        html_path = self.folder / "guard.html"
        sample.write_text(json.dumps(self.samples["candidate.json"]))
        baseline.write_text(json.dumps(self.samples["baseline.json"]))
        inj = "</script><img src=x onerror=alert(1)>"
        custom = {"version": 1, "rules": [{
            "id": inj, "select": {"type": "all"},
            "metric": "ndcg_at_k", "min_delta": 0,
        }]}
        policy.write_text(json.dumps(custom))
        self.assertEqual(self.command(["guard", str(sample), "--baseline",
                                       str(baseline), "--policy", str(policy),
                                       "--k", "1", "--html", str(html_path)]), 0)
        content = html_path.read_text()
        self.assertIn("&lt;/script&gt;", content)
        self.assertNotIn(inj, content)


if __name__ == "__main__":
    unittest.main()
