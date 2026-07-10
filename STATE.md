---
# ── MACHINE-READABLE SOURCE OF TRUTH (agents parse this block) ──
repo: simtek-trader          # local folder simtek-trader; GitHub remote is simtec-trader
schema_version: "1.0"
last_updated: "2026-07-10"
updated_by: "NewClaude"

# Where the project is in its lifecycle
phase: "live-hardening"
live_url: "https://simtek-trader-api.onrender.com"
production_commit: "6fe01d3"             # HEAD of main (forex 404/503 fix). Per VP handoff, Harold deployed it today; API verified live + healthy 2026-07-10, but /health exposes no commit/version field, so the deployed build identity is not independently verifiable from this repo — see ST-002.

# Last gate this repo passed (per Council tiered-gate model)
last_gate:
  name: "/review"
  result: "PASS"
  date: "2026-07-10"
  tier: "T1"                             # JSE/index 404-masking fix (this commit): 0 CRITICAL / 0 HIGH, 28/28 tests (16 new + 12 forex regression), live smoke 200/404/503 verified against a local server. Forex fix passed the same gate earlier today (see RESULT_TRADER_FOREX_404_FIX.md).

# Open findings — anything known-broken or deferred. Empty list = clean.
open_findings:
  - id: "ST-001"
    severity: "MEDIUM"
    summary: "JSE/index swallow bug — FIXED IN CODE at this commit, NOT yet in prod. fetch_jse_stock()/fetch_index() now use _history_with_retry() (same DataFetchError + 3x-backoff pattern as forex); /signal/{ticker} and /backtest/{ticker} map DataFetchError to 503. /review PASS, 28/28 tests, live smoke: NPN 200 real data / ZZZZQ 404 / dead-proxy 503 after 3 logged attempts on both endpoints. Prod still swallows until Harold's manual Render deploy. NOTE: fetch_index() has NO endpoint in main.py (library-level only) — API-level index tests were impossible; unit-tested instead."
    status: "fixed-awaiting-deploy"
    owner: "Harold (deploy)"
  - id: "ST-002"
    severity: "MEDIUM"
    summary: "requirements.txt does not pin yfinance (local 1.5.1; Render installs latest at build). The forex fix depends on Ticker.history(raise_errors=True) and the yfinance.exceptions taxonomy — an upstream breaking release would surface at deploy time. Also: Render deploy of 6fe01d3 not commit-verifiable from repo (/health has no version field); confirm 'Live' timestamp in Render console once."
    status: "open"
    owner: "NewClaude"

# The single next action. If Harold reads nothing else, he reads this.
next_action: "Harold: manual Render deploy of this commit, confirm 'Live' timestamp matches it, then curl prod /signal/NPN (expect 200 real data) — then close ST-001. yfinance pin (ST-002) deliberately NOT done in this task: pinning blind to local 1.5.1 could downgrade prod below whatever live-verified version Render installed for the forex fix; check the Render build log first, then pin in a deliberate follow-up."
next_action_tier: "T0"

# Cost band for the next_action (Council cost-matrix, banded not precise)
next_action_estimate:
  scope: "S"
  tokens_range: "5-20K"
  zar_range: "R0.10-R0.50"

# Council role context for this repo
monetization_candidate: true             # November 6 solution #2
simmy_dispatchable: "not-wired"          # Simmy renders Trader UI panels (TraderPanel.jsx / TraderMetrics.jsx) from static data, but the ask-simmy orchestrator's tool registry is chaos-only (get_latest_draws / get_analysis_summary / get_performance_summary) — no live Trader dispatch exists yet. Live Dispatch roadmap phase 2.
---

# Simtek Trader — Human-Readable State

**Phase:** Live, in hardening. **Live at:** simtek-trader-api.onrender.com
(FastAPI on Render, manual deploys — Render does NOT auto-deploy pushes).

## Where it stands
SIMZ trading-signals backend (JSE stocks, forex, index) plus a React frontend.
The forex 404-masking fix shipped today at `6fe01d3`: transient yfinance
failures now retry 3× with backoff and surface as **503** instead of being
swallowed into a fake 404; real invalid-pair 404s are preserved. /review PASS
(0 CRITICAL / 0 HIGH), 12/12 tests, all three live paths (200 / 404 / 503)
verified against a running server — full evidence in
`RESULT_TRADER_FOREX_404_FIX.md`. API checked live and healthy 2026-07-10
(`/signal/forex/ZAR/USD` → 200, `/health` clean). The youtube-shorts pipeline
consumes this API daily as its real signal source.

## Open findings
- **ST-001 (MEDIUM, fixed awaiting deploy):** JSE/index swallow bug fixed in
  code at this commit — `fetch_jse_stock()` / `fetch_index()` now use the same
  `_history_with_retry()` + `DataFetchError` pattern as forex, and
  `/signal/{ticker}` + `/backtest/{ticker}` return 503 on transient failure.
  /review PASS (0 CRITICAL / 0 HIGH), 28/28 tests, live smoke verified all
  three paths. Prod keeps the old behavior until Harold's manual Render
  deploy. Discovered en route: `fetch_index()` has no endpoint in `main.py` —
  it is a library function with no production caller, so index coverage is
  unit-level only (no route to integration-test).
- **ST-002 (MEDIUM, open):** yfinance unpinned in `requirements.txt`.
  Deliberately NOT pinned in the ST-001 task: prod was live-verified on
  whatever version Render installed at the forex deploy, which may be newer
  than local 1.5.1 — a blind pin could downgrade prod. Check Render's build
  log for the installed version, then pin deliberately.
- Known LOWs (pre-existing, untouched): duplicate `get_cache_key` def and dead
  code after `return` in `main.py`.

## What's next
Harold deploys this commit on Render (manual), confirms the "Live" timestamp
matches, curls prod `/signal/NPN` for 200 with real data — then ST-001 closes.

## Gate history (most recent first)
- 2026-07-10 · /review (JSE/index 404-masking fix) · PASS · T1
- 2026-07-10 · /review (forex 404-masking fix) · PASS · T1
- (earlier gates in git log)
