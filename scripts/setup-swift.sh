#!/bin/bash
set -euo pipefail
# General-purpose Swift development setup for Claude Code cloud environments.
# Installs the Swift toolchain, SwiftLint, and SwiftFormat.
#
# Environment variables:
#   SWIFT_VERSION  Swift toolchain version to install (default: 6.0.3)

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
  if command -v sudo &>/dev/null; then
    SUDO="sudo"
  else
    echo "ERROR: This script requires root privileges or sudo."
    exit 1
  fi
fi

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
  $SUDO apt-get update -qq
  DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq \
    curl gnupg2 unzip > /dev/null 2>&1
  SWIFT_VERSION="${SWIFT_VERSION:-6.0.3}"
  SWIFT_URL="https://download.swift.org/swift-${SWIFT_VERSION}-release/${SWIFT_PLATFORM}/swift-${SWIFT_VERSION}-RELEASE/swift-${SWIFT_VERSION}-RELEASE-${SWIFT_OS}.tar.gz"
  echo "Downloading Swift ${SWIFT_VERSION} for ${SWIFT_OS}..."
  curl -fsSL "$SWIFT_URL" -o /tmp/swift.tar.gz
  echo "Extracting..."
  $SUDO tar -xzf /tmp/swift.tar.gz -C /usr/local --strip-components=2
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
  # Note: unauthenticated GitHub API is limited to 60 requests/hour.
  # Set GITHUB_TOKEN in the environment to raise the limit.
  GITHUB_AUTH_HEADER=""
  if [ -n "${GITHUB_TOKEN:-}" ]; then
    GITHUB_AUTH_HEADER="-H \"Authorization: token $GITHUB_TOKEN\""
  fi
  SWIFTLINT_URL=$(curl -fsSL $GITHUB_AUTH_HEADER "https://api.github.com/repos/realm/SwiftLint/releases/latest" \
    | grep -o '"browser_download_url": *"[^"]*linux[^"]*"' \
    | head -1 \
    | cut -d'"' -f4)
  if [ -n "$SWIFTLINT_URL" ]; then
    curl -fsSL "$SWIFTLINT_URL" -o /tmp/swiftlint.zip
    unzip -oq /tmp/swiftlint.zip -d /tmp/swiftlint
    # Match the binary by exact name to avoid picking up shared libs
    SWIFTLINT_BIN=$(find /tmp/swiftlint -type f -name 'swiftlint' | head -1)
    if [ -z "$SWIFTLINT_BIN" ]; then
      echo "WARNING: Could not locate swiftlint binary in archive — skipping."
    else
      chmod +x "$SWIFTLINT_BIN"
      $SUDO install -m 755 "$SWIFTLINT_BIN" /usr/local/bin/swiftlint
      echo "Installed SwiftLint $(swiftlint version)"
    fi
    rm -rf /tmp/swiftlint.zip /tmp/swiftlint
  else
    echo "WARNING: Could not determine SwiftLint download URL — skipping."
  fi
fi
# ---------------------------------------------------------------------------
# 3. Install SwiftFormat (latest from GitHub releases)
# ---------------------------------------------------------------------------
if ! command -v swiftformat &>/dev/null; then
  echo "Installing SwiftFormat (latest)..."
  SWIFTFORMAT_URL=$(curl -fsSL $GITHUB_AUTH_HEADER "https://api.github.com/repos/nicklockwood/SwiftFormat/releases/latest" \
    | grep -o '"browser_download_url": *"[^"]*linux[^"]*"' \
    | head -1 \
    | cut -d'"' -f4)
  if [ -n "$SWIFTFORMAT_URL" ]; then
    curl -fsSL "$SWIFTFORMAT_URL" -o /tmp/swiftformat.zip
    unzip -oq /tmp/swiftformat.zip -d /tmp/swiftformat
    # Match the binary by exact name to avoid picking up shared libs
    SWIFTFORMAT_BIN=$(find /tmp/swiftformat -type f -name 'swiftformat' | head -1)
    if [ -z "$SWIFTFORMAT_BIN" ]; then
      echo "WARNING: Could not locate swiftformat binary in archive — skipping."
    else
      chmod +x "$SWIFTFORMAT_BIN"
      $SUDO install -m 755 "$SWIFTFORMAT_BIN" /usr/local/bin/swiftformat
      echo "Installed SwiftFormat $(swiftformat --version)"
    fi
    rm -rf /tmp/swiftformat.zip /tmp/swiftformat
  else
    echo "WARNING: Could not determine SwiftFormat download URL — skipping."
  fi
fi
echo "Swift development environment ready."
