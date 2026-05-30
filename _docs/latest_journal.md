# Latest Journal (Working Buffer)

Use this file as the **active-step buffer**.

## Workflow

1. At task start:
   - Read this file first.
   - If it has content from the previous step, append that content to the
     bottom of `_docs/journal.md` unchanged.
   - Clear this file back to this template.
2. During work:
   - Do not write intermediate noise here.
3. At task finish:
   - Write only the current completed step entry here.
   - Keep it in the same structure used by `_docs/journal.md`.

## Current Step Entry

## 2026-05-30 — D4 implementation: anomaly selector now links to symbol detail anchors

### What changed
- Added deterministic detail-anchor binding to anomaly selector payload in `mmsr/report/symbols.py`:
  - each row now includes `detail_anchor = symbol_detail_anchor_id(symbol)`.
- Updated anomaly detail panel rendering in `report.html.j2`:
  - detail pane now shows `Open detail page` link to `#<detail_anchor>` for the selected symbol.
- Added/updated tests to lock this behavior:
  - payload includes `detail_anchor`
  - rendered report includes `Open detail page`.

### Files changed
- `mmsr/report/symbols.py`
- `mmsr/report/templates/report.html.j2`
- `tests/test_symbol_anomaly_pages.py`
- `_docs/journal.md`
- `_docs/latest_journal.md`

### Tests updated
- `tests/test_symbol_anomaly_pages.py` assertions expanded for anchor payload + rendered link presence.

### Validation
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache conda run -n mmsr pre-commit run --all-files` passed.

### Current milestone
- D4 in progress.

### Estimated completion
- ~99% of D4.

### Remaining work
- D4 functional scope is complete; remaining work is final visual polish and roadmap milestone closeout.

### Best next deterministic implementation step
- Close D4 in design roadmap/milestone docs and start D5 polish/a11y/budget assertions.

### Open questions
- None.

## 2026-05-30 — Liquidity matrix semantics update: mean % change with z-score reference

### What changed
- Removed inaccurate threshold interpretation legend.
- Updated liquidity matrix semantics to factual display:
  - heatmap value uses **mean % change**
  - cell label includes **mean z-score in parentheses** as reference
- Updated panel copy and legend text to reflect data semantics only.
- Updated Plotly hover and colorbar labeling:
  - hover: `% Change / Z`
  - colorbar: `Mean % change`

### Files changed
- `mmsr/report/drilldowns.py`
- `mmsr/report/templates/report.html.j2`
- `tests/test_drilldowns.py`
- `_docs/journal.md`
- `_docs/latest_journal.md`

### Tests updated
- Updated drilldown assertions for new factual matrix copy and legend text.

### Validation
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache conda run -n mmsr pre-commit run --all-files` passed.

### Current milestone
- D4 in progress.

### Estimated completion
- ~97% of D4.

### Remaining work
- Optional: row-to-symbol-detail anchor binding from anomaly selector.

### Best next deterministic implementation step
- Add deterministic link from selected anomaly row to emitted symbol detail anchor and cover with render assertions.

### Open questions
- None.
