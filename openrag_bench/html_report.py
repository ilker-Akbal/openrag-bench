"""Accessible, standalone and privacy-aware offline query explorer.

All untrusted data enters escaped text/HTML attributes only. The enhancement
script contains static code (no source strings, eval, network or external JS).
Questions and document IDs are NOT included in the rendered HTML.
"""
import json
from html import escape
from .cli import METRICS

COLORS = {
    "positive": "#166534",
    "negative": "#b91c1c",
}


def _table(metrics):
    result = ['<table class="summary"><thead><tr><th scope="col">Metric</th>'
              '<th scope="col">Score</th></tr></thead><tbody>']
    for name, value in metrics.items():
        result.append(
            f"<tr><th scope=\"row\">{escape(str(name))}</th>"
            f"<td class=\"number\">{float(value):+.4f}</td></tr>"
        )
    result.append("</tbody></table>")
    return "\n".join(result)


def _coverage(rows, *, paired=False):
    total = len(rows)
    no_judgments = sum(
        row.get("diagnostics", {}).get("judged_positive_count") == 0
        for row in rows if "judged_positive_count" in row.get("diagnostics", {})
    )
    empty = sum(
        row.get("diagnostics", {}).get("candidate_retrieved_count" if paired else "retrieved_count") == 0
        for row in rows if ("candidate_retrieved_count" if paired else "retrieved_count") in row.get("diagnostics", {})
    )
    hits = sum(
        row.get("diagnostics", {}).get("candidate_hits_at_k" if paired else "hits_at_k", 0) > 0
        for row in rows
    )
    return {"queries": total, "no_positive_labels": no_judgments,
            "empty_candidate_results": empty, "queries_with_hit": hits}


def _payload(row, paired):
    metrics = row["delta"] if paired else row["metrics"]
    return escape(json.dumps({key: float(metrics[key]) for key in METRICS if key in metrics},
                             separators=(",", ":"), allow_nan=False), quote=True)


def _query_display(row, index):
    return str(row.get("query_id") or f"row-{index:06d}")


def _tr(row, index, paired, selected):
    metrics = row["delta"] if paired else row["metrics"]
    d = row.get("diagnostics", {})
    label = escape(_query_display(row, index))
    score = float(metrics[selected])
    status = ("regressed" if score < 0 else "improved" if score > 0 else "unchanged") if paired else (
        "missed" if float(metrics.get("hit_at_k", 0)) == 0 else "hit"
    )
    judged = d.get("judged_positive_count", "—")
    retrieved = d.get("candidate_retrieved_count" if paired else "retrieved_count", "—")
    overlap = d.get("top_k_overlap_count", "—") if paired else "—"
    return (f'<tr data-status="{status}" data-scores="{_payload(row, paired)}">'
            f'<th scope="row">{label}</th>'
            f'<td class="number current-score">{score:+.4f}</td>'
            f'<td class="number">{judged}</td>'
            f'<td class="number">{retrieved}</td>'
            f'<td class="number">{overlap}</td>'
            f'<td><span class="status {status}">{status}</span></td></tr>')


# Explanations use only measured ranks and policy rules; no source text or document IDs.
_THRESHOLD_WORDS = {
    "min_delta": "Quality improvement below minimum",
    "min_score": "Average quality below minimum",
    "min_query_score": "A query failed its minimum score",
    "max_regressed_queries": "Too many queries got worse",
}


def _rank_label(rank):
    return "Not retrieved" if rank is None else f"#{int(rank)}"


def _guard_failure_ids(guard):
    """Return only IDs already selected by failed policies (no raw documents)."""
    failures = []
    critical = set()
    for rule in guard["rules"]:
        if rule["passed"]:
            continue
        ids = rule.get("regressed_query_ids", []) + rule.get("below_min_query_score_ids", [])
        if rule.get("selector", {}).get("type") == "critical":
            critical.update(ids)
        for query_id in ids:
            if query_id not in failures:
                failures.append(query_id)
    return failures, critical


def _guard_section(report):
    guard = report["guard"]
    blocked = not guard["passed"]
    failures, critical = _guard_failure_ids(guard)
    row_index = {row.get("query_id"): row for row in report.get("per_query_delta", [])}
    lost = sum(bool(row.get("diagnostics", {}).get("lost_top_k_hit"))
               for row in report.get("per_query_delta", []))
    gained = sum(bool(row.get("diagnostics", {}).get("gained_top_k_hit"))
                 for row in report.get("per_query_delta", []))
    bad_rules = [rule for rule in guard["rules"] if not rule["passed"]]
    delta = float(report["delta"]["ndcg_at_k"])
    improvement = delta > 1e-12
    critical_lost = any(
        row_index.get(query_id, {}).get("diagnostics", {}).get("lost_top_k_hit")
        for query_id in critical
    )
    if not blocked:
        reason = f"All {len(guard['rules'])} quality rules passed for the evaluated queries."
    elif critical_lost and improvement:
        reason = ("Overall retrieval quality improved, but a critical query lost its "
                  f"relevant top-{int(report['k'])} hit. This release must be blocked.")
    elif critical_lost:
        reason = (f"A critical query lost a relevant hit within the top {int(report['k'])} "
                  "results. This release must be blocked.")
    else:
        reason = (f"{len(bad_rules)} of {len(guard['rules'])} retrieval quality rules "
                  "were not met. Review the failed checks below.")
    state = "BLOCKED" if blocked else "PASSED"
    title = "Release blocked" if blocked else "Quality checks passed"
    lines = [
        f'<section class="guard-hero {"is-blocked" if blocked else "is-passed"}" '
        'aria-label="OpenRAG Guard decision">',
        '<div class="hero-top"><span class="eyebrow">OPENRAG GUARD · RELEASE DECISION</span>',
        f'<span class="decision-pill">{state}</span></div>',
        f'<h2>{title}</h2><p class="hero-reason">{escape(reason)}</p>',
        '<div class="score-grid">',
        ('<div class="score-tile"><small>Baseline NDCG@k</small>'
         f'<strong>{float(report["baseline"]["metrics"]["ndcg_at_k"]):.4f}</strong></div>'),
        ('<div class="score-tile"><small>Candidate NDCG@k</small>'
         f'<strong>{float(report["candidate"]["metrics"]["ndcg_at_k"]):.4f}</strong></div>'),
        ('<div class="score-tile"><small>NDCG@k change</small>'
         f'<strong class="{"up" if delta > 0 else "down" if delta < 0 else ""}">'
         f'{delta:+.4f}</strong></div>'),
        ('<div class="score-tile"><small>Lost / gained top-k hits</small>'
         f'<strong>{lost} / {gained}</strong></div>'),
        '</div>',
        f'<p class="hero-footnote">{len(bad_rules)} failed rules out of '
        f'{len(guard["rules"])}. Metrics measure retrieval relevance, not answer truth.</p>',
        '</section>',
    ]
    if blocked:
        lines += ['<section class="card attention" id="guard-failures" '
                  'aria-label="Reasons for blocking">',
                  '<div class="section-heading"><div>',
                  '<p class="eyebrow">NEXT ACTION</p>',
                  '<h2>What needs attention?</h2></div>',
                  '<a class="jump-link" href="#query-diagnostics">Inspect all queries ↓</a>',
                  '</div>']
        if critical_lost:
            lines.append('<p>A critical query stopped returning its required '
                         'relevant document within the configured top-k cutoff. '
                         'Review that regression before approving this change.</p>')
        else:
            lines.append('<p>The selected quality policy was not satisfied. '
                         'The report shows observed changes, not a proven root cause.</p>')
        if failures:
            # Policies expose a maximum of 20 IDs per failing threshold. Be explicit.
            ordered = sorted(failures, key=lambda x: (
                x not in critical,
                not row_index.get(x, {}).get("diagnostics", {}).get("lost_top_k_hit", False),
                str(x)))
            lines.append('<div class="failure-grid">')
            for query_id in ordered[:6]:
                row = row_index.get(query_id, {})
                diag = row.get("diagnostics", {})
                baseline_rank = diag.get("baseline_first_relevant_rank")
                candidate_rank = diag.get("candidate_first_relevant_rank")
                lost_hit = bool(diag.get("lost_top_k_hit"))
                tag = ("Critical query" if query_id in critical else "Regressed query")
                reason_line = ("Relevant top-k hit lost" if lost_hit else
                               "This query violates a selected rule")
                lines += [
                    '<article class="failure-card">',
                    f'<div class="failure-meta"><span>{escape(tag)}</span>'
                    '<span class="status regressed">Needs review</span></div>',
                    f'<h3>{escape(str(query_id))}</h3>',
                    f'<p>{reason_line}</p>',
                    '<div class="rank-compare">',
                    f'<div><small>Baseline first relevant</small><strong>'
                    f'{escape(_rank_label(baseline_rank))}</strong></div>',
                    f'<span aria-hidden="true">→</span><div>',
                    f'<small>Candidate first relevant</small><strong>'
                    f'{escape(_rank_label(candidate_rank))}</strong></div>',
                    '</div></article>',
                ]
            lines.append('</div>')
            if len(failures) > 6:
                lines.append('<p class="muted">Showing 6 highlighted query IDs. '
                             'Use Query diagnostics below to inspect all visible queries. '
                             'Policy output lists at most 20 IDs per threshold.</p>')
        else:
            lines.append('<p class="muted">No specific query ID was identified by the '
                         'failed threshold; inspect the policy scope and aggregate scores.</p>')
        lines.append('</section>')
    lines += [
        '<section class="card guard-rules" aria-label="Quality policies">',
        '<div class="section-heading"><div><p class="eyebrow">POLICIES</p>',
        '<h2>Quality checks</h2></div>',
        f'<span class="muted">{len(guard["rules"]) - len(bad_rules)} of '
        f'{len(guard["rules"])} passed</span></div>',
        '<div class="rule-list">',
    ]
    for item in guard["rules"]:
        is_pass = bool(item["passed"])
        errors = ", ".join(_THRESHOLD_WORDS.get(name, str(name))
                           for name in item.get("failed_thresholds", []))
        scope = item.get("selector", {}).get("type", "unknown")
        lines += [
            f'<div class="rule-item {"rule-pass" if is_pass else "rule-fail"}">',
            '<div class="rule-main">',
            f'<strong>{escape(str(item["id"]))}</strong>',
            f'<span class="muted">{escape(str(scope))} · '
            f'{escape(str(item["metric"]))} · {int(item["query_count"])} queries</span>',
            '</div>',
            '<div class="rule-result">',
            (f'<span class="status {"hit" if is_pass else "regressed"}">'
             f'{"Passed" if is_pass else "Blocked"}</span>'),
            f'<span class="rule-delta">{float(item["delta"]):+.4f}</span>',
            '</div></div>',
        ]
        if not is_pass and errors:
            lines.append(f'<p class="rule-explanation">{escape(errors)}</p>')
    lines += [
        '</div>',
        '<details class="detail-inset"><summary>Show precise rule values and thresholds</summary>',
        '<div class="table-wrap"><table><thead><tr>',
        '<th scope="col">Rule</th><th scope="col">Scope</th>',
        '<th scope="col">Metric</th><th scope="col">Queries</th>',
        '<th scope="col">Candidate mean</th><th scope="col">Delta</th>',
        '<th scope="col">Result</th></tr></thead><tbody>',
    ]
    for item in guard["rules"]:
        failed_names = ", ".join(item.get("failed_thresholds", []))
        outcome = "Passed" if item["passed"] else f"Failed: {failed_names}"
        lines.append(
            '<tr>'
            f'<th scope="row">{escape(str(item["id"]))}</th>'
            f'<td>{escape(str(item["selector"]["type"]))}</td>'
            f'<td>{escape(str(item["metric"]))}</td>'
            f'<td class="number">{int(item["query_count"])}</td>'
            f'<td class="number">{float(item["candidate_mean"]):.4f}</td>'
            f'<td class="number">{float(item["delta"]):+.4f}</td>'
            f'<td>{escape(outcome)}</td></tr>'
        )
    lines += [
        '</tbody></table></div></details>',
        '</section>',
    ]
    return lines, set(failures)


def render_html(report):
    paired = "delta" in report
    scores_reference = report["delta"] if paired else report["metrics"]
    available_metrics = [metric for metric in METRICS if metric in scores_reference]
    if not available_metrics:
        raise ValueError("Report must contain at least one supported metric")
    selected = "ndcg_at_k" if "ndcg_at_k" in available_metrics else available_metrics[0]
    if report.get("gate", {}).get("metric") in available_metrics:
        selected = report["gate"]["metric"]
    rows = report.get("per_query_delta" if paired else "per_query", [])
    rows = sorted(rows, key=lambda row: (
        float((row["delta"] if paired else row["metrics"])[selected]),
        str(row.get("query_id") or "")))
    coverage = _coverage(rows, paired=paired)
    title = "Paired retrieval comparison" if paired else "Retrieval evaluation"
    lines = [
        "<!doctype html>", '<html lang="en"><head><meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<meta name="referrer" content="no-referrer">',
        "<title>OpenRAG Bench · Diagnostic Explorer</title>",
        """<style>
:root{font-family:system-ui,sans-serif;color-scheme:light;--ink:#182437;--soft:#52647d;--edge:#cbd5e1;--accent:#2659bc}
*{box-sizing:border-box}body{margin:0;background:#f6f8fc;color:var(--ink);line-height:1.5}
main{max-width:1120px;margin:auto;padding:2rem 1rem 4rem}
h1{margin:.2rem 0;font-size:clamp(1.55rem,3vw,2.5rem)}h2{margin-top:2rem}
.muted{color:var(--soft)}.card{background:white;border:1px solid var(--edge);border-radius:14px;padding:1.1rem;margin:1rem 0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:.8rem}
.stat strong{display:block;font-size:1.7rem}.stat small{color:var(--soft)}
table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:.6rem .7rem;border-bottom:1px solid #dfe5ee}
thead{background:#eff4fc}th{font-weight:650}.number{font-variant-numeric:tabular-nums;text-align:right}
.table-wrap{overflow:auto;max-height:650px}.query-table{white-space:nowrap}
.query-table thead{position:sticky;top:0;z-index:1}
.controls{display:flex;gap:.7rem;flex-wrap:wrap;margin:1rem 0}
label{display:flex;gap:.4rem;align-items:center}input,select{font:inherit;border:1px solid #8295ae;border-radius:8px;padding:.45rem}
input{min-width:190px}button{font:inherit;border:1px solid #8295ae;border-radius:8px;background:white;padding:.5rem;cursor:pointer}
:focus-visible{outline:3px solid #e69b19;outline-offset:3px}
.status{font-size:.83rem;font-weight:600;padding:.2rem .5rem;border-radius:100px}
.regressed,.missed{background:#fee2e2;color:#991b1b}
.improved,.hit{background:#dcfce7;color:#166534}.unchanged{background:#edf2f7;color:#475569}
.bar-track{background:#e2e8f0;border-radius:100px;min-width:70px;height:.62rem;overflow:hidden}
.bar-fill{display:block;height:100%;background:var(--accent)}.negative{background:#b91c1c}
footer{margin-top:2rem;color:var(--soft);font-size:.92rem}
@media(max-width:650px){main{padding:1rem}.stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>""",
        '</head><body><main><header><p class="muted">OFFLINE · OPENRAG BENCH</p>',
        f"<h1>{title}</h1>",
        f'<p class="muted">Evaluated {int(report["count"])} labeled queries at k={int(report["k"])}. '
        "Query IDs only; raw questions and document IDs are not included in this HTML.</p></header>",
        '<section aria-label="Evaluation coverage" class="stats">',
    ]
    cards = [
        ("Queries", coverage["queries"]),
        ("No positive labels", coverage["no_positive_labels"]),
        ("Empty candidate results", coverage["empty_candidate_results"]),
        ("Queries with top-k hit", coverage["queries_with_hit"]),
    ]
    for label, value in cards:
        lines.append(
            f'<div class="card stat"><strong>{value}</strong>'
            f'<small>{escape(label)}</small></div>'
        )
    lines.append("</section>")
    failures = set()
    if "guard" in report:
        guard_lines, failures = _guard_section(report)
        lines.extend(guard_lines)
    if paired:
        lines += [
            '<details class="card metrics-panel">',
            '<summary>Detailed retrieval metrics (baseline, candidate and differences)</summary>',
            '<p class="muted">Scores are fractions from 0 to 1, not percentages. '
            'A delta of +0.3333 means +33.33 percentage points, not a 33% '
            'relative increase. Values for different metrics can coincide '
            'on simple top-1 fixtures with one positive label per query.</p>',
            '<div class="metric-columns">',
            '<div><h3>Candidate − baseline (macro average)</h3>',
            _table(report["delta"]), '</div>',
            '<div><h3>Candidate</h3>', _table(report["candidate"]["metrics"]), '</div>',
            '<div><h3>Baseline</h3>', _table(report["baseline"]["metrics"]), '</div>',
            '</div>',
            '<p class="muted">Paired bootstrap intervals are descriptive only, '
            'not statistical significance tests.</p></details>',
        ]
    else:
        lines += [
            '<details class="card metrics-panel" open>',
            '<summary>Aggregate metrics</summary>',
            _table(report["metrics"]), '</details>',
        ]
    if "per_query" not in report and "per_query_delta" not in report:
        lines.append("<p>No per-query rows available in aggregate-only report.</p>")
    else:
        lines += ['<section class="card"><h2>Query diagnostics</h2>',
                  '<p class="muted">Use the filters to focus on the worst queries. '
                  'Questions are deliberately omitted to protect private prompts. '
                  'Sorting and filtering work locally without any network access.</p>',
                  '<div class="controls">',
                  '<label for="query-search">Query ID <input type="search" id="query-search" placeholder="Filter query ID"></label>',
                  '<label for="metric-select">Metric <select id="metric-select">']
        for metric in available_metrics:
            selected_attr = " selected" if metric == selected else ""
            lines.append(f'<option value="{escape(metric)}"{selected_attr}>{escape(metric)}</option>')
        lines += ['</select></label>',
                  '<label for="status-filter">Outcome <select id="status-filter">',
                  '<option value="all">All queries</option>']
        opts = [("regressed","Regressed"),("improved","Improved"),("unchanged","Unchanged")] if paired else [("missed","No hit"),("hit","Hit")]
        for value, label in opts:
            lines.append(f'<option value="{value}">{label}</option>')
        lines += ['</select></label>',
                  '<label for="sort-direction">Sort <select id="sort-direction">',
                  '<option value="asc">Worst first</option><option value="desc">Best first</option>',
                  '</select></label></div>',
                  '<p id="visible-count" role="status" aria-live="polite">Showing '
                  f'{len(rows)} of {len(rows)} queries</p>',
                  '<div class="table-wrap"><table class="query-table"><thead><tr>',
                  '<th scope="col">Query ID</th><th scope="col">Metric value / delta</th>',
                  '<th scope="col">Positive labels</th><th scope="col">Results returned</th>',
                  '<th scope="col">Top-k overlap</th><th scope="col">Outcome</th>',
                  '</tr></thead><tbody id="query-rows">']
        for index, row in enumerate(rows, 1):
            lines.append(_tr(row, index, paired, selected))
        lines += ['</tbody></table></div></section>',
                  """<script type="text/javascript">
"use strict";
(() => {
  const search = document.getElementById("query-search");
  const metric = document.getElementById("metric-select");
  const status = document.getElementById("status-filter");
  const direction = document.getElementById("sort-direction");
  const tbody = document.getElementById("query-rows");
  const counter = document.getElementById("visible-count");
  const rows = Array.from(tbody.rows);
  function refresh() {
    const selected = metric.value;
    const query = search.value.toLocaleLowerCase();
    const chosen = status.value;
    let shown = 0;
    rows.sort((a,b) => {
      const x = JSON.parse(a.dataset.scores)[selected];
      const y = JSON.parse(b.dataset.scores)[selected];
      const value = x - y;
      return direction.value === "asc" ? value : -value;
    });
    for (const row of rows) {
      const values = JSON.parse(row.dataset.scores);
      const score = values[selected];
      row.querySelector(".current-score").textContent = (score >= 0 ? "+" : "") + score.toFixed(4);
      const matches = row.cells[0].textContent.toLocaleLowerCase().includes(query);
      const outcome = __PAIRED__ ? (score < 0 ? "regressed" : score > 0 ? "improved" : "unchanged") : row.dataset.status;
      const pill = row.querySelector(".status");
      if (__PAIRED__) {
        pill.className = "status " + outcome;
        pill.textContent = outcome;
      }
      const visible = matches && (chosen === "all" || chosen === outcome);
      row.hidden = !visible;
      if (visible) shown++;
      tbody.appendChild(row);
    }
    counter.textContent = "Showing " + shown + " of " + rows.length + " queries";
  }
  for (const input of [search,metric,status,direction]) {
    input.addEventListener("input", refresh);
    input.addEventListener("change", refresh);
  }
  refresh();
})();
</script>"""]
    lines = [line.replace("__PAIRED__", "true" if paired else "false") for line in lines]
    lines += ['<footer>Generated by OpenRAG Bench · No remote scripts, fonts, '
              'tracking or API calls. Raw questions/document IDs excluded. '
              'Keep report files private when query IDs are sensitive.</footer>',
              '</main></body></html>']
    return "\n".join(lines)
