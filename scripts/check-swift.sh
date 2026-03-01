#!/usr/bin/env bash
# Verifies that Swift is available on macOS.
# Used by Claude Code SessionStart hook.

set -euo pipefail

if [ "$(uname)" != "Darwin" ]; then
    exit 0
fi

if command -v swift &>/dev/null; then
    exit 0
fi

echo "Error: Swift not found. Please install Swift and restart the session."
exit 1
