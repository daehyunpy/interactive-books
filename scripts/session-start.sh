#!/bin/bash
set -euo pipefail

# Main session startup orchestrator.
# Detects OS and architecture, then runs platform-specific setup scripts.
# Universal dependency syncs (uv, bunx) run on all platforms.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OS=$(uname -s)
ARCH=$(uname -m)

echo "Detected OS: $OS, Architecture: $ARCH"

# ---------------------------------------------------------------------------
# Platform-specific setup (Linux only)
# ---------------------------------------------------------------------------
case "$OS" in
    Linux)
        echo "Running Linux-specific setup scripts..."
        "$SCRIPT_DIR/setup-swift.sh"
        ;;
esac

# ---------------------------------------------------------------------------
# Universal dependency sync (all platforms)
# ---------------------------------------------------------------------------
"$SCRIPT_DIR/setup-deps.sh"

echo "Session startup complete."
