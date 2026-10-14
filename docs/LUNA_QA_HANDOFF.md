# Luna / Work independent QA handoff — OpenRAG Bench

**Target:** Public repository https://github.com/ilker-Akbal/openrag-bench
**Reference release:** v0.6.0 (published). Test **current main** in a fresh checkout,
and record the exact commit SHA. Main may include unreleased improvements.
**Status:** QA preparation. No results are claimed until the agent executes this task.

## 1. Test-only boundaries

You are the QA reviewer. Do **not** modify application code, commit, push,
merge PRs, tag releases, publish packages, or create real customer data.
Ask before any destructive operation. You may create output under
\`reports/luna-qa-<run-id>/\` (gitignored). Do not change prior captures.

Only **synthetic data** may appear in the screenshots or shared report.
No secrets, customer prompts, private document IDs, third-party datasets or
real API keys may be uploaded to ChatGPT or GitHub.

Do not presume browser/desktop/cloud environments can see one another's local
files. Report clearly if the Work cloud browser or file tools lack access.
Do not invent interactive browser evidence from source inspection.

## 2. First run in a clean, isolated environment

Clone the public repository (or copy the verified clean repository into an
isolated working directory; do not reuse an untrusted mutable checkout).

~~~bash
git clone https://github.com/ilker-Akbal/openrag-bench.git
cd openrag-bench
git rev-parse HEAD
git status --short
python --version
python -m pip install -e .
python scripts/luna_qa_probe.py --output-dir reports/luna-qa-1
~~~

If Python is unavailable or package installation is blocked by the Work
environment, report the blocker with commands and actual stderr. Do **not**
report the suite as passing without running it.

The probe tests the **real installed CLI via subprocess**: Capture accepts
complete observed rankings; Doctor checks alignment; Guard Replay blocks a
candidate whose macro score improved while the critical privacy query lost
its top-1 hit; a safe candidate passes; corrupted/duplicate/missing mappings
and changed critical flags fail closed; it refuses to overwrite evidence,
produces offline HTML, and confirms raw question/doc-ID markers do not leak
to Guard HTML or hash manifests.

Expected summary: every check passed and process exit code 0.
A deliberate Guard BLOCK (return code 2) is an **expected test pass**.
If any probe fails, record the failed check and don't suppress exceptions.

Only if a fresh environment supports it, also run:

~~~bash
python -m unittest discover -s tests -v
~~~

If Node.js is installed, run the existing Studio script smoke after generating
a second Studio HTML with the **exact required filename**:

~~~bash
openrag-bench studio --output studio-smoke.html
node tests/studio_ui_smoke.cjs
~~~

This writes synthetic smoke JSON into the fresh clone; do not commit it.

## 3. Real browser manual UI / E2E test — required separately

Open \`reports/luna-qa-1/studio.html\` in a browser available in **the same
runtime**. If local \`file://\` access is restricted, run a loopback-only
static server in the workspace:

~~~bash
python -m http.server 8765 --bind 127.0.0.1
~~~

Then open \`http://127.0.0.1:8765/reports/luna-qa-1/studio.html\`.
This is a temporary local file server; it must not be exposed to other
networks and must be stopped after QA.

Perform **real UI interactions** (do not claim them from code reading):

1. Open the pristine Studio page; verify 0 queries/0 documents and visible
   no-autosave disclosure.
2. Click "Load synthetic example"; verify exactly 3 documents and 3 labeled
   queries. Check that the privacy query is critical.
3. Change privacy relevance from 3 to 2; export the editable draft, golden
   judgments and Guard policy; inspect actual downloaded JSON.
4. Reload the tab: unsaved state should not be silently retained; import
   the draft and confirm grades/critical flag and counts survive.
5. Attempt a duplicate document ID and a duplicate query ID; confirm errors
   appear and no valid annotation is overwritten. Avoid destructive deletion.
6. Try malformed JSON and a query missing positive labels; UI must reject
   invalid golden export without a silent success.
7. Check keyboard Tab/Shift+Tab navigation and visible focus outlines.
   Test a desktop width and ~390px mobile viewport for clipped buttons,
   overflow, unintelligible labels and unusable controls.
8. Open \`blocked.html\` and \`passed.html\` created by the CLI probe. Confirm
   decision is visible near the top, regressions are not hidden on the PASSED
   report, and query filters/sorting are operational with mouse **and** keyboard.
9. Inspect network activity for unexpected third-party requests; Studio should
   not make telemetry requests. If devtools/network inspection is impossible,
   write "not verified" rather than claiming privacy is proven.

Screenshot only **original synthetic** screens. If an item is impossible in
the current Work/browser environment, write \`BLOCKED\` with an exact reason,
not \`PASS\`.

## 4. QA report deliverable

Write an original report to \`reports/luna-qa-1/LUNA_TEST_REPORT.md\` with:

- Exact SHA, platform, Python/browser versions, date, installation result
- Each automated check with PASS/FAIL, actual command and evidence file
- Each manual UI step with PASS/FAIL/BLOCKED/NOT RUN and screenshot filenames
- Severity-ordered findings (\`ID | Severity | Reproduction | Expected | Actual
  | Evidence | Suggested fix\`); differentiate reproducible bugs from guesses
- Accessibility, responsive, security/privacy and no-network observations
- Time from beginning the task to first successful report (actual observation,
  never fabricated), constraints, proposed prioritized fixes
- A final verdict: **PASS**, **PASS WITH ISSUES**, **FAIL** or **INCOMPLETE**

All tests must remain non-destructive. Do not print or publish user data. Do
not create GitHub issues/PRs without the owner's request. This is AI-assisted
QA, **not independent external developer adoption**.

## 5. Files to inspect

- \`scripts/luna_qa_probe.py\` — synthetic black-box CLI evaluation
- \`docs/OWN_RAG_QUICKSTART.md\` — first-time developer instructions
- \`docs/STUDIO.md\` and \`docs/CAPTURE_REPLAY.md\` — behavior and contracts
- \`tests/studio_ui_smoke.cjs\`, \`tests/test_studio.py\` — existing regression tests
- \`openrag_bench/studio.py\`, \`openrag_bench/capture.py\`,
  \`openrag_bench/commands.py\` and \`openrag_bench/html_report.py\`
- \`reports/luna-qa-1/\` — probe evidence only; never commit

Report **actual observed behavior** over claims in README or tests. Pay
particular attention to accessibility, export/import round-trip correctness,
critical-query policy failures, and accidental data exposure.
