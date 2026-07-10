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
  - id: "ST-004"
    severity: "LOW"
    summary: "Invalid-symbol 404 contract UNVERIFIED in prod (not broken — unreachable so far): every prod probe to date hit Yahoo's rate limiter (YFRateLimitError, per Render logs) before symbol validity was ever evaluated. Verify with the quiet-window protocol: 60+ min no probes → canary a valid UNCACHED ticker (200 = Yahoo serving Render's IP) → exactly ONE invalid probe → read status + Render log line ('No data exists' + 404 = confirmed; YFRateLimitError + 503 = still limited, stop). One probe is definitive because the two outcomes log differently. WATCH ITEM attached: Yahoo rate-limits Render's shared outbound IP in bursts (valid NPN fetched 200 between limited probes) — if valid tickers start 503ing in normal use, that becomes an availability finding; 60-min cache + YT pipeline skip-day currently absorb it."
    status: "open"
    owner: "NewClaude"
  - id: "ST-002"
    severity: "LOW"
    summary: "requirements.txt does not pin yfinance. Decoupled from the (closed) ST-003 per Harold 2026-07-10. Pin deliberately as hygiene in some future task."
    status: "open"
    owner: "NewClaude"

# The single next action. If Harold reads nothing else, he reads this.
next_action: "Run the ST-004 quiet-window test (60+ min no probes, valid-uncached canary, then ONE invalid probe, read Render log line) to confirm the invalid-symbol 404 contract in prod. Zero code changes expected."
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
- **ST-004 (LOW, open):** invalid-symbol 404 contract unverified in prod —
  every probe so far was rate-limited before validity was evaluated. Run the
  quiet-window protocol (see YAML) for a definitive single-probe answer.
  Watch item: if Yahoo's bursty rate-limiting of Render's IP starts hitting
  valid tickers in normal use, escalate to an availability finding.
- **ST-002 (LOW, open):** yfinance unpinned. Hygiene, decoupled, later.
- Known LOWs (pre-existing, untouched): duplicate `get_cache_key` def and dead
  code after `return` in `main.py`.

## Closed findings
- **ST-003** (was MEDIUM, closed 2026-07-10 — NOT A BUG): prod's
  503-on-invalid-symbol turned out to be **correct behavior**. Render logs
  showed the underlying exception is `YFRateLimitError` — Yahoo rate-limiting
  Render's outbound IP — which is the textbook transient case the fix exists
  for (it's the exact exception the test suite uses to prove the 503 path).
  The invalid ticker was never evaluated; Yahoo refused the request first.
  Local 404s differed because the home IP isn't rate-limited. Residual
  verification moved to ST-004. Self-observation note for future verifiers:
  each invalid-symbol probe burns 3 Yahoo calls, so probe barrages sustain
  the very rate limit being investigated — space probes 60+ min apart.
- **ST-001** (was MEDIUM): JSE/index swallow bug — transient failures masked
  as 404. Fixed in `19506f0` (same `_history_with_retry()` + `DataFetchError`
  pattern as forex, `/signal/{ticker}` + `/backtest/{ticker}` → 503 on
  transient). /review PASS, 28/28 tests, local smoke 200/404/503. Deploy
  verified in prod 2026-07-10 evening: process restart observed, new 503
  contract live, `/signal/NPN` + `/backtest/NPN` 200 with real data. Closed
  2026-07-10. (Its deploy verification is what surfaced ST-003 → ST-004.)

## Decisions
- 2026-07-10 — Harold: `fetch_index()` intentionally has no exposed endpoint —
  not needed. Function fixed and tested for consistency with the swallow-bug
  pattern, but deliberately not wired to `main.py`.

## What's next
Quiet-window test for ST-004 (60+ min silence → valid-uncached canary → one
invalid probe → read the Render log line). Expected outcome: 404 confirmed,
zero code changes.

## Gate history (most recent first)
- 2026-07-10 · /review (JSE/index 404-masking fix) · PASS · T1
- 2026-07-10 · /review (forex 404-masking fix) · PASS · T1
- (earlier gates in git log)
