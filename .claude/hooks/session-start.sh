#!/bin/bash
set -euo pipefail

# SessionStart hook for Claude Code on the web.
# Only runs in remote environments; delegates to the main orchestrator.

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
    exit 0
fi

exec "$CLAUDE_PROJECT_DIR/scripts/session-start.sh"
