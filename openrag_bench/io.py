"""Offline JSON array and JSON Lines (NDJSON) dataset ingestion."""
import json
from pathlib import Path


def read_rows(path, *, input_format="auto"):
    """Read a list of labeled retrieval rows.

    auto: .jsonl/.ndjson -> JSON Lines; everything else -> JSON array.
    Blank lines are ignored in JSONL. Errors identify exact source and line.
    """
    source = Path(path)
    if input_format not in ("auto", "json", "jsonl"):
        raise ValueError("input_format must be auto, json or jsonl")
    selected = ("jsonl" if source.suffix.lower() in (".jsonl", ".ndjson")
                else "json") if input_format == "auto" else input_format
    with source.open("r", encoding="utf-8-sig") as handle:
        if selected == "json":
            try:
                return json.load(handle)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{source}: invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
                ) from exc

        rows = []
        for lineno, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"{source}: invalid JSON Lines record at line {lineno}, "
                    f"column {exc.colno}: {exc.msg}"
                ) from exc
            if not isinstance(item, dict):
                raise ValueError(f"{source}: JSON Lines record at line {lineno} must be an object")
            rows.append(item)
        if not rows:
            raise ValueError(f"{source}: JSON Lines file contains no records")
        return rows
