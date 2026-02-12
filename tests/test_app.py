"""Tests for the main application class."""

from unittest.mock import MagicMock, patch

import pytest

from src.app import StockTickerApp
from src.models import AppConfig


class TestStockTickerApp:
    """Tests for the StockTickerApp class."""

    @pytest.fixture
    def app_with_temp_config(self, temp_config_file, qapp):
        """Create app with temporary config file."""
        with patch("src.app.ConfigManager") as MockConfigManager:
            mock_manager = MagicMock()
            mock_manager.load.return_value = AppConfig()
            mock_manager.save = MagicMock()
            mock_manager.update = MagicMock(return_value=AppConfig())
            MockConfigManager.return_value = mock_manager

            # Prevent actual stock fetching
            with patch("src.app.StockService") as MockStockService:
                mock_service = MagicMock()
                MockStockService.return_value = mock_service

                app = StockTickerApp()
                app._mock_config_manager = mock_manager
                app._mock_stock_service = mock_service
                yield app

    def test_app_creation(self, app_with_temp_config):
        """Test that app creates all components."""
        app = app_with_temp_config

        assert app.popup is not None
        assert app.tray is not None
        assert app.stock_service is not None

    def test_app_loads_config(self, app_with_temp_config):
        """Test that app loads configuration."""
        app = app_with_temp_config

        app._mock_config_manager.load.assert_called()

    def test_toggle_popup_shows_when_hidden(self, app_with_temp_config):
        """Test toggling popup when hidden shows it."""
        app = app_with_temp_config
        app.popup.hide()

        app._toggle_popup()

        assert app.popup.isVisible()

    def test_toggle_popup_hides_when_visible(self, app_with_temp_config):
        """Test toggling popup when visible hides it."""
        app = app_with_temp_config
        app.popup.show()

        app._toggle_popup()

        assert not app.popup.isVisible()

    def test_add_stock(self, app_with_temp_config):
        """Test adding a stock."""
        app = app_with_temp_config
        app.config.watchlist = ["AAPL"]

        app._add_stock("GOOGL")

        assert "GOOGL" in app.config.watchlist
        app._mock_config_manager.save.assert_called()

    def test_add_stock_uppercase(self, app_with_temp_config):
        """Test that added stocks are uppercased."""
        app = app_with_temp_config
        app.config.watchlist = []

        app._add_stock("aapl")

        assert "AAPL" in app.config.watchlist

    def test_add_stock_no_duplicates(self, app_with_temp_config):
        """Test that duplicate stocks aren't added."""
        app = app_with_temp_config
        app.config.watchlist = ["AAPL"]

        app._add_stock("AAPL")

        assert app.config.watchlist.count("AAPL") == 1

    def test_remove_stock(self, app_with_temp_config):
        """Test removing a stock."""
        app = app_with_temp_config
        app.config.watchlist = ["AAPL", "GOOGL"]

        app._remove_stock("AAPL")

        assert "AAPL" not in app.config.watchlist
        assert "GOOGL" in app.config.watchlist
        app._mock_config_manager.save.assert_called()

    def test_remove_nonexistent_stock(self, app_with_temp_config):
        """Test removing a stock that doesn't exist."""
        app = app_with_temp_config
        app.config.watchlist = ["AAPL"]

        app._remove_stock("GOOGL")  # Should not raise

        assert app.config.watchlist == ["AAPL"]

    def test_quit_stops_service(self, app_with_temp_config):
        """Test that quit stops the stock service."""
        app = app_with_temp_config

        with pytest.raises(SystemExit):
            app._quit()

        app._mock_stock_service.stop.assert_called()

    def test_quit_hides_tray(self, app_with_temp_config):
        """Test that quit hides the tray."""
        app = app_with_temp_config
        app.tray.show()

        with pytest.raises(SystemExit):
            app._quit()

        assert not app.tray._tray_icon.isVisible()

    def test_popup_closed_saves_geometry(self, app_with_temp_config):
        """Test that closing popup saves its geometry."""
        app = app_with_temp_config

        app._on_popup_closed()

        app._mock_config_manager.update.assert_called()
