"""Audit distributable archives before an OpenRAG Bench release.

Does not establish copyright ownership or audit package dependencies.
"""
from pathlib import Path
import tarfile
import zipfile


REQUIRED = (
    "openrag_bench/metrics.py",
    "openrag_bench/cli.py",
    "openrag_bench/comparison.py",
    "openrag_bench/trec.py",
    "openrag_bench/integrations/faiss.py",
    "openrag_bench/io.py",
    "openrag_bench/csv_report.py",
    "openrag_bench/integrations/frameworks.py",
    "openrag_bench/html_report.py",
    "openrag_bench/streaming.py",
    "openrag_bench/guard.py",
    "openrag_bench/commands.py",
    "openrag_bench/studio.py",
    "openrag_bench/capture.py",
)
FORBIDDEN = {"day-01-llm-rag-agents", "day-02-computer-vision",
             "day-03-sensor-fusion-navigation", "practice",
             "data", "reports", ".venv", "__pycache__"}


def check_names(names, archive_name):
    cleaned = []
    for name in names:
        if name.startswith("/") or ".." in Path(name).parts:
            raise ValueError(f"{archive_name}: unsafe archive path: {name}")
        pieces = name.replace("\\", "/").split("/")
        if any(part in FORBIDDEN or part.startswith("day-") for part in pieces):
            raise ValueError(f"{archive_name}: excluded path found: {name}")
        if name.lower().endswith((".pdf", ".mp4", ".pth", ".pt", ".safetensors")):
            raise ValueError(f"{archive_name}: prohibited binary asset: {name}")
        if any(part == ".env" or part.endswith(".download") for part in pieces):
            raise ValueError(f"{archive_name}: sensitive source artifact: {name}")
        cleaned.append(name)
    for path in REQUIRED:
        if not any(name.endswith(path) for name in cleaned):
            raise ValueError(f"{archive_name}: missing package file {path}")


def audit(directory):
    dist = Path(directory)
    wheels = sorted(dist.glob("openrag_bench-*.whl"))
    tarballs = sorted(dist.glob("openrag_bench-*.tar.gz"))
    if len(wheels) != 1 or len(tarballs) != 1:
        raise ValueError("Expected exactly one wheel and one source distribution")
    with zipfile.ZipFile(wheels[0]) as zf:
        names = zf.namelist()
        check_names(names, "wheel")
        metadata = next((name for name in names if name.endswith(".dist-info/METADATA")), None)
        entrypoints = next((name for name in names if name.endswith(".dist-info/entry_points.txt")), None)
        if not metadata or not entrypoints:
            raise ValueError("Wheel missing metadata or command-line entry point")
        meta = zf.read(metadata).decode("utf-8")
        entries = zf.read(entrypoints).decode("utf-8")
        if "Name: openrag-bench" not in meta or "License-Expression: MIT" not in meta:
            raise ValueError("Wheel package name or MIT license metadata missing")
        if "openrag-bench = openrag_bench.cli:main" not in entries:
            raise ValueError("Wheel console entry point missing")
        if not any(name.endswith("/LICENSE") for name in names):
            raise ValueError("Wheel has no license file")
    with tarfile.open(tarballs[0], "r:gz") as tf:
        names = tf.getnames()
        check_names(names, "source distribution")
        for required in ("pyproject.toml", "README.md", "LICENSE",
                         "docs/USAGE.md", "docs/FRAMEWORK_INTEGRATIONS.md",
                         "benchmarks/scifact_2026-10-13.json",
                         "tests/test_formats.py",
                         "tests/test_grades.py",
                         "tests/test_framework_adapters.py",
                         "scripts/audit_distributions.py",
                         "tests/test_explorer.py",
                         "tests/test_turkish.py",
                         "tests/test_streaming.py",
                         "tests/property_metrics.py",
                         "docs/TURKISH_BENCHMARK.md",
                         "docs/QUALITY.md",
                         "examples/turkish_real_benchmark.py",
                         "examples/framework_real_integration.py",
                         "scripts/benchmark_streaming.py",
                         "benchmarks/streaming_100k_2026-10-13.json",
                         "tests/test_guard.py",
                         "tests/test_studio.py",
                         "tests/studio_ui_smoke.cjs",
                         "docs/STUDIO.md",
                         "docs/CAPTURE_REPLAY.md",
                         "docs/OWN_RAG_QUICKSTART.md",
                         "docs/LUNA_QA_HANDOFF.md",
                         "scripts/luna_qa_probe.py",
                         "tests/test_luna_qa_probe.py",
                         "tests/test_quickstart_capture_replay.py",
                         "examples/quickstart_capture_replay.py",
                         "tests/test_capture_replay.py",
                         "tests/test_scifact_capture_replay.py",
                         "examples/scifact_capture_replay.py",
                         "docs/GUARD.md",
                         "examples/guard_baseline.json",
                         "examples/guard_candidate.json",
                         "examples/guard_regression.json",
                         "examples/guard_policy.json"):
            if not any(name.endswith("/" + required) for name in names):
                raise ValueError(f"Source distribution missing {required}")
    return wheels[0], tarballs[0]


if __name__ == "__main__":
    wheel, sdist = audit("dist")
    print(f"Release archive audit passed: {wheel.name} and {sdist.name}")
