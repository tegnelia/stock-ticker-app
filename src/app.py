"""Main application class coordinating all components."""

import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .config import ConfigManager
from .models import AppConfig
from .popup import PopupWindow
from .stock_service import StockService
from .tray import SystemTrayManager


class StockTickerApp:
    """Main application class that coordinates all components."""

    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Keep running with tray

        # Load configuration
        self.config_manager = ConfigManager()
        self.config = self.config_manager.load()

        # Load stylesheet
        self._load_stylesheet()

        # Initialize components
        self.stock_service = StockService(
            self.config.refresh_interval,
            self.config.chart_period
        )
        self.popup = PopupWindow()
        self.tray = SystemTrayManager()

        # Setup connections
        self._connect_signals()

        # Initialize state
        self._initialize()

    def _load_stylesheet(self):
        """Load the QSS stylesheet."""
        # Try to load from installed location first, then from source
        style_paths = [
            Path(__file__).parent / "styles" / "theme.qss",
            Path.cwd() / "src" / "styles" / "theme.qss",
        ]

        for style_path in style_paths:
            if style_path.exists():
                with open(style_path, "r") as f:
                    self.app.setStyleSheet(f.read())
                break

    def _connect_signals(self):
        """Connect all component signals."""
        # Tray signals
        self.tray.toggle_window.connect(self._toggle_popup)
        self.tray.refresh_requested.connect(self.stock_service.refresh)
        self.tray.quit_requested.connect(self._quit)

        # Popup signals
        self.popup.closed.connect(self._on_popup_closed)
        self.popup.stock_added.connect(self._add_stock)
        self.popup.stock_removed.connect(self._remove_stock)
        self.popup.stock_moved.connect(self._move_stock)
        self.popup.refresh_interval_changed.connect(self._on_refresh_interval_changed)
        self.popup.chart_period_changed.connect(self._on_chart_period_changed)

        # Stock service signals
        self.stock_service.stocks_updated.connect(self.popup.update_stocks)

    def _initialize(self):
        """Initialize the application state."""
        # Set popup position and size from config
        self.popup.set_position(*self.config.popup_position)
        self.popup.resize(*self.config.popup_size)

        # Set current settings in popup
        self.popup.set_refresh_interval(self.config.refresh_interval)
        self.popup.set_chart_period(self.config.chart_period)

        # Set watchlist
        self.stock_service.set_symbols(self.config.watchlist)

    def _toggle_popup(self):
        """Toggle the popup window visibility."""
        if self.popup.isVisible():
            self._save_popup_geometry()
            self.popup.hide()
        else:
            self.popup.show()
            self.popup.raise_()
            self.popup.activateWindow()

        self.tray.update_show_action(self.popup.isVisible())

    def _on_popup_closed(self):
        """Handle popup window close."""
        self._save_popup_geometry()
        self.tray.update_show_action(False)

    def _save_popup_geometry(self):
        """Save popup position and size to config."""
        self.config_manager.update(
            popup_position=self.popup.get_position(),
            popup_size=self.popup.get_size()
        )

    def _add_stock(self, symbol: str):
        """Add a stock to the watchlist."""
        symbol = symbol.upper().strip()
        if symbol and symbol not in self.config.watchlist:
            self.config.watchlist.append(symbol)
            self.config_manager.save(self.config)
            self.stock_service.add_symbol(symbol)
            self.stock_service.refresh()

    def _remove_stock(self, symbol: str):
        """Remove a stock from the watchlist."""
        if symbol in self.config.watchlist:
            self.config.watchlist.remove(symbol)
            self.config_manager.save(self.config)
            self.stock_service.remove_symbol(symbol)
            # Update display to remove the widget
            self.stock_service.refresh()

    def _move_stock(self, symbol: str, direction: int):
        """Move a stock up or down in the watchlist. direction: -1=up, 1=down."""
        if symbol not in self.config.watchlist:
            return

        idx = self.config.watchlist.index(symbol)
        new_idx = idx + direction

        # Check bounds
        if new_idx < 0 or new_idx >= len(self.config.watchlist):
            return

        # Swap positions
        self.config.watchlist[idx], self.config.watchlist[new_idx] = \
            self.config.watchlist[new_idx], self.config.watchlist[idx]

        self.config_manager.save(self.config)
        self.stock_service.set_symbols(self.config.watchlist)
        self.stock_service.refresh()

    def _on_refresh_interval_changed(self, seconds: int):
        """Handle refresh interval change from popup."""
        self.config.refresh_interval = seconds
        self.config_manager.save(self.config)
        self.stock_service.set_refresh_interval(seconds)

    def _on_chart_period_changed(self, period: str):
        """Handle chart period change from popup."""
        self.config.chart_period = period
        self.config_manager.save(self.config)
        self.stock_service.set_chart_period(period)
        # Refresh to get new historical data
        self.stock_service.refresh()

    def _quit(self):
        """Quit the application."""
        self._save_popup_geometry()
        self.stock_service.stop()
        self.tray.hide()
        self.popup.close()
        self.app.quit()
        sys.exit(0)

    def run(self) -> int:
        """Run the application."""
        # Show tray icon
        self.tray.show()

        # Show popup initially
        self.popup.show()
        self.tray.update_show_action(True)

        # Start stock service
        self.stock_service.start()

        return self.app.exec()


def main() -> int:
    """Entry point for the application."""
    app = StockTickerApp()
    return app.run()
