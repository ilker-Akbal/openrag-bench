"""Five-minute local onboarding and non-mutating labeled-dataset diagnostics."""
import argparse
import json
from pathlib import Path

from .cli import _validate
from .comparison import compare_rows
from .guard import guard_comparison, validate_policy
from .io import read_rows


def _read_policy(path):
    try:
        return validate_policy(json.loads(Path(path).read_text(encoding="utf-8-sig")))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Policy {path}: invalid JSON line {exc.lineno}: {exc.msg}") from exc


def _sample_files():
    rows = [
        {"query_id": "critical-privacy", "question": "How do I delete my account data?",
         "category": "privacy", "critical": True, "relevant_ids": ["privacy-guide"],
         "retrieved_ids": ["privacy-guide"]},
        {"query_id": "q-setup", "question": "How do I install the application?",
         "category": "general", "critical": False, "relevant_ids": ["setup-guide"],
         "retrieved_ids": ["other"]},
        {"query_id": "q-pricing", "question": "How do I view subscription options?",
         "category": "general", "critical": False, "relevant_ids": ["pricing-guide"],
         "retrieved_ids": ["other"]},
    ]
    candidate = [{**row, "retrieved_ids": list(row["relevant_ids"])} for row in rows]
    regression = [
        {**row, "retrieved_ids": ["other"]} if row["critical"] else
        {**row, "retrieved_ids": list(row["relevant_ids"])}
        for row in rows
    ]
    policy = {"version": 1, "rules": [
        {"id": "overall-quality", "select": {"type": "all"},
         "metric": "ndcg_at_k", "min_delta": 0},
        {"id": "critical-coverage", "select": {"type": "critical"},
         "metric": "hit_at_k", "min_query_score": 1, "max_regressed_queries": 0},
        {"id": "privacy-category", "select": {"type": "category", "value": "privacy"},
         "metric": "recall_at_k", "min_score": 1},
    ]}
    return {
        "baseline.json": rows, "candidate.json": candidate,
        "candidate-regression.json": regression, "guard-policy.json": policy,
    }


def init(argv=None):
    parser = argparse.ArgumentParser(prog="openrag-bench init",
                                     description="Create safe original demo evaluation files")
    parser.add_argument("--directory", type=Path, default=Path("openrag-demo"))
    args = parser.parse_args(argv)
    try:
        directory = args.directory
        files = _sample_files()
        # Fail closed before writing anything: no partially overwritten fixtures.
        if directory.exists() and not directory.is_dir():
            raise ValueError(f"{directory}: existing path is not a directory")
        if any((directory / name).exists() for name in files):
            raise ValueError(f"{directory}: a demo file already exists; refusing to overwrite")
        directory.mkdir(parents=True, exist_ok=True)
        for name, data in files.items():
            (directory / name).write_text(json.dumps(data, ensure_ascii=False, indent=2)
                                          + "\n", encoding="utf-8")
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(f"Created {len(files)} synthetic demo files in {directory}")
    print(f"Try: openrag-bench guard {directory / 'candidate.json'} "
          f"--baseline {directory / 'baseline.json'} --policy "
          f"{directory / 'guard-policy.json'} --k 1")
    print("Replace candidate.json with candidate-regression.json to see a blocked release.")
    return 0


def doctor(argv=None):
    parser = argparse.ArgumentParser(prog="openrag-bench doctor",
                                     description="Check data and policy before comparison")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--policy", type=Path)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    if args.policy and not args.baseline:
        parser.error("--policy requires --baseline")
    try:
        candidate = read_rows(args.dataset)
        _validate(candidate, args.k)
        if len(candidate) != len({r.get("query_id") for r in candidate}):
            raise ValueError("Duplicate candidate query IDs")
        if args.baseline:
            baseline = read_rows(args.baseline)
            compare_rows(candidate, baseline, args.k)
            if args.policy:
                guard_comparison(candidate, baseline, _read_policy(args.policy), args.k)
        missing_labels = [r.get("query_id") or str(i)
                          for i, r in enumerate(candidate, 1) if not r["relevant_ids"]]
        report = {"passed": True, "query_count": len(candidate),
                  "positive_label_coverage": len(candidate) - len(missing_labels),
                  "no_positive_label_ids": missing_labels[:20],
                  "warnings": (["Some queries have no positive judgment; "
                                "they contribute zero relevance metrics."]
                               if missing_labels else []),
                  "paired_alignment_checked": bool(args.baseline),
                  "policy_validated": bool(args.policy)}
    except (ValueError, TypeError, KeyError, OSError) as exc:
        report = {"passed": False, "error": str(exc)}
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        try:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        except OSError as exc:
            parser.error(str(exc))
    print(rendered)
    return 0 if report["passed"] else 2


def guard(argv=None):
    parser = argparse.ArgumentParser(prog="openrag-bench guard",
                                     description="Enforce a multi-rule retrieval quality policy")
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--html", type=Path)
    args = parser.parse_args(argv)
    try:
        report = guard_comparison(read_rows(args.dataset), read_rows(args.baseline),
                                  _read_policy(args.policy), args.k)
        rendered = json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False)
        if args.output:
            args.output.write_text(rendered + "\n", encoding="utf-8")
        if args.html:
            from .html_report import render_html
            args.html.write_text(render_html(report), encoding="utf-8")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.error(str(exc))
    print(rendered)
    if not report["guard"]["passed"]:
        return 2
    return 0
