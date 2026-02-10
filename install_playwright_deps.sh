#!/usr/bin/env bash
#
# Install Playwright Chromium system dependencies.
# Requires sudo access.
#
# Usage: ./install_playwright_deps.sh
#
set -euo pipefail

echo "=== Installing Playwright Chromium Dependencies ==="
echo ""
echo "This will install system dependencies using apt-get (requires sudo)."
echo ""

# Detect the correct Python to use (prefer venv if available)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/.venv/bin/python" ]; then
    PYTHON="${SCRIPT_DIR}/.venv/bin/python"
    echo "Using Python from venv: ${PYTHON}"
elif command -v python &> /dev/null; then
    PYTHON="python"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
else
    echo "Error: Python not found"
    exit 1
fi

# Install Playwright's system dependencies for Chromium
# This requires sudo, so we use it directly
sudo "${PYTHON}" -m playwright install-deps chromium

echo ""
echo "=== Done ==="
echo ""
echo "You can now run the scraper without issues."
