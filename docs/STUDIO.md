# Golden Dataset Studio — offline human relevance labeling

**Status:** included in the v0.5.0 GitHub alpha pre-release. Real-user browser and accessibility review are ongoing; no PyPI release.

## What it does

Golden Dataset Studio helps a developer prepare the human-verified question-to-document
relevance labels that an OpenRAG Bench evaluation requires. It does NOT run an LLM
or a retriever, upload document content, or automatically guess correct answers.

## Launch locally

Install the reviewed v0.5.0 GitHub wheel (or use a checked-out source tree) and run:

    python -m pip install -e .
    openrag-bench studio --output golden-dataset-studio.html

Then open the generated HTML file in a browser. On Windows PowerShell:

    Start-Process .\golden-dataset-studio.html

Studio refuses to overwrite an existing output file by default. The explicit
option --overwrite replaces the previously generated HTML only, not saved data.
No web server or cloud service is necessary.

## Workflow

1. Add stable document IDs which exactly match your retriever's output IDs.
   A display title is optional and stays in the editable draft; a local JSON
   document catalog of objects with id/title keys can be imported.
2. Create questions with unique query IDs; optionally set category and critical.
3. Assign 0=irrelevant or graded positive relevance 1, 2 or 3 to each document.
   Grading is a human labeling decision; the software cannot confirm truth.
4. Save an **editable draft** regularly. The page does not autosave.
5. Export golden judgment rows (OpenRAG Bench JSON array) and a matching
   version 1 Guard policy, then inspect and tune the policy thresholds.

## Export schema and critical safety distinction

The exported judgment JSON has query_id, question, category, critical,
retrieved_ids (intentionally []), relevant_ids, and relevance_grades.
Graded relevance maps exactly the positively labeled IDs, so it is
compatible with the existing evaluation input validator.

**An empty retrieved_ids list is NOT a measured retrieval benchmark.**
Run your own retrieval system to obtain real, ranked candidate/baseline
document IDs for each question; preserve matching ground truth, category,
critical metadata and query IDs. Then validate and evaluate:

    openrag-bench doctor candidate.json --baseline baseline.json --policy openrag-guard-policy.json --k 3
    openrag-bench guard candidate.json --baseline baseline.json --policy openrag-guard-policy.json --k 3 --html guard-report.html

Default policy includes overall NDCG@k non-regression, a strict critical
hit@k rule if any queries are critical, and category-specific NDCG@k
non-regression rules. Verify these thresholds and category choices against
your use case; auto-generated policies are only a starting point.

## Import and draft preservation

- Import an existing OpenRAG Bench JSON array of labeled query rows.
- Import a Studio draft with format identifier openrag-studio-draft/v1.
- Import a document catalog as a JSON array of {id,title} objects.
- Exports use explicit local downloads; imports use local FileReader.
- Never assume the editor has stored the state: closing or reloading
  loses unsaved work (it warns before leaving).
- Studio displays imported questions/document titles only in a local tab.

## Privacy and validation constraints

- No network requests, APIs, remote CSS/fonts/scripts, telemetry or logins.
- Restrictive CSP; dynamic labels rendered using DOM textContent.
- No localStorage or automatic browser persistence.
- Duplicate query and document IDs and unknown labeled references are rejected.
- Empty question, category or missing positive document labels prevent
  judgment/policy export. Draft export is allowed for incomplete work.
- Limits: 2,500 documents, 1,000 questions and imported JSON files below 5 MiB.
- Removing a document asks for confirmation and clears its references.
- Uploaded local JSON and downloaded drafts can contain private question text.
  Protect these files as private information.
- This feature does not provide real-time collaborative editing, multiuser
  approval, semantic deduplication, LLM labeling or corpus text ingestion.

## Testing and release readiness

Python unit tests validate generator output, safe file overwrite behavior,
offline design constraints and emitted data schema. GitHub Actions extracts
the embedded script and runs Node's JavaScript syntax checker. A real browser
end-to-end test and human usability review remain necessary before any
production-readiness claim. v0.5.0 is a public alpha pre-release.
