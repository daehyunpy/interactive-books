#!/usr/bin/env bash
# Ensures Nix is installed and on PATH for Linux cloud sessions.
# Handles three scenarios:
#   1. Nix already on PATH → exit early.
#   2. Nix in store but profile broken (partial Determinate install) → repair.
#   3. No Nix at all → fresh install via Determinate installer.
# Used by Claude Code SessionStart hook.

set -euo pipefail

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
        if [ -x "$candidate" ] && "$candidate" --version &>/dev/null; then
            NIX_BIN="$candidate"
            break
        fi
    done

    if [ -n "$NIX_BIN" ]; then
        NIX_STORE_DIR="$(dirname "$(dirname "$NIX_BIN")")"
        PROFILE_DIR="/nix/var/nix/profiles/per-user/root"

        # Create the profile symlink if missing.
        mkdir -p "$PROFILE_DIR"
        if [ ! -e "$PROFILE_DIR/profile" ]; then
            ln -sfn "$NIX_STORE_DIR" "$PROFILE_DIR/profile"
            echo "Created profile symlink: $PROFILE_DIR/profile -> $NIX_STORE_DIR"
        fi

        # Ensure the default profile points to the per-user profile.
        if [ ! -e /nix/var/nix/profiles/default ] || [ ! -e "$(readlink -f /nix/var/nix/profiles/default)/bin/nix" ]; then
            ln -sfn "$PROFILE_DIR/profile" /nix/var/nix/profiles/default
            echo "Fixed default profile symlink."
        fi

        # Ensure ~/.nix-profile exists.
        if [ ! -e "$HOME/.nix-profile" ] || [ ! -e "$(readlink -f "$HOME/.nix-profile")/bin/nix" ]; then
            ln -sfn "$PROFILE_DIR/profile" "$HOME/.nix-profile"
            echo "Fixed ~/.nix-profile symlink."
        fi

        # Install shell integration into /etc/profile.d/ so subsequent hooks see nix.
        NIX_PROFILE_SCRIPT="$NIX_STORE_DIR/etc/profile.d/nix-daemon.sh"
        if [ ! -f "$NIX_PROFILE_SCRIPT" ]; then
            NIX_PROFILE_SCRIPT="$NIX_STORE_DIR/etc/profile.d/nix.sh"
        fi
        if [ -f "$NIX_PROFILE_SCRIPT" ] && [ ! -f /etc/profile.d/nix.sh ]; then
            cp "$NIX_PROFILE_SCRIPT" /etc/profile.d/nix.sh
            echo "Installed /etc/profile.d/nix.sh"
        fi

        # Source it now so the rest of this session can use nix.
        if [ -f /etc/profile.d/nix.sh ]; then
            set +u  # nix.sh uses unset variables
            # shellcheck disable=SC1091
            . /etc/profile.d/nix.sh
            set -u
        fi

        # Also add to bashrc for interactive shells.
        BASHRC="/root/.bashrc"
        if [ -f "$BASHRC" ] && ! grep -q 'profile.d/nix.sh' "$BASHRC" 2>/dev/null; then
            printf '\n# Nix\nif [ -e /etc/profile.d/nix.sh ]; then . /etc/profile.d/nix.sh; fi\n' >> "$BASHRC"
            echo "Added nix sourcing to $BASHRC"
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
        /nix/nix-installer uninstall --no-confirm 2>/dev/null || true
    fi
fi

# --- Scenario 3: Fresh install ---
echo "Installing Nix..."
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | \
    sh -s -- install linux --no-confirm --init none

# Source the newly installed profile.
if [ -f /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
    set +u
    # shellcheck disable=SC1091
    . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
    set -u
fi

echo "Nix installed: $(nix --version 2>/dev/null || echo 'unknown version')"
