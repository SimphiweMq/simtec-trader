"""Data fetcher module for retrieving market data."""

import pandas as pd
import yfinance as yf
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_jse_stock(ticker: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch OHLCV data for a JSE stock.
    
    Args:
        ticker: JSE stock ticker (e.g., "NPN" for Naspers). .JO suffix is added if not present.
        period: Data period (default: "2y")
        interval: Data interval (default: "1d")
    
    Returns:
        DataFrame with columns: Date, Open, High, Low, Close, Volume.
        Date is the index and timezone-naive. Returns empty DataFrame on error.
    """
    try:
        # Append .JO suffix if not already present
        if not ticker.endswith(".JO"):
            ticker = f"{ticker}.JO"
        
        logger.info(f"Fetching JSE stock data for {ticker}...")
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        
        if df.empty:
            logger.warning(f"No data returned for {ticker}")
            return pd.DataFrame()
        
        # Reset index to make Date a column, then convert to timezone-naive
        df.reset_index(inplace=True)
        if df['Date'].dt.tz is not None:
            df['Date'] = df['Date'].dt.tz_localize(None)
        df.set_index('Date', inplace=True)
        
        # Ensure only required columns
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        logger.info(f"Successfully fetched {len(df)} rows for {ticker}")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching JSE stock {ticker}: {str(e)}")
        return pd.DataFrame()


def fetch_forex(from_currency: str, to_currency: str, period: str = "2y", interval: str = "1d") -> pd.DataFrame:
    """
    Fetch forex pair data.
    
    Args:
        from_currency: Source currency (e.g., "ZAR")
        to_currency: Target currency (e.g., "USD")
        period: Data period (default: "2y")
        interval: Data interval (default: "1d")
    
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


def fetch_index(index_ticker: str = "^J203.JO", period: str = "2y") -> pd.DataFrame:
    """
    Fetch index data.
    
    Args:
        index_ticker: Index ticker (default: "^J203.JO" for FTSE/JSE All Share)
        period: Data period (default: "2y")
    
    Returns:
        DataFrame with columns: Date, Open, High, Low, Close, Volume.
        Date is the index and timezone-naive. Returns empty DataFrame on error.
    """
    try:
        logger.info(f"Fetching index data for {index_ticker}...")
        df = yf.download(index_ticker, period=period, interval="1d", progress=False)
        
        if df.empty:
            logger.warning(f"No data returned for {index_ticker}")
            return pd.DataFrame()
        
        # Reset index to make Date a column, then convert to timezone-naive
        df.reset_index(inplace=True)
        if df['Date'].dt.tz is not None:
            df['Date'] = df['Date'].dt.tz_localize(None)
        df.set_index('Date', inplace=True)
        
        # Ensure only required columns
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        
        logger.info(f"Successfully fetched {len(df)} rows for {index_ticker}")
        return df
    
    except Exception as e:
        logger.error(f"Error fetching index {index_ticker}: {str(e)}")
        return pd.DataFrame()


def get_available_jse_tickers() -> dict:
    """
    Get a hardcoded dictionary of common JSE Top 40 tickers and company names.
    
    Returns:
        Dictionary mapping ticker symbols to company names.
    """
    return {
        "NPN": "Naspers",
        "CPI": "Capitec",
        "SBK": "Standard Bank",
        "ABG": "Absa Group",
        "NED": "Nedbank",
        "FSR": "Firstrand",
        "SOL": "Sasol",
        "ANG": "AngloGold Ashanti",
        "BHP": "BHP Group",
        "GLN": "Glencore"
    }


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Data Fetcher Module")
    print("=" * 60)
    
    # Test 1: Fetch Naspers (NPN) for 1 year
    print("\n[1] Fetching Naspers (NPN) for 1 year...")
    npn_df = fetch_jse_stock("NPN", period="1y")
    print(f"Rows: {len(npn_df)}")
    print("\nHead:")
    print(npn_df.head())
    print("\nTail:")
    print(npn_df.tail())
    
    # Test 2: Fetch ZARUSD=X for 1 year
    print("\n" + "=" * 60)
    print("[2] Fetching ZARUSD forex data for 1 year...")
    zar_df = fetch_forex("ZAR", "USD", period="1y")
    print(f"Rows: {len(zar_df)}")
    print("\nHead:")
    print(zar_df.head())
    print("\nTail:")
    print(zar_df.tail())
    
    # Test 3: Fetch ALSI index for 1 year
    print("\n" + "=" * 60)
    print("[3] Fetching ALSI Index (^J203.JO) for 1 year...")
    alsi_df = fetch_index("^J203.JO", period="1y")
    print(f"Rows: {len(alsi_df)}")
    print("\nHead:")
    print(alsi_df.head())
    print("\nTail:")
    print(alsi_df.tail())
    
    print("\n" + "=" * 60)
    print("Tests Complete")
    print("=" * 60)
