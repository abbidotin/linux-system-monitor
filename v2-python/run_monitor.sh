#!/usr/bin/env bash
# Quick launcher script for Linux systems

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if python3 is available
if ! command -v python3 &>/dev/null; then
    echo "Error: python3 is not installed or not in PATH."
    exit 1
fi

# Check / install dependencies if needed
if ! python3 -c "import psutil, matplotlib" &>/dev/null; then
    echo "Installing required dependencies..."
    python3 -m pip install -r requirements.txt
fi

MODE="${1:-snapshot}"
echo "Running System Health Monitor in mode: $MODE"
python3 main.py "$@"
