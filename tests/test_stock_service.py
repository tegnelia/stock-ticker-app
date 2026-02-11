"""Tests for the stock data service."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtCore import QCoreApplication

from src.models import Stock
from src.stock_service import StockFetcher, StockService


class TestStockFetcher:
    """Tests for the StockFetcher thread."""

    def test_fetcher_creation(self, qapp):
        """Test creating a stock fetcher."""
        fetcher = StockFetcher(["AAPL", "GOOGL"])
        assert fetcher.symbols == ["AAPL", "GOOGL"]

    def test_fetch_single_success(self, qapp, mock_yfinance):
        """Test fetching a single stock successfully."""
        fetcher = StockFetcher(["AAPL"])
        stock = fetcher._fetch_single("AAPL")

        assert stock.symbol == "AAPL"
        assert stock.name == "Apple Inc."
        assert stock.price == 150.25
        assert stock.change == pytest.approx(2.50, rel=0.01)
        assert stock.error is None

    def test_fetch_single_error(self, qapp):
        """Test fetching with an error."""
        with patch("src.stock_service.yf") as mock_yf:
            mock_yf.Ticker.side_effect = Exception("Network error")

            fetcher = StockFetcher(["INVALID"])
            stock = fetcher._fetch_single("INVALID")

            assert stock.symbol == "INVALID"
            assert stock.error == "Network error"

    def test_fetch_calculates_change(self, qapp):
        """Test that change is calculated correctly."""
        with patch("src.stock_service.yf") as mock_yf:
            mock_ticker = MagicMock()
            mock_ticker.info = {
                "shortName": "Test Stock",
                "regularMarketPrice": 100.0,
                "regularMarketPreviousClose": 95.0,
            }
            mock_yf.Ticker.return_value = mock_ticker

            fetcher = StockFetcher(["TEST"])
            stock = fetcher._fetch_single("TEST")

            assert stock.change == pytest.approx(5.0)
            assert stock.change_percent == pytest.approx(5.26, rel=0.01)

    def test_fetch_handles_missing_fields(self, qapp):
        """Test handling of missing price fields."""
        with patch("src.stock_service.yf") as mock_yf:
            mock_ticker = MagicMock()
            mock_ticker.info = {
                "shortName": "Test Stock",
                "currentPrice": 50.0,  # Alternative field
                "previousClose": 48.0,  # Alternative field
            }
            mock_yf.Ticker.return_value = mock_ticker

            fetcher = StockFetcher(["TEST"])
            stock = fetcher._fetch_single("TEST")

            assert stock.price == 50.0


class TestStockService:
    """Tests for the StockService class."""

    def test_service_creation(self, qapp):
        """Test creating a stock service."""
        service = StockService(refresh_interval=30)
        assert service.refresh_interval == 30
        assert service.symbols == []

    def test_set_symbols(self, qapp):
        """Test setting symbols."""
        service = StockService()
        service.set_symbols(["AAPL", "GOOGL"])

        assert service.symbols == ["AAPL", "GOOGL"]

    def test_set_symbols_copies_list(self, qapp):
        """Test that set_symbols creates a copy."""
        service = StockService()
        original = ["AAPL", "GOOGL"]
        service.set_symbols(original)

        original.append("MSFT")
        assert "MSFT" not in service.symbols

    def test_add_symbol(self, qapp):
        """Test adding a symbol."""
        service = StockService()
        service.add_symbol("aapl")  # lowercase

        assert "AAPL" in service.symbols

    def test_add_symbol_no_duplicates(self, qapp):
        """Test that duplicate symbols are not added."""
        service = StockService()
        service.add_symbol("AAPL")
        service.add_symbol("AAPL")
        service.add_symbol("aapl")

        assert service.symbols.count("AAPL") == 1

    def test_add_symbol_strips_whitespace(self, qapp):
        """Test that whitespace is stripped from symbols."""
        service = StockService()
        service.add_symbol("  AAPL  ")

        assert "AAPL" in service.symbols

    def test_add_empty_symbol_ignored(self, qapp):
        """Test that empty symbols are ignored."""
        service = StockService()
        service.add_symbol("")
        service.add_symbol("   ")

        assert len(service.symbols) == 0

    def test_remove_symbol(self, qapp):
        """Test removing a symbol."""
        service = StockService()
        service.set_symbols(["AAPL", "GOOGL"])
        service.remove_symbol("AAPL")

        assert "AAPL" not in service.symbols
        assert "GOOGL" in service.symbols

    def test_remove_symbol_case_insensitive(self, qapp):
        """Test that symbol removal is case insensitive."""
        service = StockService()
        service.set_symbols(["AAPL"])
        service.remove_symbol("aapl")

        assert "AAPL" not in service.symbols

    def test_remove_nonexistent_symbol(self, qapp):
        """Test removing a symbol that doesn't exist."""
        service = StockService()
        service.set_symbols(["AAPL"])
        service.remove_symbol("GOOGL")  # Should not raise

        assert service.symbols == ["AAPL"]

    def test_set_refresh_interval(self, qapp):
        """Test updating refresh interval."""
        service = StockService(refresh_interval=60)
        service.set_refresh_interval(120)

        assert service.refresh_interval == 120

    def test_refresh_with_no_symbols(self, qapp):
        """Test that refresh with no symbols doesn't start fetcher."""
        service = StockService()
        service.refresh()

        assert service._fetcher is None

    def test_stop_service(self, qapp):
        """Test stopping the service."""
        service = StockService()
        service.start()
        service.stop()

        assert not service._timer.isActive()

    def test_stocks_updated_signal(self, qapp, mock_yfinance, qtbot):
        """Test that stocks_updated signal is emitted."""
        service = StockService()
        service.set_symbols(["AAPL"])

        with qtbot.waitSignal(service.stocks_updated, timeout=5000) as blocker:
            service.refresh()

        assert len(blocker.args[0]) == 1
        assert blocker.args[0][0].symbol == "AAPL"
