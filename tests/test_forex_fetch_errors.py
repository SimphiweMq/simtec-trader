"""Tests for the forex 404-masking fix.

Covers the transient-vs-invalid distinction:
- A genuinely invalid pair (no data) still yields 404 from the API.
- A transient fetch failure (rate limit, network) yields 503, never 404.
- Transient failures are retried with bounded backoff before giving up.
"""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from yfinance.exceptions import YFPricesMissingError, YFRateLimitError, YFTzMissingError

import data_fetcher
from data_fetcher import DataFetchError, MAX_FETCH_RETRIES, fetch_forex


def make_ohlcv_df(rows: int = 200) -> pd.DataFrame:
    """Build a synthetic OHLCV DataFrame shaped like a yfinance history result."""
    dates = pd.date_range("2024-01-01", periods=rows, freq="D", tz="UTC")
    rng = np.random.default_rng(42)
    close = 18.0 + rng.normal(0, 0.1, rows).cumsum()
    return pd.DataFrame(
        {
            "Open": close + 0.01,
            "High": close + 0.05,
            "Low": close - 0.05,
            "Close": close,
            "Volume": np.zeros(rows),
        },
        index=pd.DatetimeIndex(dates, name="Date"),
    )


def mock_ticker_factory(history_side_effect):
    """Return a patchable yf.Ticker replacement whose .history behaves as given."""
    ticker_instance = MagicMock()
    ticker_instance.history.side_effect = history_side_effect
    return MagicMock(return_value=ticker_instance), ticker_instance


# ==================== UNIT: data_fetcher.fetch_forex ====================


@pytest.mark.unit
class TestFetchForexTransientVsInvalid:
    def test_transient_failure_raises_data_fetch_error_after_bounded_retries(self):
        # Arrange: every attempt fails with a rate-limit error
        ticker_cls, ticker_instance = mock_ticker_factory(YFRateLimitError())

        # Act / Assert
        with patch.object(data_fetcher.yf, "Ticker", ticker_cls), \
             patch.object(data_fetcher.time, "sleep") as mock_sleep:
            with pytest.raises(DataFetchError):
                fetch_forex("ZAR", "USD", period="1y")

        # Assert: bounded retries, backoff between attempts, not infinite
        assert ticker_instance.history.call_count == MAX_FETCH_RETRIES
        assert mock_sleep.call_count == MAX_FETCH_RETRIES - 1

    def test_transient_failure_chains_underlying_error(self):
        underlying = ConnectionError("connection reset by peer")
        ticker_cls, _ = mock_ticker_factory(underlying)

        with patch.object(data_fetcher.yf, "Ticker", ticker_cls), \
             patch.object(data_fetcher.time, "sleep"):
            with pytest.raises(DataFetchError) as exc_info:
                fetch_forex("ZAR", "USD")

        assert exc_info.value.__cause__ is underlying

    def test_transient_then_success_recovers_via_retry(self):
        # Arrange: first attempt rate-limited, second succeeds
        df = make_ohlcv_df()
        ticker_cls, ticker_instance = mock_ticker_factory([YFRateLimitError(), df])

        with patch.object(data_fetcher.yf, "Ticker", ticker_cls), \
             patch.object(data_fetcher.time, "sleep"):
            result = fetch_forex("ZAR", "USD")

        assert not result.empty
        assert ticker_instance.history.call_count == 2

    def test_invalid_pair_returns_empty_df_without_retry(self):
        # Arrange: yfinance signals "no data exists for this symbol"
        ticker_cls, ticker_instance = mock_ticker_factory(
            YFPricesMissingError("XXXYYY=X", "no price data found")
        )

        with patch.object(data_fetcher.yf, "Ticker", ticker_cls), \
             patch.object(data_fetcher.time, "sleep") as mock_sleep:
            result = fetch_forex("XXX", "YYY")

        # Assert: empty df (so main.py 404s), no pointless retries
        assert result.empty
        assert ticker_instance.history.call_count == 1
        assert mock_sleep.call_count == 0

    def test_missing_timezone_treated_as_not_found(self):
        ticker_cls, _ = mock_ticker_factory(YFTzMissingError("XXXYYY=X"))

        with patch.object(data_fetcher.yf, "Ticker", ticker_cls), \
             patch.object(data_fetcher.time, "sleep"):
            result = fetch_forex("XXX", "YYY")

        assert result.empty

    def test_empty_history_without_error_returns_empty_df(self):
        ticker_cls, _ = mock_ticker_factory([pd.DataFrame()])

        with patch.object(data_fetcher.yf, "Ticker", ticker_cls):
            result = fetch_forex("XXX", "YYY")

        assert result.empty

    def test_success_returns_normalized_ohlcv_frame(self):
        ticker_cls, _ = mock_ticker_factory([make_ohlcv_df()])

        with patch.object(data_fetcher.yf, "Ticker", ticker_cls):
            result = fetch_forex("ZAR", "USD")

        assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]
        assert result.index.name == "Date"
        assert result.index.tz is None


# ==================== INTEGRATION: API status codes ====================


@pytest.fixture
def client():
    import main

    main._cache.clear()
    return TestClient(main.app)


@pytest.mark.integration
class TestForexEndpointStatusCodes:
    def test_valid_pair_returns_signal_history(self, client, monkeypatch):
        import main

        monkeypatch.setattr(
            main, "fetch_forex", lambda *a, **kw: make_ohlcv_df().tz_localize(None)
        )

        response = client.get("/signal/forex/ZAR/USD")

        assert response.status_code == 200
        body = response.json()
        assert body["ticker"] == "ZAR/USD"
        assert len(body["history"]) > 0

    def test_invalid_pair_still_returns_404(self, client, monkeypatch):
        import main

        monkeypatch.setattr(main, "fetch_forex", lambda *a, **kw: pd.DataFrame())

        response = client.get("/signal/forex/XXX/YYY")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_transient_failure_returns_503_not_404(self, client, monkeypatch):
        import main

        def raise_transient(*args, **kwargs):
            raise DataFetchError("yfinance rate limited after 3 attempts")

        monkeypatch.setattr(main, "fetch_forex", raise_transient)

        response = client.get("/signal/forex/ZAR/USD")

        assert response.status_code == 503
        assert response.status_code != 404

    def test_backtest_transient_failure_returns_503(self, client, monkeypatch):
        import main

        def raise_transient(*args, **kwargs):
            raise DataFetchError("yfinance rate limited after 3 attempts")

        monkeypatch.setattr(main, "fetch_forex", raise_transient)

        response = client.get("/backtest/forex/ZAR/USD")

        assert response.status_code == 503

    def test_backtest_invalid_pair_still_returns_404(self, client, monkeypatch):
        import main

        monkeypatch.setattr(main, "fetch_forex", lambda *a, **kw: pd.DataFrame())

        response = client.get("/backtest/forex/XXX/YYY")

        assert response.status_code == 404
