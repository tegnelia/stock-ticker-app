# Stock Ticker

A desktop stock price tracker that lives in your system tray. It displays a floating popup window with real-time prices, daily changes, and sparkline charts.

![Platform](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-blue)
![Python](https://img.shields.io/badge/python-3.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

- **System tray icon** — left-click to toggle the popup, right-click for a context menu
- **Floating popup window** — frameless, always-on-top, draggable and resizable
- **Watchlist management** — add, remove, and reorder stocks
- **Sparkline charts** — inline historical price charts with a previous-close reference line
- **Configurable refresh intervals** — 1, 3, 5, or 10 minutes
- **Multiple chart periods** — 1 day, 1 week, 1 month, 1 year, 5 years, 10 years, all-time
- **Color-coded prices** — green for gains, red for losses
- **Dark theme** — professional dark UI with semi-transparent elements
- **Single instance lock** — prevents duplicate processes
- **Cross-platform** — Linux (amd64) and macOS (arm64)

## Screenshot

The popup displays each stock with its current price, daily change (absolute and percentage), and a sparkline chart. Default watchlist includes major indices: Dow Jones, NASDAQ, S&P 500, and NYSE Composite.

## Requirements

- Python 3.12+
- PySide6 >= 6.5.0
- yfinance >= 0.2.0

## Quick Start

```bash
# Clone the repo
git clone https://github.com/tegnelia/stock-ticker-app.git
cd stock-ticker-app

# Create a virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run the app
python main.py
```

## Building

### Linux (.deb)

```bash
chmod +x build-linux.sh
./build-linux.sh
# Produces: stock-ticker_1.0.0.deb
sudo dpkg -i stock-ticker_1.0.0.deb
```

### macOS (.dmg)

Requires an arm64 Mac.

```bash
chmod +x build-macos.sh
./build-macos.sh
# Produces: stock-ticker_1.0.0.dmg
```

Open the `.dmg` and drag **Stock Ticker** to your Applications folder.

## Configuration

Settings are stored as JSON and persist across sessions:

| OS    | Path                                                    |
|-------|---------------------------------------------------------|
| Linux | `~/.config/stock-ticker/config.json`                    |
| macOS | `~/Library/Application Support/stock-ticker/config.json` |

### Options

| Setting            | Default                          | Description                  |
|--------------------|----------------------------------|------------------------------|
| `watchlist`        | `["^DJI", "^IXIC", "^GSPC", "^NYA"]` | Stock symbols to track  |
| `refresh_interval` | `60`                             | Seconds between updates      |
| `chart_period`     | `"1mo"`                          | Sparkline time range         |
| `popup_position`   | `[100, 100]`                     | Window position (x, y)       |
| `popup_size`       | `[320, 400]`                     | Window size (w, h)           |
| `theme`            | `"dark"`                         | UI theme                     |

## Project Structure

```
stock-ticker-app/
├── main.py                    # Entry point
├── src/
│   ├── app.py                 # Application coordinator + single-instance lock
│   ├── popup.py               # Popup window, stock item widgets, sparklines
│   ├── stock_service.py       # Background data fetching via yfinance
│   ├── tray.py                # System tray icon and menu
│   ├── config.py              # Config loading/saving with platform-aware paths
│   ├── models.py              # Stock and AppConfig dataclasses
│   └── styles/
│       └── theme.qss          # Dark theme stylesheet
├── tests/                     # pytest test suite (92 tests)
├── build-linux.sh             # Linux .deb build script
├── build-macos.sh             # macOS .dmg build script
├── stock-ticker.spec          # PyInstaller spec (Linux)
├── stock-ticker-macos.spec    # PyInstaller spec (macOS arm64)
├── requirements.txt           # Python dependencies
└── .github/workflows/
    └── lint.yml               # CI lint job (ruff)
```

## Testing

```bash
source venv/bin/activate
python -m pytest tests/ -q --tb=short
```

## License

MIT
