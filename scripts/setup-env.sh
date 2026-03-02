#!/usr/bin/env bash
# Copies .envrc.example and .env.example if the real files don't exist.
# Used by Claude Code SessionStart hook.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

if [ ! -f "$ROOT/.envrc" ] && [ -f "$ROOT/.envrc.example" ]; then
    cp "$ROOT/.envrc.example" "$ROOT/.envrc"
fi

if [ ! -f "$ROOT/.env" ] && [ -f "$ROOT/.env.example" ]; then
    cp "$ROOT/.env.example" "$ROOT/.env"
fi
