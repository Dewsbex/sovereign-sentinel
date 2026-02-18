from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"

class TradeSignal(BaseModel):
    """
    Standard signal emitted by a Strategy Agent.
    """
    signal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    strategy_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    amount: float
    price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    reason: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Metadata for drift analysis
    market_state_snapshot: Dict[str, Any] = Field(default_factory=dict) 
    # e.g., {"rsi": 75, "atr": 120, "price": 50000}

class MarketData(BaseModel):
    """
    Standard market data packet published by the Manager.
    """
    symbol: str
    price: float
    volume: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = "kraken"

class AuditLogEntry(BaseModel):
    """
    Comprehensive audit log for debugging and drift detection.
    """
    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    component: str  # "manager", "orb_agent", "janitor"
    level: str = "INFO" # INFO, WARNING, ERROR, CRITICAL
    action: str
    details: Dict[str, Any]
    
    # Crucial for drift detection
    strategy_id: Optional[str] = None
    market_context: Optional[Dict[str, Any]] = None

class StrategyHealthReport(BaseModel):
    """
    Daily health check report for a strategy.
    """
    strategy_id: str
    date: str
    total_trades: int
    win_rate: float
    profit_loss: float
    benchmark_comparison: float # e.g. vs BTC/USD buy-and-hold
    drift_detected: bool
    drift_reason: Optional[str] = None
