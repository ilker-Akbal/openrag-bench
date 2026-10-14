"""Deterministic, offline retrieval capture with explicit stable-document mappings.

Golden labels must come from human judgment. This module never guesses relevance,
queries a network service, or fabricates missing rankings.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .cli import _validate


def _digest(value):
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _indexed_golden(judgments):
    _validate(judgments, 1)
    indexed = {}
    for row in judgments:
        query_id = row.get("query_id")
        if not isinstance(query_id, str) or not query_id.strip() or query_id in indexed:
            raise ValueError("Golden judgments require unique nonempty query_id values")
        if not isinstance(row.get("question"), str) or not row["question"].strip():
            raise ValueError(f"{query_id!r}: a nonempty question is required for capture")
        if row["retrieved_ids"]:
            raise ValueError(f"{query_id!r}: golden input must have empty retrieved_ids")
        if not row["relevant_ids"]:
            raise ValueError(f"{query_id!r}: a positive human judgment is required")
        if "critical" in row and type(row["critical"]) is not bool:
            raise ValueError(f"{query_id!r}: critical must be boolean")
        if "category" in row and (not isinstance(row["category"], str)
                                   or not row["category"].strip()):
            raise ValueError(f"{query_id!r}: category must be nonempty text")
        indexed[query_id] = row
    return indexed


def _validated_map(id_map):
    if id_map is None:
        return None
    if not isinstance(id_map, dict) or any(
            not isinstance(source, str) or not source.strip()
            or not isinstance(target, str) or not target.strip()
            for source, target in id_map.items()):
        raise ValueError("ID map must be a JSON object of nonempty string IDs")
    return id_map


def _ranked_ids(ids, query_id, id_map):
    if not isinstance(ids, list) or any(
            not isinstance(doc, str) or not doc.strip() for doc in ids):
        raise ValueError(f"{query_id!r}: retrieved_ids must be a list of nonempty strings")
    if len(set(ids)) != len(ids):
        raise ValueError(f"{query_id!r}: duplicate raw document IDs")
    if id_map is None:
        mapped = list(ids)
    else:
        unknown = sorted(set(ids) - set(id_map))
        if unknown:
            raise ValueError(f"{query_id!r}: unmapped document ID(s): {unknown}")
        mapped = [id_map[doc] for doc in ids]
    if len(set(mapped)) != len(mapped):
        raise ValueError(f"{query_id!r}: ID mapping collapses distinct ranked documents")
    return mapped


def capture_rows(judgments, rankings, *, id_map=None):
    """Return evaluator-compatible rows with real ranked IDs, preserving label metadata.

    Rankings are [{'query_id': str, 'retrieved_ids': [str, ...]}].
    Empty retrieved_ids is a valid *observed* result; missing queries are not.
    If an ID mapping is given every raw ID must be mapped explicitly.
    """
    golden = _indexed_golden(judgments)
    mapping = _validated_map(id_map)
    if not isinstance(rankings, list):
        raise ValueError("Rankings must be a JSON array")
    by_query = {}
    for row in rankings:
        if not isinstance(row, dict) or set(row) != {"query_id", "retrieved_ids"}:
            raise ValueError("Ranking rows require exactly query_id and retrieved_ids")
        query_id = row["query_id"]
        if not isinstance(query_id, str) or not query_id.strip():
            raise ValueError("Ranking query_id must be a nonempty string")
        if query_id in by_query:
            raise ValueError(f"Duplicate ranking query_id {query_id!r}")
        by_query[query_id] = _ranked_ids(row["retrieved_ids"], query_id, mapping)
    if set(by_query) != set(golden):
        missing = sorted(set(golden) - set(by_query))
        extra = sorted(set(by_query) - set(golden))
        raise ValueError(f"Rankings query IDs differ: missing={missing}, extra={extra}")

    result = []
    for query_id, golden_row in golden.items():
        row = {key: golden_row[key] for key in (
            "query_id", "question", "category", "critical",
            "relevant_ids", "relevance_grades") if key in golden_row}
        row["retrieved_ids"] = by_query[query_id]
        result.append(row)
    _validate(result, 1)
    return result


def capture_from_retriever(retriever, judgments, k, *, id_map=None):
    """Capture a synchronous Retriever.retrieve(question, k) without scoring it.

    The caller owns the retriever and its environment. No optional adapter is
    imported unless the caller chooses to use one.
    """
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")
    golden = _indexed_golden(judgments)
    rankings = []
    for query_id, row in golden.items():
        ids = retriever.retrieve(row["question"], k)
        if isinstance(ids, (str, bytes)):
            raise ValueError(f"{query_id!r}: retriever must return ranked document IDs")
        try:
            ranked = list(ids)
        except TypeError as exc:
            raise ValueError(f"{query_id!r}: retriever must return ranked document IDs") from exc
        if len(ranked) > k:
            raise ValueError(f"{query_id!r}: retriever returned more than k IDs")
        rankings.append({"query_id": query_id, "retrieved_ids": ranked})
    return capture_rows(judgments, rankings, id_map=id_map)


def _write_new(path, payload):
    """Create an output exclusively; remove it if writing fails partway."""
    path = Path(path)
    created = False
    try:
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            created = True
            handle.write(payload)
    except BaseException:
        if created:
            path.unlink(missing_ok=True)
        raise


def capture(argv=None):
    """Capture ranked JSON results onto Studio judgments; never overwrite files."""
    from .io import read_rows

    parser = argparse.ArgumentParser(prog="openrag-bench capture",
                                     description="Bind real ranked results to human golden labels")
    parser.add_argument("golden", type=Path, help="Studio-exported golden judgments JSON")
    parser.add_argument("--rankings", type=Path, required=True,
                        help="JSON/JSONL rows of query_id and ranked retrieved_ids")
    parser.add_argument("--id-map", type=Path, help="JSON mapping raw ID to canonical golden ID")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, help="Optional hash-only capture manifest")
    args = parser.parse_args(argv)
    try:
        output_paths = [args.output] + ([args.manifest] if args.manifest else [])
        if len(set(p.resolve() for p in output_paths)) != len(output_paths):
            raise ValueError("Output and manifest paths must be different")
        if any(p.exists() or p.is_symlink() for p in output_paths):
            raise ValueError("Capture refuses to overwrite existing output files")
        golden = read_rows(args.golden)
        ranks = read_rows(args.rankings)
        mapping = (json.loads(args.id_map.read_text(encoding="utf-8-sig"))
                   if args.id_map else None)
        rows = capture_rows(golden, ranks, id_map=mapping)
        serialized = json.dumps(rows, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        manifest = {
            "format": "openrag-capture/v1",
            "query_count": len(rows),
            "queries_with_results": sum(bool(row["retrieved_ids"]) for row in rows),
            "golden_sha256": _digest(golden),
            "rankings_sha256": _digest(rows),
            "id_map_sha256": _digest(mapping) if mapping is not None else None,
        }
        # Validate everything before writing, and roll back an already written
        # primary dataset if writing the optional manifest subsequently fails.
        completed = []
        try:
            _write_new(args.output, serialized)
            completed.append(args.output)
            if args.manifest:
                _write_new(args.manifest, json.dumps(manifest, indent=2,
                                                     ensure_ascii=False) + "\n")
                completed.append(args.manifest)
        except BaseException:
            for completed_path in reversed(completed):
                completed_path.unlink(missing_ok=True)
            raise
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    return 0


def replay(argv=None):
    """Run the existing fail-closed Guard on two previously captured snapshots."""
    from .commands import guard
    return guard(argv)
