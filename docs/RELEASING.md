# Maintainer release checklist

The first version [v0.1.0](https://github.com/ilker-Akbal/openrag-bench/releases/tag/v0.1.0)
was published as a **GitHub pre-release** on 2026-10-13. Its build workflow
passed package tests, archive-content audit, clean-venv wheel installation,
SHA256SUMS validation and GitHub Release publication.

This checklist applies to **future** releases. A package version alone never
proves that a later release exists.

## Pre-release verification

- [ ] Maintainer confirms authorship/redistribution rights of every exported
      source file, test, example and documentation item.
- [ ] MIT copyright notice, third-party model and dataset references are correct.
- [ ] Run the full test matrix using a clean clone; review GitHub Actions.
- [ ] Build both archives and run the distribution contents audit:
  ```bash
  python -m pip install build
  python -m build
  python scripts/audit_distributions.py
  ```
- [ ] Install the wheel into a fresh virtual environment; verify CLI commands.
- [ ] Reproduce baseline benchmark with official SciFact ZIP and published MD5.
- [ ] Review `CHANGELOG.md`, README limitations, upgrade guidance and CI jobs.
- [ ] Enable GitHub private vulnerability reporting if available, and provide
      a maintainer contact for confidential reports.
- [ ] Ensure no dataset corpora, secrets, model artifacts or private user data
      are present in release archives or commit history.

## Versioned release procedure for future versions

1. Confirm the version in `pyproject.toml` matches the intended tag.
2. From the reviewed clean `main` commit, create a signed or annotated
   Git tag such as `v0.1.0`. Push the tag and verify it resolves to
   the reviewed commit.
3. Generate SHA-256 hashes for wheel and source distribution.
4. Create a GitHub Release from that tag with tested Python versions,
   public changelog, known limitations, integrity hashes and provenance.
5. Consider PyPI/Trusted Publishing **separately**. Do not imply a package
   is published to PyPI until a real installation has been verified.
6. Keep responding to genuine issues and maintaining compatibility.

The benchmark datasets and model weights are **not** shipped in OpenRAG Bench
releases and retain their own licenses.

## Codex for Open Source application evidence

Never invent usage, external maintainers, downloads or independent benchmarks.
Evidence should refer to actual public tags, active issue triage, releases,
authentic external integrations and tracked maintenance work. A technically
complete first release does **not** guarantee admission.
