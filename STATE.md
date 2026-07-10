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
  tier: "T1"                             # forex 404-masking fix: 12/12 tests, live 200/404/503 all verified (see RESULT_TRADER_FOREX_404_FIX.md)

# Open findings — anything known-broken or deferred. Empty list = clean.
open_findings:
  - id: "ST-001"
    severity: "MEDIUM"
    summary: "fetch_jse_stock() and fetch_index() retain the identical except-Exception→empty-DataFrame swallow that fetch_forex() had — transient yfinance failures (rate limit, network) still masked as 404 on all JSE stock and index endpoints. Deliberately deferred out of the forex-fix scope, NOT forgotten."
    status: "open"
    owner: "NewClaude"
  - id: "ST-002"
    severity: "MEDIUM"
    summary: "requirements.txt does not pin yfinance (local 1.5.1; Render installs latest at build). The forex fix depends on Ticker.history(raise_errors=True) and the yfinance.exceptions taxonomy — an upstream breaking release would surface at deploy time. Also: Render deploy of 6fe01d3 not commit-verifiable from repo (/health has no version field); confirm 'Live' timestamp in Render console once."
    status: "open"
    owner: "NewClaude"

# The single next action. If Harold reads nothing else, he reads this.
next_action: "Close ST-001: apply the same DataFetchError + retry-with-backoff pattern to fetch_jse_stock()/fetch_index() (mirror tests/test_forex_fetch_errors.py for the JSE endpoints), pinning yfinance in requirements.txt in the same task — unless Harold reprioritizes."
next_action_tier: "T1"

# Cost band for the next_action (Council cost-matrix, banded not precise)
next_action_estimate:
  scope: "M"
  tokens_range: "30-60K"
  zar_range: "R0.75-R1.50"

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
- **ST-001 (MEDIUM, open):** `fetch_jse_stock()` / `fetch_index()` still have
  the pre-fix swallow bug — transient failures masked as 404 on JSE endpoints.
  Deferred deliberately when the forex fix was scoped; the fix pattern and its
  test suite are ready to mirror.
- **ST-002 (MEDIUM, open):** yfinance unpinned in `requirements.txt` (fix
  relies on its exception taxonomy); and prod build identity is unverifiable
  from the repo — Harold should eyeball the Render "Live" timestamp once.
- Known LOWs (pre-existing, untouched): duplicate `get_cache_key` def and dead
  code after `return` in `main.py`.

## What's next
Fix ST-001 with the same `DataFetchError` + retry pattern, pin yfinance in the
same task. Then the JSE endpoints stop lying about transient failures too.

## Gate history (most recent first)
- 2026-07-10 · /review (forex 404-masking fix) · PASS · T1
- (earlier gates in git log)
