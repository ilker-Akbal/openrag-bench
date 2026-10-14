"""Independent black-box QA probe for a Luna/Work handoff.

Uses only original synthetic data, Python standard library and the installed
OpenRAG Bench CLI. Generates local evidence under reports/ (gitignored).
This is NOT equivalent to genuine third-party adoption or browser usability QA.

Usage:
    python scripts/luna_qa_probe.py --output-dir reports/luna-qa-1
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


SECRET = "SYNTHETIC_PRIVATE_QUESTION_SENTINEL_7af9"
DOC_PRIVATE = "private-privacy-document-id"
RULES = {
    "version": 1,
    "rules": [
        {"id": "aggregate-nonregression", "select": {"type": "all"},
         "metric": "ndcg_at_k", "min_delta": 0},
        {"id": "critical-privacy", "select": {"type": "critical"},
         "metric": "hit_at_k", "min_query_score": 1, "max_regressed_queries": 0},
    ],
}
GOLDEN = [
    {"query_id": "q-private", "question": SECRET, "category": "privacy",
     "critical": True, "relevant_ids": [DOC_PRIVATE],
     "relevance_grades": {DOC_PRIVATE: 2}, "retrieved_ids": []},
    {"query_id": "q-setup", "question": "install application", "category": "support",
     "critical": False, "relevant_ids": ["setup-guide"],
     "relevance_grades": {"setup-guide": 2}, "retrieved_ids": []},
    {"query_id": "q-warranty", "question": "warranty duration", "category": "support",
     "critical": False, "relevant_ids": ["warranty-guide"],
     "relevance_grades": {"warranty-guide": 2}, "retrieved_ids": []},
]
BASELINE = [
    {"query_id": "q-private", "retrieved_ids": [DOC_PRIVATE]},
    {"query_id": "q-setup", "retrieved_ids": []},
    {"query_id": "q-warranty", "retrieved_ids": []},
]
CANDIDATE = [
    {"query_id": "q-private", "retrieved_ids": []},
    {"query_id": "q-setup", "retrieved_ids": ["setup-guide"]},
    {"query_id": "q-warranty", "retrieved_ids": ["warranty-guide"]},
]
SAFE = [
    {"query_id": "q-private", "retrieved_ids": [DOC_PRIVATE]},
    {"query_id": "q-setup", "retrieved_ids": ["setup-guide"]},
    {"query_id": "q-warranty", "retrieved_ids": ["warranty-guide"]},
]


def write_new(path, obj):
    with Path(path).open("x", encoding="utf-8") as target:
        json.dump(obj, target, indent=2, ensure_ascii=False, allow_nan=False)
        target.write("\n")


def invoke(*args):
    """Invoke the actual installed CLI in a new Python process, not internal functions."""
    command = [
        sys.executable, "-c",
        "from openrag_bench.cli import main; raise SystemExit(main())",
        *map(str, args),
    ]
    completed = subprocess.run(command, capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=60, check=False)
    return completed.returncode, completed.stdout, completed.stderr


def probe(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    for name, obj in (
        ("golden.json", GOLDEN),
        ("policy.json", RULES),
        ("baseline-observed.json", BASELINE),
        ("candidate-observed.json", CANDIDATE),
        ("safe-observed.json", SAFE),
    ):
        write_new(destination / name, obj)

    checks = []

    def check(label, ok, detail):
        checks.append({"check": label, "passed": bool(ok),
                       "detail": str(detail)[:240]})

    def capture_one(name):
        code, _, stderr = invoke(
            "capture", destination / "golden.json",
            "--rankings", destination / f"{name}-observed.json",
            "--output", destination / f"{name}.json",
            "--manifest", destination / f"{name}.manifest.json",
        )
        check(f"{name}_capture", code == 0, f"exit={code} {stderr.strip()}")
        return code

    capture_one("baseline")
    capture_one("candidate")
    capture_one("safe")

    code, _, stderr = invoke(
        "doctor", destination / "candidate.json",
        "--baseline", destination / "baseline.json",
        "--policy", destination / "policy.json", "--k", "1",
        "--output", destination / "doctor.json",
    )
    check("doctor_alignment", code == 0, f"exit={code} {stderr.strip()}")

    code, _, stderr = invoke(
        "replay", destination / "candidate.json",
        "--baseline", destination / "baseline.json",
        "--policy", destination / "policy.json", "--k", "1",
        "--output", destination / "blocked.json",
        "--html", destination / "blocked.html",
    )
    blocked = (json.loads((destination / "blocked.json").read_text(encoding="utf-8"))
               if (destination / "blocked.json").exists() else {})
    check("critical_block_despite_macro_gain",
          code == 2 and blocked.get("delta", {}).get("ndcg_at_k", 0) > 0
          and "critical-privacy" in blocked.get("guard", {}).get("failed_rules", []),
          f"exit={code} guard={blocked.get('guard', {}).get('passed')} {stderr.strip()}")

    code, _, stderr = invoke(
        "replay", destination / "safe.json",
        "--baseline", destination / "baseline.json",
        "--policy", destination / "policy.json", "--k", "1",
        "--output", destination / "passed.json",
        "--html", destination / "passed.html",
    )
    passed = (json.loads((destination / "passed.json").read_text(encoding="utf-8"))
              if (destination / "passed.json").exists() else {})
    check("safe_candidate_passes",
          code == 0 and passed.get("guard", {}).get("passed") is True,
          f"exit={code} {stderr.strip()}")

    for name in ("blocked", "passed"):
        html = (destination / f"{name}.html")
        body = html.read_text(encoding="utf-8") if html.is_file() else ""
        check(f"{name}_html_redaction",
              bool(body) and SECRET not in body and DOC_PRIVATE not in body,
              "HTML exists and omits original synthetic private question/doc ID")

    check("capture_manifest_redaction",
          all((destination / f"{name}.manifest.json").is_file()
              and SECRET not in (destination / f"{name}.manifest.json").read_text(encoding="utf-8")
              and DOC_PRIVATE not in (destination / f"{name}.manifest.json").read_text(encoding="utf-8")
              for name in ("baseline", "candidate", "safe")),
          "Hash manifests contain no raw private markers")

    write_new(destination / "missing-observed.json", BASELINE[:2])
    code, _, _ = invoke("capture", destination / "golden.json",
                        "--rankings", destination / "missing-observed.json",
                        "--output", destination / "missing-capture.json")
    check("missing_query_rejected",
          code == 2 and not (destination / "missing-capture.json").exists(),
          f"exit={code}, no output created")

    duplicate = [*BASELINE]
    duplicate[0] = {"query_id": "q-private", "retrieved_ids": [DOC_PRIVATE, DOC_PRIVATE]}
    write_new(destination / "duplicate-observed.json", duplicate)
    code, _, _ = invoke("capture", destination / "golden.json",
                        "--rankings", destination / "duplicate-observed.json",
                        "--output", destination / "duplicate-capture.json")
    check("duplicate_document_rejected",
          code == 2 and not (destination / "duplicate-capture.json").exists(),
          f"exit={code}, no output created")

    # Existing evidence must not be overwritten even if an identical run is attempted.
    before = (destination / "baseline.json").read_bytes()
    code, _, _ = invoke(
        "capture", destination / "golden.json",
        "--rankings", destination / "baseline-observed.json",
        "--output", destination / "baseline.json",
    )
    after = (destination / "baseline.json").read_bytes()
    check("overwrite_refused", code == 2 and before == after, f"exit={code}, bytes preserved")

    changed = json.loads((destination / "candidate.json").read_text(encoding="utf-8"))
    changed[0]["critical"] = False
    write_new(destination / "metadata-tampered.json", changed)
    code, _, _ = invoke(
        "replay", destination / "metadata-tampered.json",
        "--baseline", destination / "baseline.json",
        "--policy", destination / "policy.json", "--k", "1",
    )
    check("critical_metadata_tampering_rejected", code == 2, f"exit={code}")

    code, _, stderr = invoke("studio", "--output", destination / "studio.html")
    studio = (destination / "studio.html")
    body = studio.read_text(encoding="utf-8") if studio.is_file() else ""
    check("offline_studio_generated",
          code == 0 and "Golden Dataset Studio" in body
          and "connect-src 'none'" in body,
          f"exit={code} {stderr.strip()}")

    summary = {
        "format": "openrag-luna-qa-probe/v1",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "cwd_writable": os.access(destination, os.W_OK),
        "total": len(checks),
        "passed": sum(x["passed"] for x in checks),
        "checks": checks,
        "notes": "Synthetic-only black-box test; does not replace real browser QA",
    }
    write_new(destination / "probe-summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/luna-qa-1"))
    args = parser.parse_args(argv)
    try:
        summary = probe(args.output_dir)
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as exc:
        parser.error(str(exc))
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
