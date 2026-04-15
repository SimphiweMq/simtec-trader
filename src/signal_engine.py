"""Signal engine module for generating trading signals."""

import pandas as pd
import numpy as np
import ta
import logging

logger = logging.getLogger(__name__)


class SignalEngine:
    """
    Trading signal engine that computes technical indicators and generates trading signals.
    Takes OHLCV data and enriches it with indicators for signal generation.
    """
    
    def __init__(self, df: pd.DataFrame):
        """
        Initialize the SignalEngine with OHLCV data.
        
        Args:
            df: DataFrame with columns [Open, High, Low, Close, Volume] and Date as index
        """
        self.df = df.copy()
        self.logger = logging.getLogger(f"{__name__}.SignalEngine")
    
    def compute_indicators(self) -> pd.DataFrame:
        """
        Compute technical indicators and add them to the DataFrame.
        
        Adds the following columns:
        - SMA_20, SMA_50: Simple moving averages
        - EMA_20: Exponential moving average
        - RSI_14: Relative Strength Index (14-period)
        - MACD: MACD line
        - MACD_signal: MACD signal line
        - BB_upper, BB_middle, BB_lower: Bollinger Bands (20-period, 2 std dev)
        - ATR_14: Average True Range (14-period)
        - Volume_MA_20: 20-period volume moving average
        
        Returns:
            DataFrame with all indicators appended
        """
        try:
            self.logger.info("Computing technical indicators...")
            
            # Ensure Close is a Series
            close = self.df['Close'].squeeze()
            
            # Simple Moving Averages
            self.df['SMA_20'] = close.rolling(window=20).mean()
            self.df['SMA_50'] = close.rolling(window=50).mean()
            
            # Exponential Moving Average
            self.df['EMA_20'] = close.ewm(span=20, adjust=False).mean()
            
            # RSI (14-period) - ensure close is a Series
            try:
                rsi = ta.momentum.RSIIndicator(close=close, window=14)
                self.df['RSI_14'] = rsi.rsi()
            except Exception as e:
                self.logger.warning(f"RSI computation failed: {str(e)}, using NaN")
                self.df['RSI_14'] = np.nan
            
            # MACD
            try:
                macd = ta.trend.MACD(close=close)
                self.df['MACD'] = macd.macd()
                self.df['MACD_signal'] = macd.macd_signal()
            except Exception as e:
                self.logger.warning(f"MACD computation failed: {str(e)}, using NaN")
                self.df['MACD'] = np.nan
                self.df['MACD_signal'] = np.nan
            
            # Bollinger Bands
            try:
                bb = ta.volatility.BollingerBands(close=close, window=20, window_dev=2)
                self.df['BB_upper'] = bb.bollinger_hband()
                self.df['BB_middle'] = bb.bollinger_mavg()
                self.df['BB_lower'] = bb.bollinger_lband()
            except Exception as e:
                self.logger.warning(f"Bollinger Bands computation failed: {str(e)}, using NaN")
                self.df['BB_upper'] = np.nan
                self.df['BB_middle'] = np.nan
                self.df['BB_lower'] = np.nan
            
            # Average True Range
            try:
                high = self.df['High'].squeeze()
                low = self.df['Low'].squeeze()
                atr = ta.volatility.AverageTrueRange(
                    high=high,
                    low=low,
                    close=close,
                    window=14
                )
                self.df['ATR_14'] = atr.average_true_range()
            except Exception as e:
                self.logger.warning(f"ATR computation failed: {str(e)}, using NaN")
                self.df['ATR_14'] = np.nan
            
            # Volume Moving Average
            volume = self.df['Volume'].squeeze()
            self.df['Volume_MA_20'] = volume.rolling(window=20).mean()
            
            self.logger.info(f"Successfully computed indicators for {len(self.df)} rows")
            return self.df
        
        except Exception as e:
            self.logger.error(f"Error computing indicators: {str(e)}")
            return self.df
    
    def compute_gap_score(self) -> pd.Series:
        """
        Compute gap score: days since Close was at its 20-day high.
        
        For each row, calculates how many bars have passed since the Close
        was at its maximum value in the rolling 20-day window (including current day).
        A higher score indicates the price has moved further away from its recent high,
        useful for identifying momentum fading and potential reversals.
        
        Gap score of 0 means today is at the 20-day high.
        Gap score of N means the high occurred N bars ago.
        
        Returns:
            Series with gap scores (NaN for rows with insufficient data)
        """
        try:
            self.logger.info("Computing gap scores...")
            gap_scores = []
            close_values = self.df['Close'].values
            
            for i in range(len(self.df)):
                if i < 19:  # Not enough data for full 20-day window
                    gap_scores.append(np.nan)
                else:
                    # Look at the rolling 20-day window (including current bar)
                    window = close_values[i - 19:i + 1]
                    max_close = np.max(window)
                    
                    # Find how many bars ago the max occurred
                    # Iterate backwards from current bar
                    for j in range(len(window) - 1, -1, -1):
                        if window[j] == max_close:
                            gap = (len(window) - 1) - j
                            gap_scores.append(gap)
                            break
            
            gap_series = pd.Series(gap_scores, index=self.df.index)
            valid_count = gap_series.notna().sum()
            self.logger.info(f"Successfully computed gap scores for {valid_count} rows")
            return gap_series
        
        except Exception as e:
            self.logger.error(f"Error computing gap scores: {str(e)}")
            return pd.Series(np.nan, index=self.df.index)
    
    def generate_signals(self) -> pd.DataFrame:
        """
        Generate trading signals based on computed indicators.
        
        Signal rules:
        - BUY: Close > SMA_50 AND RSI < 70 AND gap_score > 10 (moved away from high)
        - SELL: Close < SMA_20 OR RSI > 80
        
        First computes all indicators and gap scores if not already present.
        
        Returns:
            DataFrame with added 'signal' column (values: 'BUY', 'SELL', or None)
        """
        try:
            self.logger.info("Generating trading signals...")
            
            # Ensure indicators are computed
            if 'SMA_20' not in self.df.columns:
                self.compute_indicators()
            
            # Compute gap score
            gap_scores = self.compute_gap_score()
            self.df['gap_score'] = gap_scores
            
            # Initialize signal column
            self.df['signal'] = None
            
            # Fill NaN values in RSI and other indicators with forward/backward fill
            self.df['RSI_14'] = self.df['RSI_14'].bfill().ffill()
            self.df['SMA_50'] = self.df['SMA_50'].bfill().ffill()
            self.df['SMA_20'] = self.df['SMA_20'].bfill().ffill()
            self.df['gap_score'] = self.df['gap_score'].fillna(0)
            
            # Get series for conditions (reset index to ensure alignment)
            close_vals = self.df['Close'].values.flatten()
            sma_50_vals = self.df['SMA_50'].values.flatten()
            sma_20_vals = self.df['SMA_20'].values.flatten()
            rsi_vals = self.df['RSI_14'].values.flatten()
            gap_vals = self.df['gap_score'].values.flatten()
            
            # Generate BUY signals using numpy arrays
            # BUY: Price above 20-day MA (momentum confirmation), RSI not overbought (<70), some distance from high
            buy_condition = (
                (close_vals > sma_20_vals) &
                (rsi_vals < 70) &
                (gap_vals > 2)
            )
            self.df.loc[pd.Series(buy_condition, index=self.df.index), 'signal'] = 'BUY'
            
            # Generate SELL signals using numpy arrays
            # SELL: Price below 20-day MA (breaking support) OR RSI overbought (>80)
            sell_condition = (
                (close_vals < sma_20_vals) |
                (rsi_vals > 80)
            )
            self.df.loc[pd.Series(sell_condition, index=self.df.index), 'signal'] = 'SELL'
            
            signal_count = (self.df['signal'].notna()).sum()
            self.logger.info(f"Generated signals: {signal_count} signal events")
            return self.df
        
        except Exception as e:
            self.logger.error(f"Error generating signals: {str(e)}")
            return self.df


if __name__ == "__main__":
    # Test the SignalEngine
    from data_fetcher import fetch_jse_stock
    
    print("=" * 60)
    print("Testing Signal Engine Module")
    print("=" * 60)
    
    # Fetch sample data
    print("\nFetching sample data (Naspers, 1 year)...")
    df = fetch_jse_stock("NPN", period="1y")
    
    if not df.empty:
        print(f"Data loaded: {len(df)} rows")
        
        # Initialize engine and compute indicators
        engine = SignalEngine(df)
        df_with_indicators = engine.compute_indicators()
        
        print("\nIndicators computed successfully!")
        print(f"DataFrame shape: {df_with_indicators.shape}")
        print("\nIndicator columns added:")
        indicator_cols = ['SMA_20', 'SMA_50', 'EMA_20', 'RSI_14', 'MACD', 'MACD_signal',
                         'BB_upper', 'BB_middle', 'BB_lower', 'ATR_14', 'Volume_MA_20']
        for col in indicator_cols:
            if col in df_with_indicators.columns:
                print(f"  ✓ {col}")
        
        # Compute gap scores
        print("\nComputing gap scores...")
        gap_scores = engine.compute_gap_score()
        print(f"Gap scores computed: {gap_scores.notna().sum()} valid values")
        
        # Display last 5 rows with indicators
        print("\nLast 5 rows with indicators:")
        display_cols = ['Close', 'SMA_20', 'SMA_50', 'EMA_20', 'RSI_14', 'BB_upper', 'BB_lower']
        print(df_with_indicators[display_cols].tail())
        
        print("\nLast 5 gap scores:")
        print(gap_scores.tail())
    else:
        print("Failed to load data")
    
    print("\n" + "=" * 60)
    print("Tests Complete")
    print("=" * 60)
