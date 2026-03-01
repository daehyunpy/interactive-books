#!/bin/bash
set -euo pipefail

# General-purpose Swift development setup for Claude Code cloud environments.
# Installs the latest Swift toolchain, SwiftLint, and SwiftFormat.

# ---------------------------------------------------------------------------
# 1. Install Swift toolchain via official apt repository
# ---------------------------------------------------------------------------
if ! command -v swift &>/dev/null; then
  echo "Installing Swift toolchain via apt..."

  if curl -fsSL https://download.swift.org/swift-signing-key-4.asc \
       | gpg --dearmor -o /usr/share/keyrings/swift-archive-keyring.gpg 2>/dev/null; then
    echo "deb [signed-by=/usr/share/keyrings/swift-archive-keyring.gpg] https://download.swift.org/apt/ubuntu2404 noble main" \
      > /etc/apt/sources.list.d/swift.list

    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq swiftlang > /dev/null 2>&1

    echo "Installed $(swift --version 2>&1 | head -1)"
  else
    echo "WARNING: Could not reach download.swift.org — skipping Swift toolchain."
  fi
fi

# ---------------------------------------------------------------------------
# 2. Install SwiftLint (latest from GitHub releases)
# ---------------------------------------------------------------------------
if ! command -v swiftlint &>/dev/null; then
  echo "Installing SwiftLint (latest)..."

  curl -fsSL "https://github.com/realm/SwiftLint/releases/latest/download/swiftlint_linux_amd64.zip" \
    -o /tmp/swiftlint.zip
  unzip -oq /tmp/swiftlint.zip -d /tmp/swiftlint
  install -m 755 /tmp/swiftlint/swiftlint-static /usr/local/bin/swiftlint
  rm -rf /tmp/swiftlint.zip /tmp/swiftlint

  echo "Installed SwiftLint $(swiftlint version)"
fi

# ---------------------------------------------------------------------------
# 3. Install SwiftFormat (latest from GitHub releases)
# ---------------------------------------------------------------------------
if ! command -v swiftformat &>/dev/null; then
  echo "Installing SwiftFormat (latest)..."

  curl -fsSL "https://github.com/nicklockwood/SwiftFormat/releases/latest/download/swiftformat_linux.zip" \
    -o /tmp/swiftformat.zip
  unzip -oq /tmp/swiftformat.zip -d /tmp/swiftformat
  install -m 755 /tmp/swiftformat/swiftformat_linux /usr/local/bin/swiftformat
  rm -rf /tmp/swiftformat.zip /tmp/swiftformat

  echo "Installed SwiftFormat $(swiftformat --version)"
fi

echo "Swift development environment ready."
