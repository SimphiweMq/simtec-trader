"""Backtester module for evaluating trading strategies."""

import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class Backtester:
    """
    Backtesting engine that replays trading signals against historical OHLCV data
    and measures strategy performance metrics.
    """
    
    def __init__(
        self,
        df: pd.DataFrame,
        initial_capital: float = 100000.0,
        position_size_pct: float = 0.02,
        stop_loss_pct: float = 0.05,
        take_profit_pct: float = 0.10
    ):
        """
        Initialize the Backtester.
        
        Args:
            df: DataFrame with OHLCV data and 'signal' column (output from SignalEngine.generate_signals())
            initial_capital: Starting capital in ZAR (default: 100,000)
            position_size_pct: Risk percentage per trade (default: 0.02 = 2% of capital)
            stop_loss_pct: Exit if price drops this % from entry (default: 0.05 = 5%)
            take_profit_pct: Exit if price gains this % from entry (default: 0.10 = 10%)
        """
        self.df = df.copy()
        self.initial_capital = initial_capital
        self.position_size_pct = position_size_pct
        self.stop_loss_pct = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        
        self.portfolio_value = initial_capital
        self.cash = initial_capital
        self.shares_held = 0
        self.entry_price = None
        
        self.trade_log = []  # List of completed trades: {entry_date, exit_date, entry_price, exit_price, shares, return_pct}
        self.portfolio_history = []
        
        self.logger = logging.getLogger(f"{__name__}.Backtester")
    
    def run(self) -> pd.DataFrame:
        """
        Run the backtest by iterating through historical data row-by-row.
        
        Rules:
        - No lookahead: signals on row N can only trigger trades on row N+1 open price
        - BUY signal: buy position_size_pct of current capital at next open (if not in position)
        - SELL signal OR stop loss OR take profit: exit full position at next open
        
        Returns:
            DataFrame with added columns: portfolio_value, cash, shares_held, trade_action
        """
        try:
            self.logger.info("Starting backtest...")
            
            # Initialize tracking columns
            self.df['portfolio_value'] = 0.0
            self.df['cash'] = 0.0
            self.df['shares_held'] = 0.0
            self.df['trade_action'] = None
            
            pending_buy_signal = False
            pending_sell_signal = False
            
            # Iterate through each row
            for i in range(len(self.df)):
                current_row = self.df.iloc[i]
                current_price = current_row['Open']  # Use next open for execution
                
                # Check for exit conditions if currently in a position
                if self.shares_held > 0:
                    # Check stop loss
                    loss_pct = (current_price - self.entry_price) / self.entry_price
                    if loss_pct <= -self.stop_loss_pct:
                        # Exit on stop loss
                        exit_value = self.shares_held * current_price
                        profit = exit_value - (self.shares_held * self.entry_price)
                        self.cash += exit_value
                        
                        trade_return_pct = (current_price - self.entry_price) / self.entry_price * 100
                        self.trade_log.append({
                            'entry_date': self.df.index[i - 1] if i > 0 else self.df.index[0],
                            'exit_date': self.df.index[i],
                            'entry_price': self.entry_price,
                            'exit_price': current_price,
                            'shares': self.shares_held,
                            'return_pct': trade_return_pct,
                            'reason': 'Stop Loss'
                        })
                        
                        self.shares_held = 0
                        self.entry_price = None
                        self.df.loc[self.df.index[i], 'trade_action'] = 'EXIT (SL)'
                    
                    # Check take profit
                    elif loss_pct >= self.take_profit_pct:
                        # Exit on take profit
                        exit_value = self.shares_held * current_price
                        profit = exit_value - (self.shares_held * self.entry_price)
                        self.cash += exit_value
                        
                        trade_return_pct = (current_price - self.entry_price) / self.entry_price * 100
                        self.trade_log.append({
                            'entry_date': self.df.index[i - 1] if i > 0 else self.df.index[0],
                            'exit_date': self.df.index[i],
                            'entry_price': self.entry_price,
                            'exit_price': current_price,
                            'shares': self.shares_held,
                            'return_pct': trade_return_pct,
                            'reason': 'Take Profit'
                        })
                        
                        self.shares_held = 0
                        self.entry_price = None
                        self.df.loc[self.df.index[i], 'trade_action'] = 'EXIT (TP)'
                
                # Check for SELL signal (exit if in position)
                if current_row.get('signal') == 'SELL' and self.shares_held > 0:
                    pending_sell_signal = True
                
                # Execute pending sell on next row's open
                if pending_sell_signal and i + 1 < len(self.df):
                    next_price = self.df.iloc[i + 1]['Open']
                    exit_value = self.shares_held * next_price
                    profit = exit_value - (self.shares_held * self.entry_price)
                    self.cash += exit_value
                    
                    trade_return_pct = (next_price - self.entry_price) / self.entry_price * 100
                    self.trade_log.append({
                        'entry_date': self.df.index[i - 1] if i > 0 else self.df.index[0],
                        'exit_date': self.df.index[i + 1],
                        'entry_price': self.entry_price,
                        'exit_price': next_price,
                        'shares': self.shares_held,
                        'return_pct': trade_return_pct,
                        'reason': 'SELL Signal'
                    })
                    
                    self.shares_held = 0
                    self.entry_price = None
                    self.df.loc[self.df.index[i + 1], 'trade_action'] = 'EXIT (SIG)'
                    pending_sell_signal = False
                
                # Check for BUY signal (enter if not in position)
                if current_row.get('signal') == 'BUY' and self.shares_held == 0:
                    pending_buy_signal = True
                
                # Execute pending buy on next row's open
                if pending_buy_signal and i + 1 < len(self.df):
                    next_price = self.df.iloc[i + 1]['Open']
                    trade_capital = self.cash * self.position_size_pct
                    self.shares_held = trade_capital / next_price
                    self.cash -= trade_capital
                    self.entry_price = next_price
                    
                    self.df.loc[self.df.index[i + 1], 'trade_action'] = 'ENTRY'
                    pending_buy_signal = False
                
                # Update portfolio value at current row
                current_stock_value = self.shares_held * current_price if self.shares_held > 0 else 0
                self.portfolio_value = self.cash + current_stock_value
                
                # Store in tracking columns
                self.df.loc[self.df.index[i], 'portfolio_value'] = self.portfolio_value
                self.df.loc[self.df.index[i], 'cash'] = self.cash
                self.df.loc[self.df.index[i], 'shares_held'] = self.shares_held
                self.portfolio_history.append(self.portfolio_value)
            
            self.logger.info(f"Backtest complete. Final portfolio value: R{self.portfolio_value:,.2f}")
            return self.df
        
        except Exception as e:
            self.logger.error(f"Error running backtest: {str(e)}")
            return self.df
    
    def get_stats(self) -> dict:
        """
        Calculate backtest performance statistics.
        
        Returns:
            Dictionary with metrics:
            - total_return_pct: percentage gain/loss
            - total_trades: number of completed trades
            - win_rate: percentage of profitable trades
            - avg_win_pct: average profit on winning trades
            - avg_loss_pct: average loss on losing trades
            - max_drawdown_pct: largest peak-to-trough drop
            - sharpe_ratio: annualized Sharpe ratio (risk-free = 7.0% for SA)
            - best_trade_pct: best single trade return
            - worst_trade_pct: worst single trade return
            - days_tested: calendar days in backtest
        """
        try:
            # Basic metrics
            total_return_pct = ((self.portfolio_value - self.initial_capital) / self.initial_capital) * 100
            total_trades = len(self.trade_log)
            
            # Win rate
            if total_trades > 0:
                winning_trades = [t for t in self.trade_log if t['return_pct'] > 0]
                win_rate = (len(winning_trades) / total_trades) * 100
                
                # Average win/loss
                if len(winning_trades) > 0:
                    avg_win_pct = np.mean([t['return_pct'] for t in winning_trades])
                else:
                    avg_win_pct = 0
                
                losing_trades = [t for t in self.trade_log if t['return_pct'] < 0]
                if len(losing_trades) > 0:
                    avg_loss_pct = np.mean([t['return_pct'] for t in losing_trades])
                else:
                    avg_loss_pct = 0
                
                best_trade_pct = max([t['return_pct'] for t in self.trade_log])
                worst_trade_pct = min([t['return_pct'] for t in self.trade_log])
            else:
                win_rate = 0
                avg_win_pct = 0
                avg_loss_pct = 0
                best_trade_pct = 0
                worst_trade_pct = 0
            
            # Max drawdown
            portfolio_array = np.array(self.portfolio_history)
            running_max = np.maximum.accumulate(portfolio_array)
            drawdown = (portfolio_array - running_max) / running_max
            max_drawdown_pct = np.min(drawdown) * 100 if len(drawdown) > 0 else 0
            
            # Sharpe ratio (annualized)
            if len(self.portfolio_history) > 1:
                returns = np.diff(self.portfolio_history) / self.portfolio_history[:-1]
                daily_return = np.mean(returns)
                daily_volatility = np.std(returns)
                
                # Annualize (252 trading days)
                annual_return = daily_return * 252
                annual_volatility = daily_volatility * np.sqrt(252)
                
                risk_free_rate = 0.07  # 7% for SA
                sharpe_ratio = (annual_return - risk_free_rate) / annual_volatility if annual_volatility > 0 else 0
            else:
                sharpe_ratio = 0
            
            # Days tested
            if len(self.df) > 0:
                days_tested = (self.df.index[-1] - self.df.index[0]).days
            else:
                days_tested = 0
            
            return {
                'total_return_pct': total_return_pct,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'avg_win_pct': avg_win_pct,
                'avg_loss_pct': avg_loss_pct,
                'max_drawdown_pct': max_drawdown_pct,
                'sharpe_ratio': sharpe_ratio,
                'best_trade_pct': best_trade_pct,
                'worst_trade_pct': worst_trade_pct,
                'days_tested': days_tested
            }
        
        except Exception as e:
            self.logger.error(f"Error calculating stats: {str(e)}")
            return {}
    
    def print_report(self, ticker: str = "UNKNOWN"):
        """
        Print a formatted backtest report.
        
        Args:
            ticker: Security ticker symbol
        """
        stats = self.get_stats()
        
        if not stats:
            print("Error: Could not generate report")
            return
        
        start_date = self.df.index[0].strftime("%Y-%m-%d") if len(self.df) > 0 else "N/A"
        end_date = self.df.index[-1].strftime("%Y-%m-%d") if len(self.df) > 0 else "N/A"
        
        print("\n" + "─" * 50)
        print(f"SIMTEK BACKTESTER — {ticker}")
        print(f"Period: {start_date} to {end_date}")
        print("─" * 50)
        print(f"Initial capital:     R{self.initial_capital:>12,.2f}")
        print(f"Final value:         R{self.portfolio_value:>12,.2f}")
        print(f"Total return:        {stats['total_return_pct']:>12.2f}%")
        print(f"Total trades:        {stats['total_trades']:>12.0f}")
        print(f"Win rate:            {stats['win_rate']:>12.2f}%")
        print(f"Avg win:             {stats['avg_win_pct']:>12.2f}%")
        print(f"Avg loss:            {stats['avg_loss_pct']:>12.2f}%")
        print(f"Best trade:          {stats['best_trade_pct']:>12.2f}%")
        print(f"Worst trade:         {stats['worst_trade_pct']:>12.2f}%")
        print(f"Max drawdown:        {stats['max_drawdown_pct']:>12.2f}%")
        print(f"Sharpe ratio:        {stats['sharpe_ratio']:>12.2f}")
        print("─" * 50 + "\n")


if __name__ == "__main__":
    from data_fetcher import fetch_jse_stock, fetch_forex
    from signal_engine import SignalEngine
    
    print("=" * 60)
    print("Testing Backtester Module")
    print("=" * 60)
    
    # Test 1: Backtest NPN.JO
    print("\n[1] Backtesting NPN.JO (2 years)...")
    npn_df = fetch_jse_stock("NPN", period="2y")
    
    if not npn_df.empty:
        engine = SignalEngine(npn_df)
        signaled_df = engine.generate_signals()
        
        backtester = Backtester(signaled_df, initial_capital=100000.0)
        result_df = backtester.run()
        backtester.print_report("NPN.JO")
    else:
        print("Failed to fetch NPN data")
    
    # Test 2: Backtest ZARUSD
    print("\n[2] Backtesting ZARUSD=X (2 years)...")
    zar_df = fetch_forex("ZAR", "USD", period="2y")
    
    if not zar_df.empty:
        engine = SignalEngine(zar_df)
        signaled_df = engine.generate_signals()
        
        backtester = Backtester(signaled_df, initial_capital=100000.0)
        result_df = backtester.run()
        backtester.print_report("ZARUSD=X")
    else:
        print("Failed to fetch ZARUSD data")
    
    print("=" * 60)
    print("Backtest Tests Complete")
    print("=" * 60)
