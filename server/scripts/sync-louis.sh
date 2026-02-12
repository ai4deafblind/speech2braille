#!/bin/bash
# Sync louis Python bindings from Homebrew installation
set -e

LOUIS_HOME="/opt/homebrew/Cellar/liblouis/3.36.0/lib/python3.14/site-packages/louis"
LOUIS_LOCAL="src/liblouis_bridge/louis"

if [ ! -d "$LOUIS_HOME" ]; then
    echo "Error: Homebrew liblouis not found at $LOUIS_HOME"
    echo "Install with: brew install liblouis"
    exit 1
fi

echo "Syncing louis package from Homebrew..."
rm -rf "$LOUIS_LOCAL"
cp -r "$LOUIS_HOME" "$LOUIS_LOCAL"
echo "✓ Synced louis package"
