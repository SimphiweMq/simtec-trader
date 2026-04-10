"""FastAPI backend for Simtek Trading signal engine and backtester."""

import os
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd

from data_fetcher import fetch_jse_stock, fetch_forex, get_available_jse_tickers
from signal_engine import SignalEngine
from backtester import Backtester

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Simple in-memory cache with TTL
_cache = {}
CACHE_TTL = 3600  # 1 hour


class Signal(BaseModel):
    """Signal response model."""
    ticker: str
    timestamp: str
    close: float
    signal: Optional[str]
    signal_strength: float
    rsi: Optional[float]
    macd: Optional[float]


class SignalHistory(BaseModel):
    """Signal history response."""
    ticker: str
    period: str
    current_signal: Optional[Signal]
    history: list


class BacktestStats(BaseModel):
    """Backtest statistics response."""
    ticker: str
    period: str
    initial_capital: float
    final_value: float
    total_return_pct: float
    total_trades: int
    win_rate: float
    avg_win_pct: float
    avg_loss_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    best_trade_pct: float
    worst_trade_pct: float
    days_tested: int


def get_cache_key(ticker: str, period: str, interval: str) -> str:
    """Generate cache key."""
    return f"{ticker}_{period}_{interval}".lower()


def is_cache_valid(cache_entry: dict) -> bool:
    """Check if cache entry is still valid."""
    timestamp = cache_entry.get('timestamp')
    if not timestamp:
        return False
    return (datetime.now() - timestamp).total_seconds() < CACHE_TTL


def get_cached_data(key: str) -> Optional[pd.DataFrame]:
    """Retrieve cached data if valid."""
    if key in _cache and is_cache_valid(_cache[key]):
        logger.info(f"Cache hit for {key}")
        return _cache[key]['data']
    return None


def set_cache(key: str, data: pd.DataFrame):
    """Store data in cache."""
    _cache[key] = {
        'data': data,
        'timestamp': datetime.now()
    }
    logger.info(f"Cached {key}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown."""
    logger.info("Simtek Trading API starting up...")
    yield
    logger.info("Simtek Trading API shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Simtek Trading API",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


@app.get("/tickers")
async def get_tickers():
    """Get available JSE tickers."""
    tickers = get_available_jse_tickers()
    return {"tickers": tickers}


@app.get("/signal/{ticker}", response_model=SignalHistory)
async def get_signal(
    ticker: str,
    period: str = Query("2y", min_length=1),
    interval: str = Query("1d", min_length=1)
):
    """
    Get trading signals for a JSE stock.
    
    Args:
        ticker: Stock ticker (e.g., "NPN")
        period: Data period (default: "2y")
        interval: Data interval (default: "1d")
    
    Returns:
        Current signal and 90-day history
    """
    try:
        # Check cache first
        cache_key = get_cache_key(ticker, period, interval)
        df = get_cached_data(cache_key)
        
        if df is None:
            # Fetch fresh data
            df = fetch_jse_stock(ticker, period=period, interval=interval)
            
            if df.empty:
                raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
            
            set_cache(cache_key, df)
        
        # Generate signals
        engine = SignalEngine(df)
        df_signals = engine.generate_signals()
        
        # Build history (last 90 rows)
        history = []
        for idx, row in df_signals.tail(90).iterrows():
            try:
                close_val = float(row['Close'])
                signal_val = row['signal']
                rsi_val = row['RSI_14']
                macd_val = row['MACD']
                
                signal_strength = 0.0
                if pd.notna(rsi_val):
                    signal_strength = float(rsi_val) / 100.0
                
                macd_float = None
                if pd.notna(macd_val):
                    macd_float = float(macd_val)
                
                rsi_float = None
                if pd.notna(rsi_val):
                    rsi_float = float(rsi_val)
                
                history.append({
                    'date': idx.isoformat(),
                    'close': close_val,
                    'signal': signal_val if signal_val is not None else None,
                    'signal_strength': signal_strength,
                    'rsi': rsi_float,
                    'macd': macd_float,
                })
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error building history row: {str(e)}")
                continue
        
        # Get current signal (last row)
        current_row = df_signals.iloc[-1]
        current_signal = None
        signal_value = current_row.get('signal')
        # Check if signal_value is not null/None
        if signal_value is not None and str(signal_value).strip() != 'None':
            try:
                rsi_current = current_row.get('RSI_14')
                signal_strength = 0.0
                if pd.notna(rsi_current):
                    signal_strength = float(rsi_current) / 100.0
                
                current_signal = Signal(
                    ticker=f"{ticker}.JO",
                    timestamp=df_signals.index[-1].isoformat(),
                    close=float(current_row['Close']),
                    signal=str(signal_value),
                    signal_strength=signal_strength,
                    rsi=float(rsi_current) if pd.notna(rsi_current) else None,
                    macd=float(current_row['MACD']) if pd.notna(current_row.get('MACD')) else None,
                )
            except (ValueError, TypeError):
                pass
        
        return SignalHistory(
            ticker=f"{ticker}.JO",
            period=period,
            current_signal=current_signal,
            history=history
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching signal for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/signal/forex/{from_currency}/{to_currency}", response_model=SignalHistory)
async def get_forex_signal(
    from_currency: str,
    to_currency: str,
    period: str = Query("2y", min_length=1),
    interval: str = Query("1d", min_length=1)
):
    """
    Get trading signals for a forex pair.
    
    Args:
        from_currency: Source currency (e.g., "ZAR")
        to_currency: Target currency (e.g., "USD")
        period: Data period (default: "2y")
        interval: Data interval (default: "1d")
    
    Returns:
        Current signal and 90-day history
    """
    try:
        # Check cache first
        ticker = f"{from_currency}{to_currency}"
        cache_key = get_cache_key(ticker, period, interval)
        df = get_cached_data(cache_key)
        
        if df is None:
            # Fetch fresh data
            df = fetch_forex(from_currency, to_currency, period=period, interval=interval)
            
            if df.empty:
                raise HTTPException(status_code=404, detail=f"Forex pair {ticker} not found")
            
            set_cache(cache_key, df)
        
        # Generate signals
        engine = SignalEngine(df)
        df_signals = engine.generate_signals()
        
        # Build history (last 90 rows)
        history = []
        for idx, row in df_signals.tail(90).iterrows():
            try:
                close_val = float(row['Close'])
                signal_val = row['signal']
                rsi_val = row['RSI_14']
                macd_val = row['MACD']
                
                signal_strength = 0.0
                if pd.notna(rsi_val):
                    signal_strength = float(rsi_val) / 100.0
                
                macd_float = None
                if pd.notna(macd_val):
                    macd_float = float(macd_val)
                
                rsi_float = None
                if pd.notna(rsi_val):
                    rsi_float = float(rsi_val)
                
                history.append({
                    'date': idx.isoformat(),
                    'close': close_val,
                    'signal': signal_val if signal_val is not None else None,
                    'signal_strength': signal_strength,
                    'rsi': rsi_float,
                    'macd': macd_float,
                })
            except (ValueError, TypeError, KeyError) as e:
                logger.warning(f"Error building history row: {str(e)}")
                continue
        
        # Get current signal (last row)
        current_row = df_signals.iloc[-1]
        current_signal = None
        signal_value = current_row.get('signal')
        # Check if signal_value is not null/None
        if signal_value is not None and str(signal_value).strip() != 'None':
            try:
                rsi_current = current_row.get('RSI_14')
                signal_strength = 0.0
                if pd.notna(rsi_current):
                    signal_strength = float(rsi_current) / 100.0
                
                current_signal = Signal(
                    ticker=f"{from_currency}/{to_currency}",
                    timestamp=df_signals.index[-1].isoformat(),
                    close=float(current_row['Close']),
                    signal=str(signal_value),
                    signal_strength=signal_strength,
                    rsi=float(rsi_current) if pd.notna(rsi_current) else None,
                    macd=float(current_row['MACD']) if pd.notna(current_row.get('MACD')) else None,
                )
            except (ValueError, TypeError):
                pass
        
        return SignalHistory(
            ticker=f"{from_currency}/{to_currency}",
            period=period,
            current_signal=current_signal,
            history=history
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching signal for {from_currency}/{to_currency}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backtest/{ticker}", response_model=BacktestStats)
async def backtest_stock(
    ticker: str,
    period: str = Query("2y", min_length=1),
    initial_capital: float = Query(100000.0, gt=0),
    position_size_pct: float = Query(0.02, gt=0, lt=1),
    stop_loss_pct: float = Query(0.05, gt=0, lt=1),
    take_profit_pct: float = Query(0.10, gt=0, lt=1)
):
    """
    Run backtest for a JSE stock.
    
    Args:
        ticker: Stock ticker (e.g., "NPN")
        period: Data period (default: "2y")
        initial_capital: Starting capital in ZAR (default: 100000)
        position_size_pct: Risk per trade (default: 0.02 = 2%)
        stop_loss_pct: Stop loss percentage (default: 0.05 = 5%)
        take_profit_pct: Take profit percentage (default: 0.10 = 10%)
    
    Returns:
        Backtest statistics
    """
    try:
        # Fetch data
        df = fetch_jse_stock(ticker, period=period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Ticker {ticker} not found")
        
        # Generate signals
        engine = SignalEngine(df)
        df_signals = engine.generate_signals()
        
        # Run backtest
        backtester = Backtester(
            df_signals,
            initial_capital=initial_capital,
            position_size_pct=position_size_pct,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct
        )
        backtester.run()
        stats = backtester.get_stats()
        
        return BacktestStats(
            ticker=f"{ticker}.JO",
            period=period,
            initial_capital=initial_capital,
            final_value=backtester.portfolio_value,
            total_return_pct=stats['total_return_pct'],
            total_trades=stats['total_trades'],
            win_rate=stats['win_rate'],
            avg_win_pct=stats['avg_win_pct'],
            avg_loss_pct=stats['avg_loss_pct'],
            max_drawdown_pct=stats['max_drawdown_pct'],
            sharpe_ratio=stats['sharpe_ratio'],
            best_trade_pct=stats['best_trade_pct'],
            worst_trade_pct=stats['worst_trade_pct'],
            days_tested=stats['days_tested']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest for {ticker}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/backtest/forex/{from_currency}/{to_currency}", response_model=BacktestStats)
async def backtest_forex(
    from_currency: str,
    to_currency: str,
    period: str = Query("2y", min_length=1),
    initial_capital: float = Query(100000.0, gt=0),
    position_size_pct: float = Query(0.02, gt=0, lt=1),
    stop_loss_pct: float = Query(0.05, gt=0, lt=1),
    take_profit_pct: float = Query(0.10, gt=0, lt=1)
):
    """
    Run backtest for a forex pair.
    
    Args:
        from_currency: Source currency (e.g., "ZAR")
        to_currency: Target currency (e.g., "USD")
        period: Data period (default: "2y")
        initial_capital: Starting capital in ZAR (default: 100000)
        position_size_pct: Risk per trade (default: 0.02 = 2%)
        stop_loss_pct: Stop loss percentage (default: 0.05 = 5%)
        take_profit_pct: Take profit percentage (default: 0.10 = 10%)
    
    Returns:
        Backtest statistics
    """
    try:
        # Fetch data
        df = fetch_forex(from_currency, to_currency, period=period)
        
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Forex pair {from_currency}/{to_currency} not found")
        
        # Generate signals
        engine = SignalEngine(df)
        df_signals = engine.generate_signals()
        
        # Run backtest
        backtester = Backtester(
            df_signals,
            initial_capital=initial_capital,
            position_size_pct=position_size_pct,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct
        )
        backtester.run()
        stats = backtester.get_stats()
        
        return BacktestStats(
            ticker=f"{from_currency}/{to_currency}",
            period=period,
            initial_capital=initial_capital,
            final_value=backtester.portfolio_value,
            total_return_pct=stats['total_return_pct'],
            total_trades=stats['total_trades'],
            win_rate=stats['win_rate'],
            avg_win_pct=stats['avg_win_pct'],
            avg_loss_pct=stats['avg_loss_pct'],
            max_drawdown_pct=stats['max_drawdown_pct'],
            sharpe_ratio=stats['sharpe_ratio'],
            best_trade_pct=stats['best_trade_pct'],
            worst_trade_pct=stats['worst_trade_pct'],
            days_tested=stats['days_tested']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running backtest for {from_currency}/{to_currency}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
