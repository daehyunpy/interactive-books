#!/usr/bin/env bash
# Ensures Nix is installed and on PATH for Linux cloud sessions.
# Strategy: symlink nix binaries into /usr/local/bin (already on PATH)
# so they're available in all shells without PATH manipulation.
# Used by Claude Code SessionStart hook.

set -euo pipefail

# --- Already works ---
if command -v nix &>/dev/null; then
    exit 0
fi

if [ "$(uname)" != "Linux" ]; then
    echo "Nix not found. Visit https://nixos.org/download to install it."
    exit 1
fi

CURRENT_USER="$(whoami)"
PROFILE_DIR="/nix/var/nix/profiles/per-user/$CURRENT_USER"
DEFAULT_PROFILE="/nix/var/nix/profiles/default"

# --- Nix store exists but not on PATH ---
if [ -d /nix/store ]; then
    echo "Found /nix/store but nix is not on PATH. Repairing..."

    # Find a working nix binary in the store.
    NIX_BIN=""
    for candidate in /nix/store/*/bin/nix; do
        if [ -x "$candidate" ]; then
            NIX_BIN="$candidate"
            break
        fi
    done

    if [ -n "$NIX_BIN" ]; then
        NIX_STORE_DIR="${NIX_BIN%/bin/nix}"

        # Wire up profile symlinks so nix-env/devbox can manage packages.
        mkdir -p "$PROFILE_DIR"
        ln -sfn "$NIX_STORE_DIR" "$PROFILE_DIR/profile"
        ln -sfn "$PROFILE_DIR/profile" "$DEFAULT_PROFILE"
        ln -sfn "$PROFILE_DIR/profile" "$HOME/.nix-profile"

        # Symlink nix binaries into /usr/local/bin (already on PATH).
        for bin in "$DEFAULT_PROFILE/bin"/*; do
            [ -x "$bin" ] && ln -sf "$bin" /usr/local/bin/
        done

        echo "Nix repaired: $(nix --version 2>/dev/null)"
        exit 0
    fi

    # No working binary found — clean up before fresh install.
    if [ -x /nix/nix-installer ]; then
        echo "Uninstalling broken Nix..."
        /nix/nix-installer uninstall --no-confirm || true
    fi
fi

# --- Fresh install ---
echo "Installing Nix..."
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | \
    sh -s -- install linux --no-confirm --init none

# Symlink into /usr/local/bin so it's on PATH for all shells.
for bin in "$DEFAULT_PROFILE/bin"/*; do
    [ -x "$bin" ] && ln -sf "$bin" /usr/local/bin/
done

echo "Nix installed: $(nix --version 2>/dev/null || echo 'unknown version')"
