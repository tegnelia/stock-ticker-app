#!/bin/bash
# Build script for Stock Ticker App (macOS arm64)
# Creates a .dmg installer from the current source code

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

VERSION="1.0.0"
APP_NAME="Stock Ticker"
DMG_NAME="stock-ticker_${VERSION}.dmg"

echo "=== Stock Ticker macOS Build Script ==="
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
echo "[3/5] Building .app bundle with PyInstaller..."
pyinstaller --clean --noconfirm stock-ticker-macos.spec 2>&1 | tail -5

# Step 4: Create .dmg
echo "[4/5] Creating .dmg installer..."
DMG_STAGING="dist/dmg-staging"
rm -rf "$DMG_STAGING"
mkdir -p "$DMG_STAGING"

# Copy .app bundle into staging area
cp -R "dist/${APP_NAME}.app" "$DMG_STAGING/"

# Create symlink to /Applications for drag-and-drop install
ln -s /Applications "$DMG_STAGING/Applications"

# Remove any existing .dmg
rm -f "$DMG_NAME"

# Create .dmg using hdiutil
hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_STAGING" \
    -ov \
    -format UDZO \
    "$DMG_NAME"

# Clean up staging directory
rm -rf "$DMG_STAGING"

# Step 5: Done
echo "[5/5] Verifying output..."
echo ""
echo "=== Build Complete ==="
echo "Installer: ${DMG_NAME}"
ls -lh "$DMG_NAME"
echo ""
echo "To install: Open ${DMG_NAME} and drag Stock Ticker to Applications"
