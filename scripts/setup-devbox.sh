#!/usr/bin/env bash
# Installs Devbox on Linux if not already present.
# Used by Claude Code SessionStart hook for cloud sessions.

set -euo pipefail

if [ "$(uname)" != "Linux" ]; then
    exit 0
fi

if command -v devbox &>/dev/null; then
    exit 0
fi

curl -fsSL https://get.jetify.com/devbox | bash -s -- --yes
