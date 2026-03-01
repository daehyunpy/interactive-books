#!/bin/bash
set -euo pipefail

# Cloud environment setup script for Swift development.
# Paste into the "Setup script" field in Claude Code cloud environment settings.
# Runs once on new sessions (skipped on resume). Uses "Trusted" network access.

SWIFT_VERSION="6.1.2"
SWIFT_TAG="swift-${SWIFT_VERSION}-RELEASE"
SWIFT_PLATFORM="ubuntu24.04"

# ---------------------------------------------------------------------------
# 1. Install Swift toolchain
# ---------------------------------------------------------------------------
if ! command -v swift &>/dev/null; then
  echo "Installing Swift ${SWIFT_VERSION}..."

  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    binutils \
    libc6-dev \
    libcurl4-openssl-dev \
    libstdc++-13-dev \
    > /dev/null 2>&1

  SWIFT_BRANCH="${SWIFT_TAG,,}"
  SWIFT_PLATFORM_SLUG="${SWIFT_PLATFORM//./}"
  SWIFT_URL="https://download.swift.org/${SWIFT_BRANCH}/${SWIFT_PLATFORM_SLUG}/${SWIFT_TAG}/${SWIFT_TAG}-${SWIFT_PLATFORM}.tar.gz"

  if ! curl -fsSL "$SWIFT_URL" | tar xz -C /opt; then
    echo "ERROR: Failed to download Swift toolchain from ${SWIFT_URL}"
    echo "The domain download.swift.org may be blocked by the network proxy."
    echo "Swift build and test commands will not be available."
  else
    for bin in /opt/${SWIFT_TAG}-${SWIFT_PLATFORM}/usr/bin/*; do
      ln -sf "$bin" /usr/local/bin/
    done
    echo "Installed $(swift --version 2>&1 | head -1)"
  fi
fi

# ---------------------------------------------------------------------------
# 2. Install SwiftLint (from GitHub releases — Linux amd64 binary)
# ---------------------------------------------------------------------------
if ! command -v swiftlint &>/dev/null; then
  echo "Installing SwiftLint..."
  SWIFTLINT_VERSION="0.63.2"
  SWIFTLINT_URL="https://github.com/realm/SwiftLint/releases/download/${SWIFTLINT_VERSION}/swiftlint_linux_amd64.zip"

  curl -fsSL "$SWIFTLINT_URL" -o /tmp/swiftlint.zip
  unzip -oq /tmp/swiftlint.zip -d /tmp/swiftlint
  # Use static binary — does not require Swift toolchain's libsourcekitdInProc.so
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

# ---------------------------------------------------------------------------
# 4. Resolve Swift package dependencies (only if Swift is available)
# ---------------------------------------------------------------------------
if command -v swift &>/dev/null; then
  echo "Resolving Swift package dependencies..."
  cd "$CLAUDE_PROJECT_DIR/swift/InteractiveBooks"
  swift package resolve
fi

echo "Swift development environment ready."
