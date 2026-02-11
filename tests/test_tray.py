"""Tests for the system tray manager."""

import pytest
from PySide6.QtWidgets import QSystemTrayIcon

from src.tray import SystemTrayManager, create_default_icon


class TestCreateDefaultIcon:
    """Tests for the create_default_icon function."""

    def test_icon_created(self, qapp):
        """Test that an icon is created."""
        icon = create_default_icon()
        assert not icon.isNull()

    def test_icon_has_pixmap(self, qapp):
        """Test that icon has a valid pixmap."""
        icon = create_default_icon()
        pixmap = icon.pixmap(64, 64)
        assert not pixmap.isNull()
        assert pixmap.width() == 64
        assert pixmap.height() == 64


class TestSystemTrayManager:
    """Tests for the SystemTrayManager class."""

    def test_tray_creation(self, qapp):
        """Test creating a system tray manager."""
        tray = SystemTrayManager()
        assert tray._tray_icon is not None

    def test_tray_tooltip(self, qapp):
        """Test tray icon tooltip."""
        tray = SystemTrayManager()
        assert tray._tray_icon.toolTip() == "Stock Ticker"

    def test_tray_has_context_menu(self, qapp):
        """Test that tray has a context menu."""
        tray = SystemTrayManager()
        menu = tray._tray_icon.contextMenu()
        assert menu is not None

    def test_context_menu_actions(self, qapp):
        """Test context menu has expected actions."""
        tray = SystemTrayManager()
        menu = tray._tray_icon.contextMenu()
        actions = menu.actions()

        action_texts = [a.text() for a in actions if not a.isSeparator()]
        assert "Hide Window" in action_texts
        assert "Refresh Now" in action_texts
        assert "Quit" in action_texts

    def test_toggle_window_signal(self, qapp, qtbot):
        """Test toggle_window signal is emitted on left click."""
        tray = SystemTrayManager()

        with qtbot.waitSignal(tray.toggle_window):
            tray._on_activated(QSystemTrayIcon.Trigger)

    def test_toggle_window_not_emitted_on_right_click(self, qapp, qtbot):
        """Test toggle_window not emitted on context menu."""
        tray = SystemTrayManager()

        with qtbot.assertNotEmitted(tray.toggle_window):
            tray._on_activated(QSystemTrayIcon.Context)

    def test_refresh_requested_signal(self, qapp, qtbot):
        """Test refresh_requested signal from menu."""
        tray = SystemTrayManager()
        menu = tray._tray_icon.contextMenu()

        # Find refresh action
        refresh_action = None
        for action in menu.actions():
            if action.text() == "Refresh Now":
                refresh_action = action
                break

        with qtbot.waitSignal(tray.refresh_requested):
            refresh_action.trigger()

    def test_quit_requested_signal(self, qapp, qtbot):
        """Test quit_requested signal from menu."""
        tray = SystemTrayManager()
        menu = tray._tray_icon.contextMenu()

        # Find quit action
        quit_action = None
        for action in menu.actions():
            if action.text() == "Quit":
                quit_action = action
                break

        with qtbot.waitSignal(tray.quit_requested):
            quit_action.trigger()

    def test_update_show_action_visible(self, qapp):
        """Test updating show action when window is visible."""
        tray = SystemTrayManager()
        tray.update_show_action(window_visible=True)

        assert tray._show_action.text() == "Hide Window"

    def test_update_show_action_hidden(self, qapp):
        """Test updating show action when window is hidden."""
        tray = SystemTrayManager()
        tray.update_show_action(window_visible=False)

        assert tray._show_action.text() == "Show Window"

    def test_show_tray(self, qapp):
        """Test showing the tray icon."""
        tray = SystemTrayManager()
        tray.show()

        assert tray._tray_icon.isVisible()

    def test_hide_tray(self, qapp):
        """Test hiding the tray icon."""
        tray = SystemTrayManager()
        tray.show()
        tray.hide()

        assert not tray._tray_icon.isVisible()
