"""Floating popup window for displaying stock prices."""

from datetime import datetime
from typing import Callable

from PySide6.QtCore import Qt, QPoint, Signal, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QFont, QCursor, QPainter, QPen, QColor, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QSizeGrip, QGraphicsOpacityEffect,
    QComboBox
)

from .models import Stock, REFRESH_INTERVALS, CHART_PERIODS


class SparklineWidget(QWidget):
    """A mini chart widget showing price history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.data: list[float] = []
        self.is_up: bool = True  # Based on daily change (vs previous close)
        self.prev_close: float = 0.0  # Previous day's close price
        self.setMinimumSize(60, 22)
        self.setMaximumHeight(25)

    def set_data(self, data: list[float], is_up: bool = True, prev_close: float = 0.0):
        """Set the data points for the sparkline."""
        self.data = data
        self.is_up = is_up
        self.prev_close = prev_close
        self.update()

    def paintEvent(self, event):
        """Draw the sparkline chart."""
        painter = QPainter(self)
        painter.eraseRect(self.rect())

        if not self.data or len(self.data) < 2:
            painter.end()
            return
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate bounds
        width = self.width()
        height = self.height()
        padding = 2

        min_val = min(self.data)
        max_val = max(self.data)

        # Include prev_close in the range calculation if it's set
        if self.prev_close > 0:
            min_val = min(min_val, self.prev_close)
            max_val = max(max_val, self.prev_close)

        val_range = max_val - min_val if max_val != min_val else 1

        # Color based on daily change (current price vs previous close)
        if self.is_up:
            line_color = QColor("#4CAF50")  # Green
            fill_color = QColor(76, 175, 80, 50)  # Green with alpha
        else:
            line_color = QColor("#F44336")  # Red
            fill_color = QColor(244, 67, 54, 50)  # Red with alpha

        # Draw previous close line first (so it's behind the chart)
        if self.prev_close > 0 and min_val <= self.prev_close <= max_val:
            prev_close_y = height - padding - ((self.prev_close - min_val) / val_range) * (height - 2 * padding)
            pen = QPen(QColor("#FFD700"))  # Gold/yellow color
            pen.setWidth(1)
            pen.setStyle(Qt.DashLine)
            painter.setPen(pen)
            painter.drawLine(int(padding), int(prev_close_y), int(width - padding), int(prev_close_y))

        # Build the price path
        path = QPainterPath()
        fill_path = QPainterPath()

        x_step = (width - 2 * padding) / (len(self.data) - 1)

        for i, val in enumerate(self.data):
            x = padding + i * x_step
            y = height - padding - ((val - min_val) / val_range) * (height - 2 * padding)

            if i == 0:
                path.moveTo(x, y)
                fill_path.moveTo(x, height - padding)
                fill_path.lineTo(x, y)
            else:
                path.lineTo(x, y)
                fill_path.lineTo(x, y)

        # Complete fill path
        fill_path.lineTo(width - padding, height - padding)
        fill_path.closeSubpath()

        # Draw fill
        painter.fillPath(fill_path, fill_color)

        # Draw price line
        pen = QPen(line_color)
        pen.setWidth(2)
        pen.setStyle(Qt.SolidLine)
        painter.setPen(pen)
        painter.drawPath(path)


class StockItemWidget(QFrame):
    """Widget displaying a single stock's information."""

    remove_clicked = Signal(str)  # Emits symbol
    move_up_clicked = Signal(str)  # Emits symbol
    move_down_clicked = Signal(str)  # Emits symbol

    def __init__(self, stock: Stock, parent=None):
        super().__init__(parent)
        self.stock = stock
        self.setObjectName("StockItem")
        self._setup_ui()
        self._update_display()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(3)

        # Top row: symbol, name, remove button
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        # Left side: symbol and name
        left_layout = QVBoxLayout()
        left_layout.setSpacing(2)

        self.symbol_label = QLabel(self.stock.symbol)
        self.symbol_label.setObjectName("StockSymbol")
        left_layout.addWidget(self.symbol_label)

        self.name_label = QLabel()
        self.name_label.setObjectName("StockName")
        self.name_label.setMaximumWidth(150)
        left_layout.addWidget(self.name_label)

        top_row.addLayout(left_layout)
        top_row.addStretch()

        # Right side: price and change
        right_layout = QVBoxLayout()
        right_layout.setSpacing(2)
        right_layout.setAlignment(Qt.AlignRight)

        self.price_label = QLabel()
        self.price_label.setObjectName("StockPrice")
        self.price_label.setAlignment(Qt.AlignRight)
        right_layout.addWidget(self.price_label)

        self.change_label = QLabel()
        self.change_label.setAlignment(Qt.AlignRight)
        right_layout.addWidget(self.change_label)

        top_row.addLayout(right_layout)

        # Action buttons container
        buttons_layout = QVBoxLayout()
        buttons_layout.setSpacing(2)
        buttons_layout.setContentsMargins(0, 0, 0, 0)

        # Move up button
        self.move_up_btn = QPushButton("▲")
        self.move_up_btn.setObjectName("MoveButton")
        self.move_up_btn.setFixedSize(16, 12)
        self.move_up_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.move_up_btn.clicked.connect(lambda: self.move_up_clicked.emit(self.stock.symbol))
        buttons_layout.addWidget(self.move_up_btn)

        # Move down button
        self.move_down_btn = QPushButton("▼")
        self.move_down_btn.setObjectName("MoveButton")
        self.move_down_btn.setFixedSize(16, 12)
        self.move_down_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.move_down_btn.clicked.connect(lambda: self.move_down_clicked.emit(self.stock.symbol))
        buttons_layout.addWidget(self.move_down_btn)

        top_row.addLayout(buttons_layout)

        # Remove button
        self.remove_btn = QPushButton("×")
        self.remove_btn.setObjectName("RemoveButton")
        self.remove_btn.setFixedSize(20, 20)
        self.remove_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.remove_btn.clicked.connect(lambda: self.remove_clicked.emit(self.stock.symbol))
        top_row.addWidget(self.remove_btn)

        layout.addLayout(top_row)

        # Bottom row: sparkline chart
        self.sparkline = SparklineWidget()
        layout.addWidget(self.sparkline)

    def _update_display(self):
        """Update the display with current stock data."""
        if self.stock.error:
            self.name_label.setText("Error loading")
            self.price_label.setText("--")
            self.change_label.setText(self.stock.error[:30])
            self.change_label.setObjectName("StockChangeFlat")
            return

        # Truncate name if too long
        name = self.stock.name
        if len(name) > 25:
            name = name[:22] + "..."
        self.name_label.setText(name)

        # Format price (without $)
        self.price_label.setText(f"{self.stock.price:,.2f}")

        # Format change
        sign = "+" if self.stock.change >= 0 else ""
        change_text = f"{sign}{self.stock.change:,.2f} ({sign}{self.stock.change_percent:.2f}%)"
        self.change_label.setText(change_text)

        # Set color based on change direction
        if self.stock.is_up:
            self.change_label.setObjectName("StockChangeUp")
        elif self.stock.is_down:
            self.change_label.setObjectName("StockChangeDown")
        else:
            self.change_label.setObjectName("StockChangeFlat")

        # Force style refresh
        self.change_label.style().unpolish(self.change_label)
        self.change_label.style().polish(self.change_label)

        # Update sparkline (color based on daily change vs previous close)
        if self.stock.history:
            self.sparkline.set_data(
                self.stock.history,
                is_up=self.stock.change >= 0,
                prev_close=self.stock.prev_close
            )
            self.sparkline.show()
        else:
            self.sparkline.hide()

    def update_stock(self, stock: Stock):
        """Update with new stock data."""
        old_price = self.stock.price
        self.stock = stock
        self._update_display()

        # Animate if price changed
        if old_price != stock.price and old_price != 0:
            self._animate_change()

    def _animate_change(self):
        """Brief flash animation on price change."""
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)

        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(300)
        anim.setStartValue(0.5)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeleteWhenStopped)


class PopupWindow(QWidget):
    """Frameless floating popup window for stock display."""

    closed = Signal()
    stock_added = Signal(str)  # Emits symbol
    stock_removed = Signal(str)  # Emits symbol
    stock_moved = Signal(str, int)  # Emits (symbol, direction: -1=up, 1=down)
    refresh_interval_changed = Signal(int)  # Emits seconds
    chart_period_changed = Signal(str)  # Emits period string

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setObjectName("PopupWindow")

        self._drag_position: QPoint | None = None
        self._stock_widgets: dict[str, StockItemWidget] = {}

        self._setup_ui()
        self.setMinimumSize(300, 350)
        self.resize(340, 500)

    def _setup_ui(self):
        # Main container with background
        self.container = QFrame(self)
        self.container.setObjectName("PopupWindow")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Title bar
        self._create_title_bar(container_layout)

        # Settings bar
        self._create_settings_bar(container_layout)

        # Stock list area
        self._create_stock_list(container_layout)

        # Add stock section
        self._create_add_section(container_layout)

        # Resize grip
        self.size_grip = QSizeGrip(self)
        self.size_grip.setObjectName("ResizeHandle")

    def _create_title_bar(self, parent_layout: QVBoxLayout):
        """Create the title bar with close button."""
        title_bar = QFrame()
        title_bar.setObjectName("TitleBar")
        title_bar.setFixedHeight(40)

        layout = QHBoxLayout(title_bar)
        layout.setContentsMargins(12, 0, 8, 0)

        title = QLabel("Stock Ticker")
        title.setObjectName("TitleLabel")
        layout.addWidget(title)

        layout.addStretch()

        close_btn = QPushButton("×")
        close_btn.setObjectName("CloseButton")
        close_btn.setFixedSize(28, 28)
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.clicked.connect(self._on_close)
        layout.addWidget(close_btn)

        parent_layout.addWidget(title_bar)

    def _create_settings_bar(self, parent_layout: QVBoxLayout):
        """Create the settings bar with refresh interval and chart period selectors."""
        settings_bar = QFrame()
        settings_bar.setObjectName("SettingsBar")
        settings_bar.setFixedHeight(36)

        layout = QHBoxLayout(settings_bar)
        layout.setContentsMargins(12, 4, 12, 4)
        layout.setSpacing(8)

        # Refresh interval selector
        refresh_label = QLabel("Refresh:")
        refresh_label.setObjectName("SettingsLabel")
        layout.addWidget(refresh_label)

        self.refresh_combo = QComboBox()
        self.refresh_combo.setObjectName("SettingsCombo")
        for label in REFRESH_INTERVALS.keys():
            self.refresh_combo.addItem(label)
        self.refresh_combo.currentTextChanged.connect(self._on_refresh_changed)
        layout.addWidget(self.refresh_combo)

        layout.addStretch()

        # Chart period selector
        chart_label = QLabel("Chart:")
        chart_label.setObjectName("SettingsLabel")
        layout.addWidget(chart_label)

        self.chart_combo = QComboBox()
        self.chart_combo.setObjectName("SettingsCombo")
        for label in CHART_PERIODS.keys():
            self.chart_combo.addItem(label)
        self.chart_combo.setCurrentText("1 month")  # Default
        self.chart_combo.currentTextChanged.connect(self._on_chart_period_changed)
        layout.addWidget(self.chart_combo)

        parent_layout.addWidget(settings_bar)

    def _create_stock_list(self, parent_layout: QVBoxLayout):
        """Create the scrollable stock list area."""
        scroll_area = QScrollArea()
        scroll_area.setObjectName("StockList")
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        self.stock_container = QWidget()
        self.stock_layout = QVBoxLayout(self.stock_container)
        self.stock_layout.setContentsMargins(8, 8, 8, 8)
        self.stock_layout.setSpacing(8)
        self.stock_layout.addStretch()

        scroll_area.setWidget(self.stock_container)
        parent_layout.addWidget(scroll_area, 1)

        # Status label
        self.status_label = QLabel()
        self.status_label.setObjectName("StatusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        parent_layout.addWidget(self.status_label)

    def _create_add_section(self, parent_layout: QVBoxLayout):
        """Create the add stock input section."""
        add_section = QFrame()
        add_section.setObjectName("AddStockSection")

        layout = QHBoxLayout(add_section)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(8)

        self.symbol_input = QLineEdit()
        self.symbol_input.setObjectName("SymbolInput")
        self.symbol_input.setPlaceholderText("Enter symbol (e.g., AAPL)")
        self.symbol_input.returnPressed.connect(self._on_add_stock)
        layout.addWidget(self.symbol_input, 1)

        add_btn = QPushButton("Add")
        add_btn.setObjectName("AddButton")
        add_btn.setCursor(QCursor(Qt.PointingHandCursor))
        add_btn.clicked.connect(self._on_add_stock)
        layout.addWidget(add_btn)

        parent_layout.addWidget(add_section)

    def _on_close(self):
        """Handle close button click - hide instead of quit."""
        self.hide()
        self.closed.emit()

    def _on_add_stock(self):
        """Handle add stock button click."""
        symbol = self.symbol_input.text().strip().upper()
        if symbol:
            self.stock_added.emit(symbol)
            self.symbol_input.clear()

    def _on_remove_stock(self, symbol: str):
        """Handle remove stock button click."""
        self.stock_removed.emit(symbol)

    def _on_move_stock(self, symbol: str, direction: int):
        """Handle move stock up/down. direction: -1=up, 1=down."""
        self.stock_moved.emit(symbol, direction)

    def _on_refresh_changed(self, text: str):
        """Handle refresh interval change."""
        if text in REFRESH_INTERVALS:
            self.refresh_interval_changed.emit(REFRESH_INTERVALS[text])

    def _on_chart_period_changed(self, text: str):
        """Handle chart period change."""
        if text in CHART_PERIODS:
            self.chart_period_changed.emit(CHART_PERIODS[text])

    def set_refresh_interval(self, seconds: int):
        """Set the current refresh interval in the combo box."""
        for label, value in REFRESH_INTERVALS.items():
            if value == seconds:
                self.refresh_combo.blockSignals(True)
                self.refresh_combo.setCurrentText(label)
                self.refresh_combo.blockSignals(False)
                break

    def set_chart_period(self, period: str):
        """Set the current chart period in the combo box."""
        for label, value in CHART_PERIODS.items():
            if value == period:
                self.chart_combo.blockSignals(True)
                self.chart_combo.setCurrentText(label)
                self.chart_combo.blockSignals(False)
                break

    def update_stocks(self, stocks: list[Stock]):
        """Update the display with new stock data."""
        # Remove widgets for stocks no longer in list
        current_symbols = {s.symbol for s in stocks}
        for symbol in list(self._stock_widgets.keys()):
            if symbol not in current_symbols:
                self._remove_stock_widget(symbol)

        # Update or add widgets in order
        for i, stock in enumerate(stocks):
            if stock.symbol in self._stock_widgets:
                # Update existing widget
                self._stock_widgets[stock.symbol].update_stock(stock)
                # Ensure correct position (move to index i)
                widget = self._stock_widgets[stock.symbol]
                self.stock_layout.removeWidget(widget)
                self.stock_layout.insertWidget(i, widget)
            else:
                # Add new widget at correct position
                self._add_stock_widget_at(stock, i)

        # Update status
        now = datetime.now().strftime("%H:%M:%S")
        self.status_label.setText(f"Last updated: {now}")

    def _add_stock_widget(self, stock: Stock):
        """Add a new stock widget to the end of the list."""
        # Insert before the stretch (at count - 1)
        count = self.stock_layout.count()
        self._add_stock_widget_at(stock, count - 1)

    def _add_stock_widget_at(self, stock: Stock, index: int):
        """Add a new stock widget at a specific position."""
        widget = StockItemWidget(stock)
        widget.remove_clicked.connect(self._on_remove_stock)
        widget.move_up_clicked.connect(lambda s: self._on_move_stock(s, -1))
        widget.move_down_clicked.connect(lambda s: self._on_move_stock(s, 1))

        self.stock_layout.insertWidget(index, widget)
        self._stock_widgets[stock.symbol] = widget

    def _remove_stock_widget(self, symbol: str):
        """Remove a stock widget from the list."""
        if symbol in self._stock_widgets:
            widget = self._stock_widgets.pop(symbol)
            self.stock_layout.removeWidget(widget)
            widget.deleteLater()

    def set_position(self, x: int, y: int):
        """Set the popup position."""
        self.move(x, y)

    def get_position(self) -> tuple[int, int]:
        """Get the current popup position."""
        pos = self.pos()
        return (pos.x(), pos.y())

    def get_size(self) -> tuple[int, int]:
        """Get the current popup size."""
        size = self.size()
        return (size.width(), size.height())

    # Drag to move functionality
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_position is not None:
            self.move(event.globalPosition().toPoint() - self._drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_position = None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Position resize grip at bottom-right
        self.size_grip.move(
            self.width() - self.size_grip.width(),
            self.height() - self.size_grip.height()
        )
