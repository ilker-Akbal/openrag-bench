"""Show safe guard results in GitHub Step Summary; no PR write permission."""
import html
import json
import os
from pathlib import Path
import sys


def render(report):
    guard = report["guard"]
    state = "PASS" if guard["passed"] else "BLOCK"
    lines = [
        "## OpenRAG Guard — " + state, "",
        f"Evaluated {int(report['count'])} aligned queries at k={int(report['k'])}.",
        "",
        "| Policy | Metric | Queries | Candidate mean | Delta | Status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    def safe_cell(value):
        content = html.escape(str(value), quote=True).replace("|", "&#124;")
        for symbol, replacement in (("\\r", " "), ("\\n", " "),
                                    ("[", "&#91;"), ("]", "&#93;"),
                                    ("(", "&#40;"), (")", "&#41;"),
                                    ("\u0060", "&#96;")):
            content = content.replace(symbol, replacement)
        return content

    for item in guard["rules"]:
        state = "Pass" if item["passed"] else "Blocked"
        parts = [
            safe_cell(item["id"]),
            safe_cell(item["metric"]),
            str(int(item["query_count"])),
            f"{float(item['candidate_mean']):.4f}",
            f"{float(item['delta']):+.4f}",
            state,
        ]
        lines.append("| " + " | ".join(parts) + " |")
    lines += [
        "",
        "Only aggregate metrics and rule names are shown here; no questions,",
        "document contents, or query IDs are posted to the workflow summary.",
        "The optional JSON report remains in the runner workspace.",
    ]
    return "\n".join(lines) + "\n"


def main(argv=None):
    path = Path((argv if argv is not None else sys.argv[1:])[0])
    passed = False
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        result = render(data)
        passed = data["guard"]["passed"] is True
    else:
        result = "## OpenRAG Guard — ERROR\n\nEvaluation did not produce a report. Check the CI logs.\n"
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as handle:
            handle.write(result)
    else:
        print(result, end="")
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a", encoding="utf-8") as handle:
            handle.write("passed=" + ("true" if passed else "false") + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
