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

## 2026-05-30 — D3/D4 fix: render bug + execution-ease heatmap orientation update

### What changed
- Fixed the drilldown heatmap render bug by changing JSON payload serialization for script tags:
  - removed HTML-entity escaping for embedded JSON
  - added safe `</` escaping (`<\\/`) for script payloads
- Applied the same script-payload fix to symbol anomaly explorer payloads.
- Updated drilldown matrix heatmap orientation:
  - rows = group values
  - columns = market-condition metrics
- Updated drilldown heatmap scoring semantics to execution ease:
  - uses `z_score` when available
  - sign-normalized by metric polarity (`higher_is_better`)
  - positive score = easier execution, negative = worse execution
- Scoped heatmap metrics to execution-condition set:
  - `quoted_spread_bps`
  - `top_of_book_depth`
  - `primary_quote_reversion_100ms_bps`
  - `primary_quote_reversion_500ms_bps`
- Updated Plotly wiring for new axis orientation and click behavior (`point.y` selects group trend).
- Updated drilldown symbol/report tests for the new selection and render behavior.

### Files changed
- `mmsr/report/drilldowns.py`
- `mmsr/report/symbols.py`
- `mmsr/report/templates/report.html.j2`
- `tests/test_drilldowns.py`
- `_docs/journal.md`
- `_docs/latest_journal.md`

### Tests updated
- `tests/test_drilldowns.py` expectations updated for matrix availability/ordering under new metric filtering and sort behavior.

### Validation
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache conda run -n mmsr pre-commit run --all-files` passed.

### Current milestone
- D3 complete and hardened.
- D4 in progress.

### Estimated completion
- ~90% of D4 stream.

### Remaining work
- Optional: add explicit legend text block matching positive/negative execution-ease thresholds.
- Optional: add anchor link from selected anomaly row to emitted symbol detail page section.

### Best next deterministic implementation step
- Add deterministic execution-ease legend thresholds and corresponding regression assertions in rendered HTML.

### Open questions
- None.

## 2026-05-30 — D4 implementation: anomaly row selector linked to detail panel

### What changed
- Added a deterministic symbol anomaly explorer block in `mmsr/report/symbols.py`:
  - left side anomaly row list (symbol, metric, status)
  - right side detail panel (symbol/metric/status/current/reference/change/scope)
  - deterministic default selection uses anomaly rank index `0`
- Wired the explorer into `build_symbol_anomaly_page()` so it renders above the anomaly table.
- Added CSS and JavaScript in `mmsr/report/templates/report.html.j2`:
  - responsive two-column explorer layout
  - click row updates detail panel
  - selected-row highlight state
- Updated symbol anomaly tests to validate:
  - explorer presence
  - deterministic default selection ordering
  - rendered report contains explorer hooks.

### Files changed
- `mmsr/report/symbols.py`
- `mmsr/report/templates/report.html.j2`
- `tests/test_symbol_anomaly_pages.py`
- `_docs/journal.md`
- `_docs/latest_journal.md`

### Tests updated
- `tests/test_symbol_anomaly_pages.py` assertions expanded for explorer block and ordering.

### Validation
- `PRE_COMMIT_HOME=/tmp/pre-commit-cache conda run -n mmsr pre-commit run --all-files` passed (ruff, mypy, full pytest).

### Current milestone
- D4 in progress (symbol drilldown UX cleanup).

### Estimated completion
- ~85% of D4.

### Remaining work
- Optional refinement: connect explorer row to symbol detail page anchor when detail pages exist.
- Continue redesign stream toward D5 polish/a11y/budget hardening.

### Best next deterministic implementation step
- Add optional “open detail page” link binding from selected anomaly row to emitted symbol detail anchor and lock with render assertions.

### Open questions
- None.
