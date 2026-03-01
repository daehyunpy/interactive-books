#!/bin/bash
set -euo pipefail

# General-purpose Swift development setup for Claude Code cloud environments.
# Installs Swift toolchain, SwiftLint, and SwiftFormat.

# ---------------------------------------------------------------------------
# 1. Install Swift toolchain via official apt repository
# ---------------------------------------------------------------------------
if ! command -v swift &>/dev/null; then
  echo "Installing Swift toolchain via apt..."

  # Add the Swift signing key and apt repository
  curl -fsSL https://download.swift.org/swift-signing-key-4.asc \
    | gpg --dearmor -o /usr/share/keyrings/swift-archive-keyring.gpg
  echo "deb [signed-by=/usr/share/keyrings/swift-archive-keyring.gpg] https://download.swift.org/apt/ubuntu2404 noble main" \
    > /etc/apt/sources.list.d/swift.list

  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq swiftlang > /dev/null 2>&1

  echo "Installed $(swift --version 2>&1 | head -1)"
fi

# ---------------------------------------------------------------------------
# 2. Install SwiftLint (from GitHub releases — Linux amd64 static binary)
# ---------------------------------------------------------------------------
if ! command -v swiftlint &>/dev/null; then
  echo "Installing SwiftLint..."
  SWIFTLINT_VERSION="0.63.2"
  SWIFTLINT_URL="https://github.com/realm/SwiftLint/releases/download/${SWIFTLINT_VERSION}/swiftlint_linux_amd64.zip"

  curl -fsSL "$SWIFTLINT_URL" -o /tmp/swiftlint.zip
  unzip -oq /tmp/swiftlint.zip -d /tmp/swiftlint
  install -m 755 /tmp/swiftlint/swiftlint-static /usr/local/bin/swiftlint
  rm -rf /tmp/swiftlint.zip /tmp/swiftlint

  echo "Installed SwiftLint $(swiftlint version)"
fi

# ---------------------------------------------------------------------------
# 3. Install SwiftFormat (from GitHub releases — Linux binary)
# ---------------------------------------------------------------------------
if ! command -v swiftformat &>/dev/null; then
  echo "Installing SwiftFormat..."
  SWIFTFORMAT_VERSION="0.59.1"
  SWIFTFORMAT_URL="https://github.com/nicklockwood/SwiftFormat/releases/download/${SWIFTFORMAT_VERSION}/swiftformat_linux.zip"

  curl -fsSL "$SWIFTFORMAT_URL" -o /tmp/swiftformat.zip
  unzip -oq /tmp/swiftformat.zip -d /tmp/swiftformat
  install -m 755 /tmp/swiftformat/swiftformat_linux /usr/local/bin/swiftformat
  rm -rf /tmp/swiftformat.zip /tmp/swiftformat

  echo "Installed SwiftFormat $(swiftformat --version)"
fi

echo "Swift development environment ready."
