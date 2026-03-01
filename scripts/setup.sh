#!/bin/bash
set -euo pipefail
# General-purpose Swift development setup for Claude Code cloud environments.
# Installs the Swift toolchain, SwiftLint, and SwiftFormat.
# ---------------------------------------------------------------------------
# 1. Install Swift toolchain via official tarball
# ---------------------------------------------------------------------------
if ! command -v swift &>/dev/null; then
  echo "Installing Swift toolchain..."
  UBUNTU_CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
  case "$UBUNTU_CODENAME" in
    noble)   SWIFT_PLATFORM="ubuntu2404" ; SWIFT_OS="ubuntu24.04" ;;
    jammy)   SWIFT_PLATFORM="ubuntu2204" ; SWIFT_OS="ubuntu22.04" ;;
    focal)   SWIFT_PLATFORM="ubuntu2004" ; SWIFT_OS="ubuntu20.04" ;;
    *)
      echo "WARNING: Unsupported Ubuntu version ($UBUNTU_CODENAME). Attempting noble..."
      SWIFT_PLATFORM="ubuntu2404"
      SWIFT_OS="ubuntu24.04"
      ;;
  esac
  # Install prerequisites
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    curl gnupg2 unzip > /dev/null 2>&1
  SWIFT_VERSION="6.0.3"
  SWIFT_URL="https://download.swift.org/swift-${SWIFT_VERSION}-release/${SWIFT_PLATFORM}/swift-${SWIFT_VERSION}-RELEASE/swift-${SWIFT_VERSION}-RELEASE-${SWIFT_OS}.tar.gz"
  echo "Downloading Swift ${SWIFT_VERSION} for ${SWIFT_OS}..."
  curl -fsSL "$SWIFT_URL" -o /tmp/swift.tar.gz
  echo "Extracting..."
  tar -xzf /tmp/swift.tar.gz -C /usr/local --strip-components=2
  rm /tmp/swift.tar.gz
  if command -v swift &>/dev/null; then
    echo "Installed $(swift --version 2>&1 | head -1)"
  else
    echo "ERROR: Swift installation failed."
    exit 1
  fi
fi
# ---------------------------------------------------------------------------
# 2. Install SwiftLint (latest from GitHub releases)
# ---------------------------------------------------------------------------
if ! command -v swiftlint &>/dev/null; then
  echo "Installing SwiftLint (latest)..."
  SWIFTLINT_URL=$(curl -fsSL "https://api.github.com/repos/realm/SwiftLint/releases/latest" \
    | grep -o '"browser_download_url": *"[^"]*linux[^"]*"' \
    | head -1 \
    | cut -d'"' -f4)
  if [ -n "$SWIFTLINT_URL" ]; then
    curl -fsSL "$SWIFTLINT_URL" -o /tmp/swiftlint.zip
    unzip -oq /tmp/swiftlint.zip -d /tmp/swiftlint
    # Find the actual binary (name varies across releases)
    SWIFTLINT_BIN=$(find /tmp/swiftlint -type f -executable | head -1)
    if [ -z "$SWIFTLINT_BIN" ]; then
      SWIFTLINT_BIN=$(find /tmp/swiftlint -name '*swiftlint*' -type f | head -1)
      chmod +x "$SWIFTLINT_BIN"
    fi
    install -m 755 "$SWIFTLINT_BIN" /usr/local/bin/swiftlint
    rm -rf /tmp/swiftlint.zip /tmp/swiftlint
    echo "Installed SwiftLint $(swiftlint version)"
  else
    echo "WARNING: Could not determine SwiftLint download URL — skipping."
  fi
fi
# ---------------------------------------------------------------------------
# 3. Install SwiftFormat (latest from GitHub releases)
# ---------------------------------------------------------------------------
if ! command -v swiftformat &>/dev/null; then
  echo "Installing SwiftFormat (latest)..."
  SWIFTFORMAT_URL=$(curl -fsSL "https://api.github.com/repos/nicklockwood/SwiftFormat/releases/latest" \
    | grep -o '"browser_download_url": *"[^"]*linux[^"]*"' \
    | head -1 \
    | cut -d'"' -f4)
  if [ -n "$SWIFTFORMAT_URL" ]; then
    curl -fsSL "$SWIFTFORMAT_URL" -o /tmp/swiftformat.zip
    unzip -oq /tmp/swiftformat.zip -d /tmp/swiftformat
    # Find the actual binary
    SWIFTFORMAT_BIN=$(find /tmp/swiftformat -type f -executable | head -1)
    if [ -z "$SWIFTFORMAT_BIN" ]; then
      SWIFTFORMAT_BIN=$(find /tmp/swiftformat -name '*swiftformat*' -type f | head -1)
      chmod +x "$SWIFTFORMAT_BIN"
    fi
    install -m 755 "$SWIFTFORMAT_BIN" /usr/local/bin/swiftformat
    rm -rf /tmp/swiftformat.zip /tmp/swiftformat
    echo "Installed SwiftFormat $(swiftformat --version)"
  else
    echo "WARNING: Could not determine SwiftFormat download URL — skipping."
  fi
fi
# ---------------------------------------------------------------------------
# 4. Resolve Swift packages if applicable
# ---------------------------------------------------------------------------
if [ -f "Package.swift" ]; then
  echo "Resolving Swift packages..."
  swift package resolve
fi
echo "Swift development environment ready."
