#!/usr/bin/env bash
# Installs Devbox on Linux if not already present.
# Used by Claude Code SessionStart hook for cloud sessions.
#
# Containers without a proper init system (PID 1 doesn't reap children)
# cause Nix's sandbox to crash — waitpid() returns ECHILD. We disable
# the sandbox and symlink binaries manually since the installer's
# configure_nix step can get stuck.

set -euo pipefail

if [ "$(uname)" != "Linux" ]; then
    exit 0
fi

if command -v devbox &>/dev/null; then
    exit 0
fi

# Install Devbox (which installs Nix as a dependency)
curl -fsSL https://get.jetify.com/devbox | bash -s -- -f

# Disable Nix sandbox — it crashes in containers without an init system.
mkdir -p /etc/nix
cat >> /etc/nix/nix.conf <<NIX_CONF
sandbox = false
filter-syscalls = false
NIX_CONF
