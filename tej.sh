#!/bin/bash
# TejStrike AI - Linux/Kali Quick Launcher
# chmod +x tej.sh && ./tej.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 &> /dev/null; then
    python3 tej_ai.py "$@"
elif command -v python &> /dev/null; then
    python tej_ai.py "$@"
else
    echo "Error: Python 3.8+ is required"
    echo "Install with: sudo apt install python3"
    exit 1
fi
