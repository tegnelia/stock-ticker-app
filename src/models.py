"""Data models for the stock ticker application."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Stock:
    """Represents a stock with its current price information."""
    symbol: str
    name: str = ""
    price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    prev_close: float = 0.0  # Previous day's close price
    last_updated: Optional[datetime] = None
    error: Optional[str] = None
    history: list[float] = field(default_factory=list)  # Historical prices for chart

    @property
    def is_up(self) -> bool:
        return self.change > 0

    @property
    def is_down(self) -> bool:
        return self.change < 0

    @property
    def change_color(self) -> str:
        if self.change > 0:
            return "#4CAF50"  # Green
        elif self.change < 0:
            return "#F44336"  # Red
        return "#9E9E9E"  # Gray


# Refresh interval options (in seconds)
REFRESH_INTERVALS = {
    "1 min": 60,
    "3 min": 180,
    "5 min": 300,
    "10 min": 600,
}

# Chart period options
CHART_PERIODS = {
    "1 day": "1d",
    "1 week": "5d",
    "1 month": "1mo",
    "1 year": "1y",
    "5 year": "5y",
    "10 year": "10y",
    "All time": "max",
}


@dataclass
class AppConfig:
    """Application configuration."""
    watchlist: list[str] = field(default_factory=lambda: ["^DJI", "^IXIC", "^GSPC", "^NYA"])
    refresh_interval: int = 60  # seconds
    chart_period: str = "1mo"  # yfinance period string
    popup_position: tuple[int, int] = (100, 100)
    popup_size: tuple[int, int] = (320, 400)
    theme: str = "dark"
