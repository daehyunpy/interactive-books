#!/usr/bin/env bash
# Installs direnv on Linux if not already present.
# Used by Claude Code SessionStart hook for cloud sessions.

set -euo pipefail

if command -v direnv &>/dev/null; then
    exit 0
fi

if [ "$(uname)" != "Linux" ]; then
    echo "Visit https://direnv.net to install it."
    exit 1
fi

curl -sfL https://direnv.net/install.sh | bash
