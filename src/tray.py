"""System tray icon and menu management."""

from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


def create_default_icon() -> QIcon:
    """Create a simple stock chart icon programmatically."""
    size = 64
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))  # Transparent background

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Draw background circle
    painter.setBrush(QColor(108, 99, 255))  # Purple
    painter.setPen(QColor(0, 0, 0, 0))
    painter.drawEllipse(4, 4, size - 8, size - 8)

    # Draw simple up arrow / chart line
    painter.setPen(QColor(255, 255, 255))
    painter.setBrush(QColor(255, 255, 255))

    # Draw "$" symbol
    font = QFont("Arial", 28, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x0084, "$")  # Qt.AlignCenter

    painter.end()
    return QIcon(pixmap)


class SystemTrayManager(QObject):
    """Manages the system tray icon and its interactions."""

    toggle_window = Signal()
    refresh_requested = Signal()
    quit_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._tray_icon = QSystemTrayIcon(self)
        self._tray_icon.setIcon(create_default_icon())
        self._tray_icon.setToolTip("Stock Ticker")

        self._setup_menu()
        self._connect_signals()

    def _setup_menu(self):
        """Create the right-click context menu."""
        menu = QMenu()

        # Show/Hide action
        self._show_action = QAction("Hide Window", menu)
        self._show_action.triggered.connect(self.toggle_window.emit)
        menu.addAction(self._show_action)

        menu.addSeparator()

        # Refresh action
        refresh_action = QAction("Refresh Now", menu)
        refresh_action.triggered.connect(self.refresh_requested.emit)
        menu.addAction(refresh_action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self.quit_requested.emit)
        menu.addAction(quit_action)

        self._tray_icon.setContextMenu(menu)

    def _connect_signals(self):
        """Connect tray icon signals."""
        self._tray_icon.activated.connect(self._on_activated)

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.Trigger:  # Left click
            self.toggle_window.emit()

    def show(self):
        """Show the tray icon."""
        self._tray_icon.show()

    def hide(self):
        """Hide the tray icon."""
        self._tray_icon.hide()

    def update_show_action(self, window_visible: bool):
        """Update the show/hide action text based on window visibility."""
        self._show_action.setText("Hide Window" if window_visible else "Show Window")

    def show_message(self, title: str, message: str,
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.Information,
                     timeout: int = 3000):
        """Show a system notification."""
        self._tray_icon.showMessage(title, message, icon, timeout)
