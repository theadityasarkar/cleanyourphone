#!/usr/bin/env bash
# Shell script to safely debloat an Android Phone over USB Debugging
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS="$REPO/tools"

if [ $# -lt 1 ]; then
    echo "Usage: ./tools/disable.sh <examples/poco-m4-5g/debloat-safe.txt>"
    exit 2
fi

LIST="$(realpath "$1")"
PY="python3"
if ! command -v "$PY" &>/dev/null; then
    PY="python"
fi

if ! command -v "$PY" &>/dev/null; then
    echo "Error: Python 3 is required."
    exit 2
fi

# Ensure ADB is available
if ! command -v adb &>/dev/null && [ ! -f "$TOOLS/platform-tools/adb" ]; then
    echo "ADB not found. Automatically downloading Google Android SDK Platform-Tools..."
    bash "$TOOLS/get-platform-tools.sh"
fi

echo "=========================================================="
echo " CleanYourPhone: Debloating Phone via USB Debugging"
echo " List: $LIST"
echo "=========================================================="

# Safety check
echo -e "\n[*] Running Safety Guard Check..."
"$PY" "$TOOLS/recovery.py" --check-safety "$LIST"

# Save recovery baseline
echo -e "\n[*] Recording Recovery Baseline..."
"$PY" "$TOOLS/recovery.py" --save "$LIST"

echo -e "\n[*] Disabling packages..."
while IFS= read -r line || [ -n "$line" ]; do
    cleaned="$(echo "$line" | sed 's/#.*//' | tr -d '\r' | xargs)"
    if [ -z "$cleaned" ]; then
        continue
    fi
    pkg="$(echo "$cleaned" | awk '{print $1}')"
    echo -n "  -> Disabling $pkg ... "
    res="$("$PY" "$TOOLS/phone.py" "pm disable-user --user 0 $pkg" 2>&1 || true)"
    if [[ "$res" =~ "new state: disabled" ]]; then
        echo "[DISABLED]"
    elif [[ "$res" =~ "not installed" || "$res" =~ "unknown package" ]]; then
        echo "[NOT INSTALLED]"
    else
        echo "[$res]"
    fi
done < "$LIST"

echo -e "\n[*] Syncing disk cache on device..."
"$PY" "$TOOLS/phone.py" "sync" >/dev/null 2>&1 || true

echo -e "\n=========================================================="
echo " [SUCCESS] Debloat complete!"
echo " To restore at any time, run:"
echo "   ./tools/restore.sh $1"
echo "=========================================================="
