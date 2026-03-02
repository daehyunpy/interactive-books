#!/usr/bin/env bash
# Installs Nix on Linux if not already present.
# Used by Claude Code SessionStart hook for cloud sessions.
#
# Containers without a proper init system (PID 1 doesn't reap children)
# cause Nix's sandbox to crash — waitpid() returns ECHILD. We disable
# the sandbox after installation.

set -euo pipefail

if command -v nix &>/dev/null; then
    exit 0
fi

if [ "$(uname)" != "Linux" ]; then
    echo "Visit https://nixos.org/download to install it."
    exit 1
fi

sh <(curl --proto '=https' --tlsv1.2 -L https://nixos.org/nix/install) --daemon
