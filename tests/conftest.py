"""Shared pytest fixtures for stock ticker app tests."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from PySide6.QtWidgets import QApplication

from src.models import Stock, AppConfig


@pytest.fixture(scope="session")
def qapp():
    """Create a QApplication instance for the test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def sample_stock():
    """Create a sample stock for testing."""
    return Stock(
        symbol="AAPL",
        name="Apple Inc.",
        price=150.25,
        change=2.50,
        change_percent=1.69,
        last_updated=datetime.now(),
        history=[145.0, 147.0, 148.5, 149.0, 150.25],
    )


@pytest.fixture
def sample_stock_down():
    """Create a sample stock with negative change."""
    return Stock(
        symbol="GOOGL",
        name="Alphabet Inc.",
        price=140.00,
        change=-3.25,
        change_percent=-2.27,
        last_updated=datetime.now(),
    )


@pytest.fixture
def sample_stock_flat():
    """Create a sample stock with no change."""
    return Stock(
        symbol="MSFT",
        name="Microsoft Corporation",
        price=380.00,
        change=0.0,
        change_percent=0.0,
        last_updated=datetime.now(),
    )


@pytest.fixture
def sample_stock_error():
    """Create a sample stock with an error."""
    return Stock(
        symbol="INVALID",
        error="Symbol not found",
        last_updated=datetime.now(),
    )


@pytest.fixture
def sample_config():
    """Create a sample app configuration."""
    return AppConfig(
        watchlist=["AAPL", "GOOGL", "MSFT"],
        refresh_interval=30,
        popup_position=(200, 200),
        popup_size=(400, 500),
        theme="dark",
    )


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create a temporary directory for config files."""
    return tmp_path


@pytest.fixture
def temp_config_file(temp_config_dir):
    """Create a temporary config file path."""
    return temp_config_dir / "config.json"


@pytest.fixture
def mock_yfinance():
    """Mock yfinance Ticker for testing."""
    import pandas as pd

    with patch("src.stock_service.yf") as mock_yf:
        mock_ticker = MagicMock()
        mock_ticker.info = {
            "shortName": "Apple Inc.",
            "regularMarketPrice": 150.25,
            "regularMarketPreviousClose": 147.75,
        }
        # Mock history method to return a DataFrame
        mock_history = pd.DataFrame({
            "Close": [145.0, 147.0, 148.5, 149.0, 150.25]
        })
        mock_ticker.history.return_value = mock_history
        mock_yf.Ticker.return_value = mock_ticker
        yield mock_yf
