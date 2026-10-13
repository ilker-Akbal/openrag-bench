"""Standalone HTML report generator; all user-controlled strings are escaped."""
from html import escape


def _table(metrics):
    result = ['<table><thead><tr><th>Metric</th><th>Score</th></tr></thead><tbody>']
    for key, value in metrics.items():
        result.append(f"<tr><td>{escape(str(key))}</td><td>{float(value):+.4f}</td></tr>")
    result.append("</tbody></table>")
    return "\n".join(result)


def render_html(report):
    lines = [
        "<!doctype html>",
        '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        "<title>OpenRAG Bench Report</title>",
        "<style>body{font:16px system-ui;max-width:950px;margin:3rem auto;padding:0 1rem;color:#17202a}"
        "table{border-collapse:collapse;width:100%;margin:1rem 0}"
        "th,td{padding:.7rem;border-bottom:1px solid #ccc;text-align:left}"
        "th{background:#f4f6f7}code{font-size:.9em}</style>",
        "</head><body><h1>OpenRAG Bench</h1>",
        f'<p>Evaluated {int(report["count"])} queries at k={int(report["k"])}</p>'
    ]
    if "delta" in report:
        lines.append("<h2>Candidate − baseline (macro average)</h2>")
        lines.append(_table(report["delta"]))
        lines.append("<h2>Candidate</h2>")
        lines.append(_table(report["candidate"]["metrics"]))
        lines.append("<h2>Baseline</h2>")
        lines.append(_table(report["baseline"]["metrics"]))
        lines.append("<p>Bootstrap intervals are descriptive, not significance tests.</p>")
        lines.append("<h2>Per-query deltas</h2>")
        rows = [{"question": row["query_id"], "metrics": row["delta"]}
                for row in report["per_query_delta"]]
    else:
        lines.append("<h2>Aggregate metrics</h2>")
        lines.append(_table(report["metrics"]))
        lines.append("<h2>Per-query results</h2>")
        rows = report.get("per_query", [])

    lines.append('<table><thead><tr><th>Query</th><th>Scores</th></tr></thead><tbody>')
    for row in rows:
        label = escape(str(row.get("question") or row.get("query_id") or "—"))
        scores = ", ".join(f"{escape(str(key))}: {float(value):+.3f}"
                           for key, value in row["metrics"].items())
        lines.append(f"<tr><td>{label}</td><td>{scores}</td></tr>")
    lines.append("</tbody></table></body></html>")
    return "\n".join(lines)
