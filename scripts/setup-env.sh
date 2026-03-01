#!/usr/bin/env bash
# Copies .envrc.example and .env.example if the real files don't exist.
# Used by Claude Code SessionStart hook.

set -euo pipefail

if [ ! -f .envrc ] && [ -f .envrc.example ]; then
    cp .envrc.example .envrc
fi

if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
fi
