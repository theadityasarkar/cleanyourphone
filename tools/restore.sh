#!/usr/bin/env bash
# Shell script to restore disabled packages on an Android Phone
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TOOLS="$REPO/tools"

if [ $# -lt 1 ]; then
    echo "Usage: ./tools/restore.sh <examples/poco-m4-5g/debloat-safe.txt>"
    exit 2
fi

LIST="$(realpath "$1")"
PY="python3"
if ! command -v "$PY" &>/dev/null; then
    PY="python"
fi

echo "=========================================================="
echo " CleanYourPhone: Restoring Packages via USB Debugging"
echo " List: $LIST"
echo "=========================================================="

echo -e "\n[*] Generating restore commands from baseline record..."
"$PY" "$TOOLS/recovery.py" --commands "$LIST" | while IFS= read -r cmd; do
    if [[ "$cmd" =~ ^pm\ enable\ (.*)$ ]]; then
        pkg="${BASH_REMATCH[1]}"
        echo -n "  <- Restoring $pkg ... "
        res="$("$PY" "$TOOLS/phone.py" "$cmd" 2>&1 || true)"
        if [[ "$res" =~ "new state: enabled" || "$res" =~ "new state: default" ]]; then
            echo "[ENABLED]"
        else
            echo "[$res]"
        fi
    fi
done

echo -e "\n[*] Syncing disk cache on device..."
"$PY" "$TOOLS/phone.py" "sync" >/dev/null 2>&1 || true

echo -e "\n=========================================================="
echo " [SUCCESS] Restore complete!"
echo "=========================================================="
