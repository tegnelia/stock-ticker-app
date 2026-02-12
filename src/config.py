"""Configuration management for the stock ticker app."""

import json
from pathlib import Path
from typing import Any

from .models import AppConfig


class ConfigManager:
    """Manages loading and saving application configuration."""

    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_dir = Path.home() / ".config" / "stock-ticker"
            config_dir.mkdir(parents=True, exist_ok=True)
            self.config_path = config_dir / "config.json"
        else:
            self.config_path = Path(config_path)

        self._config: AppConfig | None = None

    def load(self) -> AppConfig:
        """Load configuration from file or return defaults."""
        if self._config is not None:
            return self._config

        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    data = json.load(f)
                # Use defaults from a fresh AppConfig instance
                defaults = AppConfig()
                self._config = AppConfig(
                    watchlist=data.get("watchlist", defaults.watchlist),
                    refresh_interval=data.get("refresh_interval", defaults.refresh_interval),
                    chart_period=data.get("chart_period", defaults.chart_period),
                    popup_position=tuple(data.get("popup_position", list(defaults.popup_position))),
                    popup_size=tuple(data.get("popup_size", list(defaults.popup_size))),
                    theme=data.get("theme", defaults.theme),
                )
            except (json.JSONDecodeError, KeyError, TypeError):
                self._config = AppConfig()
        else:
            self._config = AppConfig()

        return self._config

    def save(self, config: AppConfig) -> None:
        """Save configuration to file."""
        self._config = config
        data = {
            "watchlist": config.watchlist,
            "refresh_interval": config.refresh_interval,
            "chart_period": config.chart_period,
            "popup_position": list(config.popup_position),
            "popup_size": list(config.popup_size),
            "theme": config.theme,
        }
        with open(self.config_path, "w") as f:
            json.dump(data, f, indent=2)

    def update(self, **kwargs: Any) -> AppConfig:
        """Update specific config values and save."""
        config = self.load()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        self.save(config)
        return config
