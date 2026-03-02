#!/usr/bin/env bash
# Ensures Nix is installed and on PATH for Linux cloud sessions.
# Handles three scenarios:
#   1. Nix already on PATH → exit early.
#   2. Nix in store but profile broken (partial Determinate install) → repair.
#   3. No Nix at all → fresh install via Determinate installer.
# Used by Claude Code SessionStart hook.

set -euo pipefail

SYSTEM_NIX_PROFILE="/etc/profile.d/nix.sh"
DEFAULT_PROFILE="/nix/var/nix/profiles/default"
CURRENT_USER="$(whoami)"
PROFILE_DIR="/nix/var/nix/profiles/per-user/$CURRENT_USER"

source_nix_profile() {
    local script="$1"
    if [ -f "$script" ]; then
        set +u  # nix.sh references unset variables
        # shellcheck disable=SC1090
        . "$script"
        set -u
    fi
}

# --- Scenario 1: Nix already works ---
if command -v nix &>/dev/null; then
    exit 0
fi

if [ "$(uname)" != "Linux" ]; then
    echo "Nix not found. Visit https://nixos.org/download to install it."
    exit 1
fi

# --- Scenario 2: Nix store exists but profile/PATH is broken ---
# The Determinate installer can leave /nix/store populated but profiles unlinked
# (e.g., setup_default_profile stuck in "Progress" in a container without systemd).
if [ -d /nix/store ]; then
    echo "Found /nix/store but nix is not on PATH. Attempting repair..."

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

        # Wire up profile symlinks. ln -sfn is idempotent — no guards needed.
        mkdir -p "$PROFILE_DIR"
        ln -sfn "$NIX_STORE_DIR" "$PROFILE_DIR/profile"
        ln -sfn "$PROFILE_DIR/profile" "$DEFAULT_PROFILE"
        ln -sfn "$PROFILE_DIR/profile" "$HOME/.nix-profile"

        # Install shell integration so subsequent hooks see nix.
        NIX_PROFILE_SCRIPT="$NIX_STORE_DIR/etc/profile.d/nix-daemon.sh"
        if [ ! -f "$NIX_PROFILE_SCRIPT" ]; then
            NIX_PROFILE_SCRIPT="$NIX_STORE_DIR/etc/profile.d/nix.sh"
        fi
        if [ -f "$NIX_PROFILE_SCRIPT" ] && [ ! -f "$SYSTEM_NIX_PROFILE" ]; then
            cp "$NIX_PROFILE_SCRIPT" "$SYSTEM_NIX_PROFILE"
            echo "Installed $SYSTEM_NIX_PROFILE"
        fi

        source_nix_profile "$SYSTEM_NIX_PROFILE"

        # Add to bashrc for interactive shells (guard prevents duplicate appends).
        BASHRC="$HOME/.bashrc"
        if [ -f "$BASHRC" ] && ! grep -q 'profile.d/nix.sh' "$BASHRC" 2>/dev/null; then
            printf '\n# Nix\nif [ -e %s ]; then . %s; fi\n' "$SYSTEM_NIX_PROFILE" "$SYSTEM_NIX_PROFILE" >> "$BASHRC"
        fi

        if command -v nix &>/dev/null; then
            echo "Nix repaired successfully: $(nix --version 2>/dev/null)"
            exit 0
        else
            echo "Profile repair did not put nix on PATH. Falling through to fresh install."
        fi
    else
        echo "No working nix binary found in /nix/store. Falling through to fresh install."
    fi

    # Clean up the broken installation before reinstalling.
    if [ -x /nix/nix-installer ]; then
        echo "Uninstalling broken Nix installation..."
        /nix/nix-installer uninstall --no-confirm || true
    fi
fi

# --- Scenario 3: Fresh install ---
echo "Installing Nix..."
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | \
    sh -s -- install linux --no-confirm --init none

source_nix_profile "$DEFAULT_PROFILE/etc/profile.d/nix-daemon.sh"

echo "Nix installed: $(nix --version 2>/dev/null || echo 'unknown version')"
