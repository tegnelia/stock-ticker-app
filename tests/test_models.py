"""Tests for data models."""



from src.models import Stock, AppConfig


class TestStock:
    """Tests for the Stock dataclass."""

    def test_stock_creation(self, sample_stock):
        """Test creating a stock with all fields."""
        assert sample_stock.symbol == "AAPL"
        assert sample_stock.name == "Apple Inc."
        assert sample_stock.price == 150.25
        assert sample_stock.change == 2.50
        assert sample_stock.change_percent == 1.69
        assert sample_stock.last_updated is not None
        assert sample_stock.error is None

    def test_stock_defaults(self):
        """Test stock default values."""
        stock = Stock(symbol="TEST")
        assert stock.name == ""
        assert stock.price == 0.0
        assert stock.change == 0.0
        assert stock.change_percent == 0.0
        assert stock.last_updated is None
        assert stock.error is None

    def test_is_up_positive_change(self, sample_stock):
        """Test is_up property with positive change."""
        assert sample_stock.is_up is True
        assert sample_stock.is_down is False

    def test_is_down_negative_change(self, sample_stock_down):
        """Test is_down property with negative change."""
        assert sample_stock_down.is_up is False
        assert sample_stock_down.is_down is True

    def test_is_flat_no_change(self, sample_stock_flat):
        """Test properties with zero change."""
        assert sample_stock_flat.is_up is False
        assert sample_stock_flat.is_down is False

    def test_change_color_up(self, sample_stock):
        """Test change_color for positive change."""
        assert sample_stock.change_color == "#4CAF50"  # Green

    def test_change_color_down(self, sample_stock_down):
        """Test change_color for negative change."""
        assert sample_stock_down.change_color == "#F44336"  # Red

    def test_change_color_flat(self, sample_stock_flat):
        """Test change_color for zero change."""
        assert sample_stock_flat.change_color == "#9E9E9E"  # Gray

    def test_stock_with_error(self, sample_stock_error):
        """Test stock with error state."""
        assert sample_stock_error.error == "Symbol not found"
        assert sample_stock_error.price == 0.0


class TestAppConfig:
    """Tests for the AppConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = AppConfig()
        assert config.watchlist == ["^DJI", "^IXIC", "^GSPC", "^NYA"]
        assert config.refresh_interval == 60
        assert config.popup_position == (100, 100)
        assert config.popup_size == (320, 400)
        assert config.theme == "dark"

    def test_custom_config(self, sample_config):
        """Test custom configuration values."""
        assert sample_config.watchlist == ["AAPL", "GOOGL", "MSFT"]
        assert sample_config.refresh_interval == 30
        assert sample_config.popup_position == (200, 200)
        assert sample_config.popup_size == (400, 500)
        assert sample_config.theme == "dark"

    def test_config_watchlist_mutable(self):
        """Test that default watchlist is independent per instance."""
        config1 = AppConfig()
        config2 = AppConfig()
        config1.watchlist.append("AAPL")
        assert "AAPL" not in config2.watchlist

    def test_config_with_empty_watchlist(self):
        """Test config with empty watchlist."""
        config = AppConfig(watchlist=[])
        assert config.watchlist == []
