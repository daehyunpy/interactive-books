#!/usr/bin/env bash
# Installs Devbox on Linux if not already present.
# Used by Claude Code SessionStart hook for cloud sessions.

set -euo pipefail

if command -v devbox &>/dev/null; then
    exit 0
fi

if [ "$(uname)" != "Linux" ]; then
    echo "Error: Devbox not found. Visit https://www.jetify.com/devbox to install it."
    exit 1
fi

curl -fsSL https://get.jetify.com/devbox | bash -s -- --force
