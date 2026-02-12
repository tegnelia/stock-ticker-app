"""Tests for configuration management."""

import json


from src.config import ConfigManager
from src.models import AppConfig


class TestConfigManager:
    """Tests for the ConfigManager class."""

    def test_load_creates_default_config(self, temp_config_file):
        """Test loading returns default config when file doesn't exist."""
        manager = ConfigManager(str(temp_config_file))
        config = manager.load()

        assert config.watchlist == ["^DJI", "^IXIC", "^GSPC", "^NYA"]
        assert config.refresh_interval == 60
        assert config.theme == "dark"

    def test_save_creates_file(self, temp_config_file):
        """Test saving creates config file."""
        manager = ConfigManager(str(temp_config_file))
        config = AppConfig(watchlist=["AAPL", "GOOGL"])
        manager.save(config)

        assert temp_config_file.exists()
        with open(temp_config_file) as f:
            data = json.load(f)
        assert data["watchlist"] == ["AAPL", "GOOGL"]

    def test_load_existing_config(self, temp_config_file):
        """Test loading an existing config file."""
        config_data = {
            "watchlist": ["TSLA", "NVDA"],
            "refresh_interval": 120,
            "popup_position": [300, 300],
            "popup_size": [500, 600],
            "theme": "dark",
        }
        with open(temp_config_file, "w") as f:
            json.dump(config_data, f)

        manager = ConfigManager(str(temp_config_file))
        config = manager.load()

        assert config.watchlist == ["TSLA", "NVDA"]
        assert config.refresh_interval == 120
        assert config.popup_position == (300, 300)
        assert config.popup_size == (500, 600)

    def test_load_partial_config(self, temp_config_file):
        """Test loading config with missing fields uses defaults."""
        config_data = {"watchlist": ["AMZN"]}
        with open(temp_config_file, "w") as f:
            json.dump(config_data, f)

        manager = ConfigManager(str(temp_config_file))
        config = manager.load()

        assert config.watchlist == ["AMZN"]
        assert config.refresh_interval == 60  # default
        assert config.theme == "dark"  # default

    def test_load_invalid_json(self, temp_config_file):
        """Test loading invalid JSON returns default config."""
        with open(temp_config_file, "w") as f:
            f.write("not valid json {{{")

        manager = ConfigManager(str(temp_config_file))
        config = manager.load()

        # Should return defaults
        assert config.watchlist == ["^DJI", "^IXIC", "^GSPC", "^NYA"]

    def test_update_single_field(self, temp_config_file):
        """Test updating a single config field."""
        manager = ConfigManager(str(temp_config_file))
        manager.load()  # Initialize

        updated = manager.update(refresh_interval=90)

        assert updated.refresh_interval == 90
        # Verify it was saved
        with open(temp_config_file) as f:
            data = json.load(f)
        assert data["refresh_interval"] == 90

    def test_update_multiple_fields(self, temp_config_file):
        """Test updating multiple config fields."""
        manager = ConfigManager(str(temp_config_file))
        manager.load()

        updated = manager.update(
            watchlist=["AAPL"],
            popup_position=(500, 500)
        )

        assert updated.watchlist == ["AAPL"]
        assert updated.popup_position == (500, 500)

    def test_update_invalid_field_ignored(self, temp_config_file):
        """Test that updating non-existent field is ignored."""
        manager = ConfigManager(str(temp_config_file))
        manager.load()

        updated = manager.update(nonexistent_field="value")

        # Should not raise, config unchanged
        assert not hasattr(updated, "nonexistent_field")

    def test_config_caching(self, temp_config_file):
        """Test that config is cached after first load."""
        manager = ConfigManager(str(temp_config_file))
        config1 = manager.load()
        config2 = manager.load()

        assert config1 is config2

    def test_save_updates_cache(self, temp_config_file):
        """Test that save updates the cached config."""
        manager = ConfigManager(str(temp_config_file))
        manager.load()

        new_config = AppConfig(watchlist=["META"])
        manager.save(new_config)

        assert manager.load().watchlist == ["META"]

    def test_popup_position_tuple_conversion(self, temp_config_file):
        """Test that popup_position list is converted to tuple."""
        config_data = {"popup_position": [123, 456]}
        with open(temp_config_file, "w") as f:
            json.dump(config_data, f)

        manager = ConfigManager(str(temp_config_file))
        config = manager.load()

        assert isinstance(config.popup_position, tuple)
        assert config.popup_position == (123, 456)
