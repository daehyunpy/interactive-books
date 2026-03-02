#!/usr/bin/env bash
# Installs Nix on Linux if not already present.
# Used by Claude Code SessionStart hook for cloud sessions.

set -euo pipefail

if command -v nix &>/dev/null; then
    exit 0
fi

if [ "$(uname)" != "Linux" ]; then
    echo "Visit https://nixos.org/download to install it."
    exit 1
fi

sh <(curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install) --no-daemon
