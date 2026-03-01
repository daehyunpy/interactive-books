#!/bin/bash
set -euo pipefail

# Universal dependency sync — runs on all platforms.
# Installs/syncs Python (uv) and Node (bunx) dependencies.

# ---------------------------------------------------------------------------
# 1. Python — install uv if needed, then sync
# ---------------------------------------------------------------------------
if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Persist uv on PATH for the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi

echo "Running uv sync..."
cd "$CLAUDE_PROJECT_DIR/python"
uv sync

# ---------------------------------------------------------------------------
# 2. Node — install bun if needed, then sync
# ---------------------------------------------------------------------------
if ! command -v bun &>/dev/null; then
    echo "Installing bun..."
    curl -fsSL https://bun.sh/install | bash
    export PATH="$HOME/.bun/bin:$PATH"
fi

# Persist bun on PATH for the rest of the session.
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
    echo 'export PATH="$HOME/.bun/bin:$PATH"' >> "$CLAUDE_ENV_FILE"
fi

echo "Running bunx sync..."
cd "$CLAUDE_PROJECT_DIR"
bunx sync

echo "Dependencies synced."
