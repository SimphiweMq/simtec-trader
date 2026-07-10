---
# ── MACHINE-READABLE SOURCE OF TRUTH (agents parse this block) ──
repo: simtek-trader          # local folder simtek-trader; GitHub remote is simtec-trader
schema_version: "1.0"
last_updated: "2026-07-10"
updated_by: "NewClaude"

# Where the project is in its lifecycle
phase: "live-hardening"
live_url: "https://simtek-trader-api.onrender.com"
production_commit: "19506f0"             # JSE/index fix. Deploy VERIFIED live 2026-07-10 evening: process restart observed (/health in-memory cache emptied), and prod serves the 503 error string that only exists in this commit. /signal/NPN 200 real data, /backtest/NPN 200.

# Last gate this repo passed (per Council tiered-gate model)
last_gate:
  name: "/review"
  result: "PASS"
  date: "2026-07-10"
  tier: "T1"                             # JSE/index 404-masking fix (this commit): 0 CRITICAL / 0 HIGH, 28/28 tests (16 new + 12 forex regression), live smoke 200/404/503 verified against a local server. Forex fix passed the same gate earlier today (see RESULT_TRADER_FOREX_404_FIX.md).

# Open findings — anything known-broken or deferred. Empty list = clean.
open_findings:
  - id: "ST-003"
    severity: "MEDIUM"
    summary: "PROD REGRESSION (found during ST-001 deploy verification, 2026-07-10): invalid symbols return 503 after 3 pointless retries (~7s) instead of the 404 contract — verified on BOTH /signal/ZZZZQ and /signal/forex/XQZ/QQW. Locally (yfinance 1.5.1) the same requests correctly 404. Strong hypothesis: prod's yfinance (unpinned, Render installs latest) raises a different exception type for missing symbols, so _NO_DATA_ERRORS misses it and it's misclassified as transient. This is ST-002's risk materialized. Impact bounded: valid tickers 200, transient errors 503 (correct), YT pipeline and frontend only request valid tickers; but the 404 contract is broken and invalid requests burn 3 Yahoo calls each. Note this means the forex fix's invalid-pair 404 was only ever verified locally, never in prod."
    status: "open"
    owner: "NewClaude"
  - id: "ST-002"
    severity: "MEDIUM"
    summary: "requirements.txt does not pin yfinance (local 1.5.1; Render installs latest at build). No longer theoretical — see ST-003. Fix together: read the installed version from Render's build log, reproduce ST-003 locally against that version, then extend _NO_DATA_ERRORS and/or pin, redeploy, and verify invalid symbols 404 IN PROD (add that probe to the deploy checklist)."
    status: "open"
    owner: "NewClaude"

# The single next action. If Harold reads nothing else, he reads this.
next_action: "Close ST-003 + ST-002 together: get prod's yfinance version from the Render build log, reproduce the invalid-symbol misclassification locally on that version, extend _NO_DATA_ERRORS (and pin yfinance), redeploy, verify prod: invalid ticker AND invalid forex pair both 404, valid 200."
next_action_tier: "T1"

# Cost band for the next_action (Council cost-matrix, banded not precise)
next_action_estimate:
  scope: "M"
  tokens_range: "20-50K"
  zar_range: "R0.50-R1.25"

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
- **ST-003 (MEDIUM, open):** prod returns 503-after-retries (~7s) for INVALID
  symbols instead of 404 — verified on both `/signal/ZZZZQ` and
  `/signal/forex/XQZ/QQW` right after the ST-001 deploy. Locally the same
  requests 404 correctly, so prod's (unpinned, newer) yfinance almost
  certainly raises a missing-symbol exception type that `_NO_DATA_ERRORS`
  doesn't cover. ST-002's risk, no longer hypothetical. Bounded impact: valid
  tickers work, real transient errors are handled correctly, and the API's
  actual consumers only request valid tickers.
- **ST-002 (MEDIUM, open):** yfinance unpinned. Fix together with ST-003:
  read the installed version from Render's build log, reproduce locally,
  extend `_NO_DATA_ERRORS` and/or pin, redeploy, verify invalid symbols 404
  in prod.
- Known LOWs (pre-existing, untouched): duplicate `get_cache_key` def and dead
  code after `return` in `main.py`.

## Closed findings
- **ST-001** (was MEDIUM): JSE/index swallow bug — transient failures masked
  as 404. Fixed in `19506f0` (same `_history_with_retry()` + `DataFetchError`
  pattern as forex, `/signal/{ticker}` + `/backtest/{ticker}` → 503 on
  transient). /review PASS, 28/28 tests, local smoke 200/404/503. Deploy
  verified in prod 2026-07-10 evening: process restart observed, new 503
  contract live, `/signal/NPN` + `/backtest/NPN` 200 with real data. Closed
  2026-07-10. (Its deploy verification is what surfaced ST-003.)

## Decisions
- 2026-07-10 — Harold: `fetch_index()` intentionally has no exposed endpoint —
  not needed. Function fixed and tested for consistency with the swallow-bug
  pattern, but deliberately not wired to `main.py`.

## What's next
Close ST-003 + ST-002 as one task: align on prod's actual yfinance version,
broaden the no-data classification (and pin), redeploy, and this time verify
the invalid-symbol 404 contract in prod, not just locally.

## Gate history (most recent first)
- 2026-07-10 · /review (JSE/index 404-masking fix) · PASS · T1
- 2026-07-10 · /review (forex 404-masking fix) · PASS · T1
- (earlier gates in git log)
