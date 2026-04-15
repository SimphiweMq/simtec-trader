"""Database service layer for signal and trade management."""

import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
import models

logger = logging.getLogger(__name__)


class SignalService:
    """Service for managing signals in the database."""
    
    @staticmethod
    def create_signal(
        db: Session,
        ticker: str,
        date: datetime,
        signal_type: str,
        close_price: float,
        rsi: Optional[float] = None,
        sma_20: Optional[float] = None,
        sma_50: Optional[float] = None,
        macd: Optional[float] = None,
        gap_score: Optional[float] = None,
        signal_strength: Optional[float] = None,
        period: str = "1d",
        interval: str = "1d",
    ) -> models.Signal:
        """Create and save a new signal to the database."""
        try:
            signal = models.Signal(
                ticker=ticker,
                date=date,
                signal_type=signal_type,
                close_price=close_price,
                rsi=rsi,
                sma_20=sma_20,
                sma_50=sma_50,
                macd=macd,
                gap_score=gap_score,
                signal_strength=signal_strength,
                period=period,
                interval=interval,
            )
            db.add(signal)
            db.commit()
            db.refresh(signal)
            logger.info(f"Signal saved: {ticker} {signal_type} at {date}")
            return signal
        except Exception as e:
            logger.error(f"Failed to create signal: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def get_signals_by_ticker(
        db: Session,
        ticker: str,
        limit: int = 100,
        signal_type: Optional[str] = None,
    ) -> List[models.Signal]:
        """Get recent signals for a ticker."""
        query = db.query(models.Signal).filter(models.Signal.ticker == ticker)
        if signal_type:
            query = query.filter(models.Signal.signal_type == signal_type)
        return query.order_by(desc(models.Signal.date)).limit(limit).all()
    
    @staticmethod
    def get_signal_count(db: Session, ticker: str) -> int:
        """Get total number of signals for a ticker."""
        return db.query(models.Signal).filter(models.Signal.ticker == ticker).count()
    
    @staticmethod
    def batch_create_signals(
        db: Session,
        signals_data: List[dict],
    ) -> int:
        """
        Batch create multiple signals from a list of signal data dictionaries.
        
        Args:
            db: Database session
            signals_data: List of dicts with keys: ticker, date, signal_type, close_price, etc.
        
        Returns:
            Number of signals created
        """
        try:
            signal_objects = [models.Signal(**data) for data in signals_data]
            db.add_all(signal_objects)
            db.commit()
            logger.info(f"Batch created {len(signal_objects)} signals")
            return len(signal_objects)
        except Exception as e:
            logger.error(f"Failed to batch create signals: {str(e)}")
            db.rollback()
            raise


class TradeService:
    """Service for managing trades in the database."""
    
    @staticmethod
    def create_trade(
        db: Session,
        ticker: str,
        entry_date: datetime,
        entry_price: float,
        position_size: float,
        entry_signal_id: Optional[int] = None,
    ) -> models.Trade:
        """Create a new open trade."""
        try:
            trade = models.Trade(
                ticker=ticker,
                entry_date=entry_date,
                entry_price=entry_price,
                position_size=position_size,
                entry_signal_id=entry_signal_id,
                is_closed=False,
            )
            db.add(trade)
            db.commit()
            db.refresh(trade)
            logger.info(f"Trade opened: {ticker} @ {entry_price} ({position_size} units)")
            return trade
        except Exception as e:
            logger.error(f"Failed to create trade: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def close_trade(
        db: Session,
        trade_id: int,
        exit_price: float,
        exit_date: datetime,
        exit_reason: str = "SIGNAL",
        exit_signal_id: Optional[int] = None,
    ) -> models.Trade:
        """Close an open trade and calculate P&L."""
        try:
            trade = db.query(models.Trade).filter(models.Trade.id == trade_id).first()
            if not trade:
                raise ValueError(f"Trade {trade_id} not found")
            
            trade.exit_price = exit_price
            trade.exit_date = exit_date
            trade.exit_reason = exit_reason
            trade.exit_signal_id = exit_signal_id
            trade.is_closed = True
            
            # Calculate P&L
            trade.pnl_amount = (exit_price - trade.entry_price) * trade.position_size
            trade.pnl_pct = ((exit_price - trade.entry_price) / trade.entry_price) * 100
            
            db.commit()
            db.refresh(trade)
            logger.info(
                f"Trade closed: {trade.ticker} PnL: {trade.pnl_pct:.2f}% "
                f"(${trade.pnl_amount:.2f})"
            )
            return trade
        except Exception as e:
            logger.error(f"Failed to close trade: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def get_open_trades(db: Session, ticker: Optional[str] = None) -> List[models.Trade]:
        """Get all open trades, optionally filtered by ticker."""
        query = db.query(models.Trade).filter(models.Trade.is_closed == False)
        if ticker:
            query = query.filter(models.Trade.ticker == ticker)
        return query.order_by(models.Trade.entry_date).all()
    
    @staticmethod
    def get_closed_trades(
        db: Session,
        ticker: Optional[str] = None,
        limit: int = 100,
    ) -> List[models.Trade]:
        """Get closed trades, optionally filtered by ticker."""
        query = db.query(models.Trade).filter(models.Trade.is_closed == True)
        if ticker:
            query = query.filter(models.Trade.ticker == ticker)
        return query.order_by(desc(models.Trade.exit_date)).limit(limit).all()
    
    @staticmethod
    def get_trade_stats(db: Session, ticker: Optional[str] = None) -> dict:
        """Calculate trade statistics."""
        query = db.query(models.Trade).filter(models.Trade.is_closed == True)
        if ticker:
            query = query.filter(models.Trade.ticker == ticker)
        
        trades = query.all()
        if not trades:
            return {
                "total_trades": 0,
                "winning_trades": 0,
                "losing_trades": 0,
                "win_rate": 0,
                "avg_win_pct": 0,
                "avg_loss_pct": 0,
                "total_return_pct": 0,
            }
        
        winning = [t for t in trades if t.pnl_pct and t.pnl_pct > 0]
        losing = [t for t in trades if t.pnl_pct and t.pnl_pct < 0]
        
        total_return = sum(t.pnl_pct for t in trades if t.pnl_pct)
        avg_win = sum(t.pnl_pct for t in winning) / len(winning) if winning else 0
        avg_loss = sum(t.pnl_pct for t in losing) / len(losing) if losing else 0
        
        return {
            "total_trades": len(trades),
            "winning_trades": len(winning),
            "losing_trades": len(losing),
            "win_rate": (len(winning) / len(trades) * 100) if trades else 0,
            "avg_win_pct": avg_win,
            "avg_loss_pct": avg_loss,
            "total_return_pct": total_return,
        }


class PerformanceService:
    """Service for managing performance metrics."""
    
    @staticmethod
    def create_or_update_metric(
        db: Session,
        ticker: str,
        metric_date: datetime,
        **kwargs
    ) -> models.PerformanceMetric:
        """Create or update daily performance metrics."""
        try:
            metric = (
                db.query(models.PerformanceMetric)
                .filter(
                    and_(
                        models.PerformanceMetric.ticker == ticker,
                        models.PerformanceMetric.metric_date == metric_date,
                    )
                )
                .first()
            )
            
            if not metric:
                metric = models.PerformanceMetric(
                    ticker=ticker,
                    metric_date=metric_date,
                    **kwargs
                )
                db.add(metric)
            else:
                for key, value in kwargs.items():
                    if hasattr(metric, key):
                        setattr(metric, key, value)
            
            db.commit()
            db.refresh(metric)
            logger.info(f"Performance metric upserted for {ticker} on {metric_date}")
            return metric
        except Exception as e:
            logger.error(f"Failed to create/update metric: {str(e)}")
            db.rollback()
            raise
    
    @staticmethod
    def get_latest_metrics(db: Session, ticker: str) -> Optional[models.PerformanceMetric]:
        """Get the latest performance metrics for a ticker."""
        return (
            db.query(models.PerformanceMetric)
            .filter(models.PerformanceMetric.ticker == ticker)
            .order_by(desc(models.PerformanceMetric.metric_date))
            .first()
        )
