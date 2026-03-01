#!/bin/bash
set -euo pipefail

# SessionStart hook — runs in all environments.
# Delegates to the main orchestrator which handles OS detection
# and universal dependency sync (uv, bunx).

exec "$CLAUDE_PROJECT_DIR/scripts/session-start.sh"
