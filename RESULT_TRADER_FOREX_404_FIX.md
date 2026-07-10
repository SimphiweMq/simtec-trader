# RESULT: Trader Forex 404-Masking Fix

**Task**: HANDOFF_TRADER_FOREX_404_FIX · Tier T1 · 2026-07-10
**Status**: Fix committed + tested locally. **NOT yet deployed to Render** — pending Harold's manual deploy + "Live" timestamp check.

---

## 1. Original `fetch_forex()` as found (hard rule 1 evidence)

`src/data_fetcher.py`, lines 54–93 before the fix:

```python
def fetch_forex(from_currency: str, to_currency: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch forex pair data.
    ...
    Returns:
        DataFrame with columns: Date, Open, High, Low, Close, Volume.
        Date is the index and timezone-naive. Returns empty DataFrame on error.
    """
    try:
        # Construct forex ticker symbol
        forex_ticker = f"{from_currency}{to_currency}=X"

        logger.info(f"Fetching forex data for {forex_ticker}...")
        df = yf.download(forex_ticker, period=period, interval=interval, progress=False)

        if df.empty:
            logger.warning(f"No data returned for {forex_ticker}")
            return pd.DataFrame()

        # Reset index to make Date a column, then convert to timezone-naive
        df.reset_index(inplace=True)
        if df['Date'].dt.tz is not None:
            df['Date'] = df['Date'].dt.tz_localize(None)
        df.set_index('Date', inplace=True)

        # Ensure only required columns
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]

        logger.info(f"Successfully fetched {len(df)} rows for {forex_ticker}")
        return df

    except Exception as e:
        logger.error(f"Error fetching forex {from_currency}{to_currency}: {str(e)}")
        return pd.DataFrame()
```

**Diagnosis confirmed — with one addition.** The `except Exception → return pd.DataFrame()` swallow is exactly as the VP diagnosed. But the swallowing is actually **two layers deep**: in the installed yfinance (1.5.1), `yf.download()` itself never raises — it catches every per-ticker exception internally (`multi.py::_download_one`), logs it, and returns an empty DataFrame. So even deleting the `try/except` in `fetch_forex` would not have fixed the bug. The fix therefore switches to `yf.Ticker(...).history(..., raise_errors=True)`, the documented API for getting real exceptions out of yfinance.

`fetch_jse_stock()` (lines 12–51) and `fetch_index()` have the **identical swallow pattern** — shown to satisfy hard rule 1, left unfixed per the out-of-scope boundary. Recommend a follow-up task mirroring this fix for the JSE endpoints.

## 2. Fix applied

**Plain English:** `fetch_forex` now fetches via `Ticker.history(raise_errors=True)` so real errors surface. yfinance's "this symbol has no data" errors (`YFPricesMissingError`, `YFTickerMissingError`, `YFTzMissingError`, `YFInvalidPeriodError`) are classified as *permanent no-data* → empty DataFrame → main.py's existing 404, unchanged. Everything else (rate limit, network, upstream errors) is *transient* → retried up to 3 times with linear backoff (2s, 4s), each attempt logged with the real underlying error, then raised as a new `DataFetchError` (with `__cause__` chained). `main.py` maps `DataFetchError` to **503** in both forex endpoints (`/signal/forex/...` and `/backtest/forex/...`), placed before the generic 500 catch-all.

**Key diff — `src/data_fetcher.py`:**

```python
MAX_FETCH_RETRIES = 3
RETRY_BACKOFF_SECONDS = 2.0

_NO_DATA_ERRORS = (YFPricesMissingError, YFTickerMissingError, YFTzMissingError, YFInvalidPeriodError)

class DataFetchError(Exception):
    """Transient failure fetching market data (rate limit, network, upstream)."""

def _history_with_retry(ticker, period, interval):
    last_error = None
    for attempt in range(1, MAX_FETCH_RETRIES + 1):
        try:
            return yf.Ticker(ticker).history(period=period, interval=interval,
                                             actions=False, raise_errors=True)
        except _NO_DATA_ERRORS as e:
            logger.warning(f"No data exists for {ticker}: {e}")
            return pd.DataFrame()          # → caller's 404 path (preserved)
        except Exception as e:
            last_error = e
            logger.warning(f"Transient fetch failure for {ticker} (attempt {attempt}/{MAX_FETCH_RETRIES}): {e!r}")
            if attempt < MAX_FETCH_RETRIES:
                time.sleep(RETRY_BACKOFF_SECONDS * attempt)
    logger.error(f"All {MAX_FETCH_RETRIES} fetch attempts failed for {ticker}: {last_error!r}")
    raise DataFetchError(...) from last_error   # → caller's 503 path (new)
```

`fetch_forex` itself lost its outer `try/except` entirely; unexpected errors now propagate (visible) instead of being silenced.

**Key diff — `src/main.py`** (both forex endpoints):

```python
    except HTTPException:
        raise
    except DataFetchError as e:                                   # NEW
        logger.error(f"Transient fetch failure for {from_currency}/{to_currency}: {str(e)}")
        raise HTTPException(status_code=503,
            detail=f"Market data source temporarily unavailable for {from_currency}/{to_currency}; please retry shortly")
    except Exception as e:
        ...  # unchanged 500
```

## 3. /review — **PASS (APPROVE)**

Gate criteria:
- ✅ Transient failures no longer masked as 404 (mapped to 503, real error logged with `repr` + chained cause)
- ✅ Real 404 preserved for invalid pairs (verified live, see below)
- ✅ Retry bounded: exactly 3 attempts, linear backoff, ~6s worst case; no-data errors are not retried at all
- ✅ No new error-swallowing: no-data errors are logged and intentionally mapped to the 404 contract; everything else raises

Findings: 0 CRITICAL, 0 HIGH. MEDIUM (out of scope, follow-up): `fetch_jse_stock`/`fetch_index` still swallow; `requirements.txt` doesn't pin yfinance (local 1.5.1, Render installs latest at build — `raise_errors` exists in all recent versions). LOW (pre-existing, untouched): duplicate `get_cache_key` def and dead code after `return` in `main.py`.

## 4. Test evidence

Automated: **12/12 passed** (`tests/test_forex_fetch_errors.py` — 7 unit on fetcher, 5 integration on API status codes, covering transient-vs-invalid so it can't silently regress).

Live server (uvicorn, real Yahoo):

| Case | Request | Result |
|---|---|---|
| Valid pair | `GET /signal/forex/ZAR/USD?period=6mo` | **200**, real history ending 2026-07-10 close 0.06137, current signal `BUY` |
| Invalid pair | `GET /signal/forex/XQZ/QQW` | **404** `"Forex pair XQZQQW not found"` (Yahoo returned real quote-not-found) |
| Transient (server run behind dead proxy → all Yahoo requests fail) | `GET /signal/forex/ZAR/USD` | **503** `"Market data source temporarily unavailable for ZAR/USD; please retry shortly"` after 3 logged attempts, ~6s |

## 5. Deployment

**NOT deployed.** Render (`simtek-trader-api`, Python 3.11.9) does not auto-deploy. Pending: Harold sign-off → manual Render deploy → verify "Live" timestamp → confirm `GET /signal/forex/ZAR/USD` returns 200 in prod.

## 6. Cost calibration

Estimate was 40–80K tokens. Actual: ~60–70K (within band). Scope stayed M — no expansion beyond the two files + tests.
