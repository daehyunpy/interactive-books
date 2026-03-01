#!/bin/bash
set -euo pipefail
# General-purpose Swift development setup for Claude Code cloud environments.
# Installs the Swift toolchain, SwiftLint, SwiftFormat, gh, and git-lfs.
#
# Environment variables:
#   SWIFT_VERSION  Swift toolchain version to install (default: 6.1.2)

# ---------------------------------------------------------------------------
# Helper: install a tool from its GitHub release (latest Linux zip)
# Usage: install_github_release <cmd_name> <repo> <version_flag>
# ---------------------------------------------------------------------------
install_github_release() {
  local cmd="$1"
  local repo="$2"
  local version_flag="$3"

  if command -v "$cmd" &>/dev/null; then
    return
  fi

  echo "Installing ${cmd} (latest)..."
  local url
  url=$(curl -fsSL "https://api.github.com/repos/${repo}/releases/latest" \
    | grep -o '"browser_download_url": *"[^"]*linux[^"]*"' \
    | head -1 \
    | cut -d'"' -f4)

  if [ -z "$url" ]; then
    echo "WARNING: Could not determine ${cmd} download URL — skipping."
    return
  fi

  curl -fsSL "$url" -o "/tmp/${cmd}.zip"
  unzip -oq "/tmp/${cmd}.zip" -d "/tmp/${cmd}"
  local bin
  bin=$(find "/tmp/${cmd}" -type f -name "$cmd" | head -1)

  if [ -z "$bin" ]; then
    echo "WARNING: Could not locate ${cmd} binary in archive — skipping."
  else
    sudo install -m 755 "$bin" "/usr/local/bin/${cmd}"
    echo "Installed ${cmd} $(${cmd} ${version_flag})"
  fi

  rm -rf "/tmp/${cmd}.zip" "/tmp/${cmd}"
}

# ---------------------------------------------------------------------------
# 1. Install apt packages (gh, git-lfs)
# ---------------------------------------------------------------------------
if ! command -v gh &>/dev/null || ! command -v git-lfs &>/dev/null; then
  sudo apt-get update -qq || true
  DEBIAN_FRONTEND=noninteractive sudo apt-get install -y -qq \
    gh git-lfs > /dev/null 2>&1 || echo "WARNING: apt-get install failed — gh/git-lfs may be unavailable."
fi

# ---------------------------------------------------------------------------
# 2. Install Swift toolchain via official tarball
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
  SWIFT_VERSION="${SWIFT_VERSION:-6.1.2}"
  SWIFT_URL="https://download.swift.org/swift-${SWIFT_VERSION}-release/${SWIFT_PLATFORM}/swift-${SWIFT_VERSION}-RELEASE/swift-${SWIFT_VERSION}-RELEASE-${SWIFT_OS}.tar.gz"
  echo "Downloading Swift ${SWIFT_VERSION} for ${SWIFT_OS}..."
  curl -fsSL "$SWIFT_URL" -o /tmp/swift.tar.gz
  echo "Extracting..."
  sudo tar -xzf /tmp/swift.tar.gz -C /usr/local --strip-components=2
  rm /tmp/swift.tar.gz
  if command -v swift &>/dev/null; then
    echo "Installed $(swift --version 2>&1 | head -1)"
  else
    echo "ERROR: Swift installation failed."
    exit 1
  fi
fi

# ---------------------------------------------------------------------------
# 3. Install SwiftLint & SwiftFormat (latest from GitHub releases)
# ---------------------------------------------------------------------------
install_github_release swiftlint realm/SwiftLint version
install_github_release swiftformat nicklockwood/SwiftFormat --version

echo "Swift development environment ready."
