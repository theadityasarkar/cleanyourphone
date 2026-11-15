#!/usr/bin/env bash
# Downloads Google Android SDK Platform-Tools for Linux/macOS
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST="$REPO/tools/platform-tools"

if [ -f "$DEST/adb" ]; then
    echo "[OK] ADB is already installed at: $DEST/adb"
    exit 0
fi

OS="$(uname -s)"
if [ "$OS" = "Darwin" ]; then
    URL="https://dl.google.com/android/repository/platform-tools-latest-darwin.zip"
else
    URL="https://dl.google.com/android/repository/platform-tools-latest-linux.zip"
fi

ZIP="$REPO/tools/platform-tools.zip"
echo "Downloading Android SDK Platform-Tools from Google..."
curl -fsSL -o "$ZIP" "$URL"

echo "Extracting..."
unzip -q -o "$ZIP" -d "$REPO/tools"
rm -f "$ZIP"
chmod +x "$DEST/adb"

echo "[SUCCESS] adb is ready at $DEST/adb"
