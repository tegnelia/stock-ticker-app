"""Stock data fetching service using yfinance."""

from datetime import datetime

import yfinance as yf
from PySide6.QtCore import QObject, QThread, Signal, QTimer

from .models import Stock


class StockFetcher(QThread):
    """Background thread for fetching stock data."""

    finished = Signal(list)  # Emits list of Stock objects

    def __init__(self, symbols: list[str], chart_period: str = "1mo", parent=None):
        super().__init__(parent)
        self.symbols = symbols
        self.chart_period = chart_period

    def run(self):
        """Fetch stock data for all symbols."""
        stocks = []
        for symbol in self.symbols:
            stock = self._fetch_single(symbol)
            stocks.append(stock)
        self.finished.emit(stocks)

    def _fetch_single(self, symbol: str) -> Stock:
        """Fetch data for a single stock symbol."""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            # Get current price - try multiple fields
            price = info.get("regularMarketPrice") or info.get("currentPrice", 0)
            prev_close = info.get("regularMarketPreviousClose") or info.get("previousClose", 0)

            # Calculate change
            change = price - prev_close if prev_close else 0
            change_percent = (change / prev_close * 100) if prev_close else 0

            # Get name
            name = info.get("shortName") or info.get("longName") or symbol

            # Fetch historical data for chart
            history = self._fetch_history(ticker)

            return Stock(
                symbol=symbol,
                name=name,
                price=price,
                change=change,
                change_percent=change_percent,
                prev_close=prev_close,
                last_updated=datetime.now(),
                history=history,
            )
        except Exception as e:
            return Stock(
                symbol=symbol,
                error=str(e),
                last_updated=datetime.now(),
            )

    def _fetch_history(self, ticker) -> list[float]:
        """Fetch historical price data for charting."""
        try:
            # Determine interval based on period
            interval = "1d"
            if self.chart_period == "1d":
                interval = "5m"
            elif self.chart_period == "5d":
                interval = "15m"

            hist = ticker.history(period=self.chart_period, interval=interval)
            if hist.empty:
                return []

            # Return closing prices as list
            return hist["Close"].tolist()
        except Exception:
            return []


class StockService(QObject):
    """Service for managing stock data fetching and updates."""

    stocks_updated = Signal(list)  # Emits list of Stock objects

    def __init__(self, refresh_interval: int = 60, chart_period: str = "1mo", parent=None):
        super().__init__(parent)
        self.refresh_interval = refresh_interval
        self.chart_period = chart_period
        self.symbols: list[str] = []
        self._fetcher: StockFetcher | None = None

        # Setup auto-refresh timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)

    def set_symbols(self, symbols: list[str]) -> None:
        """Set the list of symbols to track."""
        self.symbols = symbols.copy()

    def add_symbol(self, symbol: str) -> None:
        """Add a symbol to track."""
        symbol = symbol.upper().strip()
        if symbol and symbol not in self.symbols:
            self.symbols.append(symbol)

    def remove_symbol(self, symbol: str) -> None:
        """Remove a symbol from tracking."""
        symbol = symbol.upper().strip()
        if symbol in self.symbols:
            self.symbols.remove(symbol)

    def start(self) -> None:
        """Start the stock service with auto-refresh."""
        self.refresh()
        self._timer.start(self.refresh_interval * 1000)

    def stop(self) -> None:
        """Stop the stock service."""
        self._timer.stop()
        if self._fetcher and self._fetcher.isRunning():
            self._fetcher.quit()
            self._fetcher.wait(2000)  # Wait max 2 seconds
            if self._fetcher.isRunning():
                self._fetcher.terminate()

    def refresh(self) -> None:
        """Trigger a manual refresh of stock data."""
        if self._fetcher and self._fetcher.isRunning():
            return  # Already fetching

        if not self.symbols:
            return

        self._fetcher = StockFetcher(self.symbols, self.chart_period, self)
        self._fetcher.finished.connect(self._on_fetch_complete)
        self._fetcher.start()

    def _on_fetch_complete(self, stocks: list[Stock]) -> None:
        """Handle completed stock fetch."""
        self.stocks_updated.emit(stocks)

    def set_refresh_interval(self, seconds: int) -> None:
        """Update the refresh interval."""
        self.refresh_interval = seconds
        if self._timer.isActive():
            self._timer.stop()
            self._timer.start(seconds * 1000)

    def set_chart_period(self, period: str) -> None:
        """Update the chart period."""
        self.chart_period = period
