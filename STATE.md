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
    summary: "PROD: invalid symbols return 503 after 3 retries (~7s) instead of the 404 contract — verified on /signal/ZZZZQ, /signal/forex/XQZ/QQW, /signal/XQZW. Locally the same requests correctly 404. Harold's call 2026-07-10: same version + same code + different behavior means the cause is ENVIRONMENT-LEVEL (Yahoo treating Render's outbound IP differently — rate-limit/block shaping the response so yfinance raises a non-no-data exception), NOT package drift — version-pin plan DROPPED. Do not fix blind: capture the real exception from Render's environment first. The retry loop already logs it — every attempt logs the underlying exception repr; a probe at 2026-07-10 17:22:25 UTC (XQZW) left 4 such lines in Render's service logs. Get the repr (Harold pastes the log lines, or shell into the instance), THEN classify. Note: the ~7s is fully explained by the deliberate 2s+4s backoff — timing alone is not evidence of Yahoo slowness. Impact bounded: valid tickers 200, real transients 503, consumers only request valid tickers."
    status: "open"
    owner: "NewClaude (blocked on Render log access)"
  - id: "ST-002"
    severity: "LOW"
    summary: "requirements.txt does not pin yfinance. Downgraded from MEDIUM and DECOUPLED from ST-003 per Harold 2026-07-10 (cause is environment-level, not version drift). Pin deliberately once ST-003's evidence is in — not as a fix for it."
    status: "open"
    owner: "NewClaude"

# The single next action. If Harold reads nothing else, he reads this.
next_action: "ST-003 evidence capture: pull the 'Transient fetch failure for XQZW.JO (attempt 1/3): <repr>' lines from Render service logs around 2026-07-10 17:22:18-25 UTC (Harold pastes them, or shell into the instance and hit /signal/XQZW again). The repr names the real exception class + message from Render's environment; classify and scope the actual fix from that, not from local behavior."
next_action_tier: "T0"

# Cost band for the next_action (Council cost-matrix, banded not precise)
next_action_estimate:
  scope: "S"
  tokens_range: "5-15K"
  zar_range: "R0.10-R0.40"

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
- **ST-003 (MEDIUM, open, evidence-capture phase):** prod returns
  503-after-retries (~7s) for INVALID symbols instead of 404 — verified on
  `/signal/ZZZZQ`, `/signal/forex/XQZ/QQW`, `/signal/XQZW`; locally the same
  requests 404 correctly. Harold's redirect (2026-07-10): same version + same
  code + different behavior ⇒ environment-level cause (Yahoo responding
  differently to Render's outbound IP), NOT package drift — the version-pin
  fix plan is dropped. Rule: don't fix blind. The deployed retry loop already
  logs the real underlying exception (`repr`) on every attempt; a probe at
  17:22:25 UTC left those lines in Render's service logs. Next step is
  reading them (Harold pastes, or shell into the instance), then scoping the
  fix from the actual exception class — not from local guesses. The ~7s
  timing is the deliberate 2s+4s backoff, not evidence of Yahoo slowness.
- **ST-002 (LOW, open):** yfinance unpinned. Downgraded and decoupled from
  ST-003 per Harold — pin deliberately later; it is not the ST-003 fix.
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
Read the real exception out of Render's logs (probe timestamp 2026-07-10
17:22:18–25 UTC, ticker XQZW.JO, four log lines carrying the repr). Classify
from evidence, then scope the actual ST-003 fix.

## Gate history (most recent first)
- 2026-07-10 · /review (JSE/index 404-masking fix) · PASS · T1
- 2026-07-10 · /review (forex 404-masking fix) · PASS · T1
- (earlier gates in git log)
