#!/bin/bash

# Ensure uv and common tool paths are available when launched from Finder
export PATH="$HOME/.local/bin:$HOME/.cargo/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

# Resolve the directory containing this script
SCRIPT="${BASH_SOURCE[0]:-$0}"
DIR="$( cd "$( dirname "$SCRIPT" )" && pwd )"

cd "$DIR"
clear

# ── Preflight checks ───────────────────────────────────────────────────────────
if ! command -v uv &> /dev/null; then
    echo "Error: uv is not installed. Please run install.sh first."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

if [ ! -f "$DIR/.env" ]; then
    echo "Error: No API key found. Please run install.sh first."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

# ── Run the app ────────────────────────────────────────────────────────────────
PYTHONPATH="$DIR/src" uv run python "$DIR/src/main.py"

# Keep the terminal open if the app exits with an error
if [ $? -ne 0 ]; then
    echo ""
    read -p "Job Agent exited with an error. Press Enter to close..."
fi
