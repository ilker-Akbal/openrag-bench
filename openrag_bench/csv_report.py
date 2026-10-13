"""Dependency-free, spreadsheet-safe per-query CSV reports."""
import csv
from io import StringIO

from .cli import METRICS


def _safe_id(value):
    """Prevent formulas in spreadsheet apps when reading untrusted query IDs."""
    text = str(value)
    if text.lstrip().startswith(("=", "+", "-", "@")) or (
            text and text[0] in ("\t", "\r", "\n")):
        return "'" + text
    return text


def render_csv(report):
    """Write query-level scores with stable, documented columns.

    Question text is intentionally omitted: questions frequently contain
    sensitive source data, and the report only needs stable query identifiers.
    """
    stream = StringIO(newline="")
    writer = csv.writer(stream, lineterminator="\n")
    if "delta" not in report:
        writer.writerow(["query_id", *METRICS])
        for index, row in enumerate(report["per_query"], 1):
            query_id = row.get("query_id") or f"row_{index:06d}"
            writer.writerow([_safe_id(query_id),
                             *(row["metrics"][metric] for metric in METRICS)])
    else:
        columns = [f"{scope}_{metric}" for scope in
                   ("baseline", "candidate", "delta") for metric in METRICS]
        writer.writerow(["query_id", *columns])
        base = {row["query_id"]: row["metrics"]
                for row in report["baseline"]["per_query"]}
        cand = {row["query_id"]: row["metrics"]
                for row in report["candidate"]["per_query"]}
        for item in report["per_query_delta"]:
            query_id = item["query_id"]
            writer.writerow([
                _safe_id(query_id),
                *(base[query_id][metric] for metric in METRICS),
                *(cand[query_id][metric] for metric in METRICS),
                *(item["delta"][metric] for metric in METRICS),
            ])
    return stream.getvalue()
