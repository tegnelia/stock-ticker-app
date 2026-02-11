#!/bin/bash
# Build script for Stock Ticker App
# Creates a .deb package from the current source code

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.0.0"
PACKAGE_NAME="stock-ticker"
DEB_DIR="packaging/${PACKAGE_NAME}_${VERSION}"

echo "=== Stock Ticker Build Script ==="
echo ""

# Step 1: Activate virtual environment
echo "[1/5] Activating virtual environment..."
source venv/bin/activate

# Step 2: Run tests
echo "[2/5] Running tests..."
python -m pytest tests/ -q --tb=short
if [ $? -ne 0 ]; then
    echo "ERROR: Tests failed. Aborting build."
    exit 1
fi
echo "Tests passed!"

# Step 3: Build with PyInstaller
echo "[3/5] Building executable with PyInstaller..."
pyinstaller --clean --noconfirm stock-ticker.spec 2>&1 | tail -5

# Step 4: Prepare .deb package structure
echo "[4/5] Preparing .deb package..."
rm -rf "$DEB_DIR"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/64x64/apps"

# Copy binary
cp dist/stock-ticker "$DEB_DIR/usr/bin/"
chmod 755 "$DEB_DIR/usr/bin/stock-ticker"

# Create control file
cat > "$DEB_DIR/DEBIAN/control" << EOF
Package: ${PACKAGE_NAME}
Version: ${VERSION}
Section: finance
Priority: optional
Architecture: amd64
Maintainer: Your Name <your.email@example.com>
Description: Stock Ticker - Desktop stock price tracker
 A Linux desktop application that displays stock prices in a
 system tray with a floating, interactive popup window.
 Features include real-time price updates, sparkline charts,
 configurable refresh intervals, and watchlist management.
EOF

# Create desktop entry
cat > "$DEB_DIR/usr/share/applications/stock-ticker.desktop" << EOF
[Desktop Entry]
Name=Stock Ticker
Comment=Track stock prices with a floating popup
Exec=/usr/bin/stock-ticker
Icon=stock-ticker
Terminal=false
Type=Application
Categories=Finance;Office;
Keywords=stocks;finance;trading;market;
StartupNotify=true
EOF

# Create icon
cat > "$DEB_DIR/usr/share/icons/hicolor/64x64/apps/stock-ticker.svg" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="32" r="28" fill="#6C63FF"/>
  <text x="32" y="44" font-family="Arial" font-size="32" font-weight="bold" fill="white" text-anchor="middle">$</text>
</svg>
EOF

# Step 5: Build .deb package
echo "[5/5] Building .deb package..."
dpkg-deb --build "$DEB_DIR" "${PACKAGE_NAME}_${VERSION}.deb"

echo ""
echo "=== Build Complete ==="
echo "Package: ${PACKAGE_NAME}_${VERSION}.deb"
ls -lh "${PACKAGE_NAME}_${VERSION}.deb"
echo ""
echo "To install: sudo dpkg -i ${PACKAGE_NAME}_${VERSION}.deb"
