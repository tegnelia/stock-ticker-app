"""Tests for the popup window."""


from PySide6.QtCore import Qt

from src.models import Stock
from src.popup import PopupWindow, StockItemWidget


class TestStockItemWidget:
    """Tests for the StockItemWidget class."""

    def test_widget_creation(self, qapp, sample_stock):
        """Test creating a stock item widget."""
        widget = StockItemWidget(sample_stock)

        assert widget.stock.symbol == "AAPL"
        assert widget.symbol_label.text() == "AAPL"

    def test_widget_displays_price(self, qapp, sample_stock):
        """Test that price is displayed correctly (without $ symbol)."""
        widget = StockItemWidget(sample_stock)

        assert "150.25" in widget.price_label.text()
        assert "$" not in widget.price_label.text()

    def test_widget_displays_positive_change(self, qapp, sample_stock):
        """Test positive change display."""
        widget = StockItemWidget(sample_stock)

        change_text = widget.change_label.text()
        assert "+2.50" in change_text
        assert "+1.69%" in change_text

    def test_widget_displays_negative_change(self, qapp, sample_stock_down):
        """Test negative change display."""
        widget = StockItemWidget(sample_stock_down)

        change_text = widget.change_label.text()
        assert "-3.25" in change_text
        assert "-2.27%" in change_text

    def test_widget_displays_error(self, qapp, sample_stock_error):
        """Test error state display."""
        widget = StockItemWidget(sample_stock_error)

        assert widget.price_label.text() == "--"
        assert "Error loading" in widget.name_label.text()

    def test_widget_truncates_long_name(self, qapp):
        """Test that long stock names are truncated."""
        stock = Stock(
            symbol="TEST",
            name="This Is A Very Long Company Name That Should Be Truncated",
            price=100.0,
        )
        widget = StockItemWidget(stock)

        assert len(widget.name_label.text()) <= 25

    def test_update_stock(self, qapp, sample_stock):
        """Test updating stock data."""
        widget = StockItemWidget(sample_stock)

        new_stock = Stock(
            symbol="AAPL",
            name="Apple Inc.",
            price=155.00,
            change=5.00,
            change_percent=3.33,
        )
        widget.update_stock(new_stock)

        assert "155.00" in widget.price_label.text()

    def test_remove_clicked_signal(self, qapp, sample_stock, qtbot):
        """Test that remove button emits signal."""
        widget = StockItemWidget(sample_stock)

        with qtbot.waitSignal(widget.remove_clicked) as blocker:
            widget.remove_btn.click()

        assert blocker.args[0] == "AAPL"


class TestPopupWindow:
    """Tests for the PopupWindow class."""

    def test_popup_creation(self, qapp):
        """Test creating a popup window."""
        popup = PopupWindow()

        assert popup.windowFlags() & Qt.FramelessWindowHint
        assert popup.windowFlags() & Qt.WindowStaysOnTopHint

    def test_popup_initial_size(self, qapp):
        """Test popup has correct initial size."""
        popup = PopupWindow()

        assert popup.width() == 340
        assert popup.height() == 500

    def test_popup_minimum_size(self, qapp):
        """Test popup has minimum size constraints."""
        popup = PopupWindow()

        assert popup.minimumWidth() == 300
        assert popup.minimumHeight() == 350

    def test_set_position(self, qapp):
        """Test setting popup position."""
        popup = PopupWindow()
        popup.set_position(200, 300)

        pos = popup.get_position()
        assert pos == (200, 300)

    def test_get_size(self, qapp):
        """Test getting popup size."""
        popup = PopupWindow()
        popup.resize(400, 500)

        size = popup.get_size()
        assert size == (400, 500)

    def test_update_stocks_adds_widgets(self, qapp, sample_stock):
        """Test that update_stocks adds stock widgets."""
        popup = PopupWindow()
        popup.update_stocks([sample_stock])

        assert "AAPL" in popup._stock_widgets

    def test_update_stocks_updates_existing(self, qapp, sample_stock):
        """Test that update_stocks updates existing widgets."""
        popup = PopupWindow()
        popup.update_stocks([sample_stock])

        updated_stock = Stock(
            symbol="AAPL",
            name="Apple Inc.",
            price=160.00,
            change=10.0,
            change_percent=6.67,
        )
        popup.update_stocks([updated_stock])

        assert len(popup._stock_widgets) == 1
        assert popup._stock_widgets["AAPL"].stock.price == 160.00

    def test_update_stocks_removes_old(self, qapp, sample_stock, sample_stock_down):
        """Test that update_stocks removes stocks not in list."""
        popup = PopupWindow()
        popup.update_stocks([sample_stock, sample_stock_down])
        assert len(popup._stock_widgets) == 2

        popup.update_stocks([sample_stock])  # Remove GOOGL
        assert len(popup._stock_widgets) == 1
        assert "GOOGL" not in popup._stock_widgets

    def test_stock_added_signal(self, qapp, qtbot):
        """Test that adding a stock emits signal."""
        popup = PopupWindow()
        popup.symbol_input.setText("TSLA")

        with qtbot.waitSignal(popup.stock_added) as blocker:
            popup.symbol_input.returnPressed.emit()

        assert blocker.args[0] == "TSLA"

    def test_stock_added_clears_input(self, qapp):
        """Test that input is cleared after adding."""
        popup = PopupWindow()
        popup.symbol_input.setText("TSLA")
        popup._on_add_stock()

        assert popup.symbol_input.text() == ""

    def test_stock_added_uppercase(self, qapp, qtbot):
        """Test that symbols are converted to uppercase."""
        popup = PopupWindow()
        popup.symbol_input.setText("tsla")

        with qtbot.waitSignal(popup.stock_added) as blocker:
            popup._on_add_stock()

        assert blocker.args[0] == "TSLA"

    def test_empty_input_not_added(self, qapp, qtbot):
        """Test that empty input doesn't emit signal."""
        popup = PopupWindow()
        popup.symbol_input.setText("")

        with qtbot.assertNotEmitted(popup.stock_added):
            popup._on_add_stock()

    def test_closed_signal(self, qapp, qtbot):
        """Test that closing emits closed signal."""
        popup = PopupWindow()

        with qtbot.waitSignal(popup.closed):
            popup._on_close()

        assert not popup.isVisible()

    def test_stock_removed_signal(self, qapp, sample_stock, qtbot):
        """Test that removing a stock emits signal."""
        popup = PopupWindow()
        popup.update_stocks([sample_stock])

        with qtbot.waitSignal(popup.stock_removed) as blocker:
            popup._stock_widgets["AAPL"].remove_btn.click()

        assert blocker.args[0] == "AAPL"

    def test_status_label_updated(self, qapp, sample_stock):
        """Test that status label shows last update time."""
        popup = PopupWindow()
        popup.update_stocks([sample_stock])

        assert "Last updated:" in popup.status_label.text()
