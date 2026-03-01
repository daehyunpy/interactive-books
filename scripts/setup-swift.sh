#!/bin/bash
set -euo pipefail
# General-purpose Swift development setup for Claude Code cloud environments.
# Installs the Swift toolchain, SwiftLint, SwiftFormat, gh, and git-lfs.
#
# Optimized for speed: starts the large Swift toolchain download (~878 MB)
# immediately in the background, then installs apt packages and dev tools
# concurrently. Total wall time ≈ max(Swift download, apt + dev tools).
#
# Environment variables:
#   SWIFT_VERSION  Swift toolchain version to install (default: 6.1.2)

# ---------------------------------------------------------------------------
# Detect architecture for selecting correct release binaries
# ---------------------------------------------------------------------------
ARCH=$(uname -m)
case "$ARCH" in
  x86_64)  ARCH_PATTERN="amd64\|x86_64" ;;
  aarch64) ARCH_PATTERN="arm64\|aarch64" ;;
  *)       ARCH_PATTERN="$ARCH" ;;
esac

# ---------------------------------------------------------------------------
# Detect Ubuntu version (needed for Swift download URL)
# ---------------------------------------------------------------------------
UBUNTU_CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
case "$UBUNTU_CODENAME" in
  noble)   SWIFT_PLATFORM="ubuntu2404" ; SWIFT_OS="ubuntu24.04" ;;
  jammy)   SWIFT_PLATFORM="ubuntu2204" ; SWIFT_OS="ubuntu22.04" ;;
  focal)   SWIFT_PLATFORM="ubuntu2004" ; SWIFT_OS="ubuntu20.04" ;;
  *)
    echo "WARNING: Unsupported Ubuntu version ($UBUNTU_CODENAME). Attempting noble defaults..."
    SWIFT_PLATFORM="ubuntu2404"
    SWIFT_OS="ubuntu24.04"
    ;;
esac

# ---------------------------------------------------------------------------
# 1. Start Swift toolchain download immediately (biggest bottleneck: ~878 MB)
# ---------------------------------------------------------------------------
SWIFT_DOWNLOAD_PID=""
if ! command -v swift &>/dev/null; then
  SWIFT_VERSION="${SWIFT_VERSION:-6.1.2}"
  SWIFT_URL="https://download.swift.org/swift-${SWIFT_VERSION}-release/${SWIFT_PLATFORM}/swift-${SWIFT_VERSION}-RELEASE/swift-${SWIFT_VERSION}-RELEASE-${SWIFT_OS}.tar.gz"
  echo "Downloading Swift ${SWIFT_VERSION} for ${SWIFT_OS} (background)..."
  curl -fsSL "$SWIFT_URL" -o /tmp/swift.tar.gz &
  SWIFT_DOWNLOAD_PID=$!
fi

# ---------------------------------------------------------------------------
# Helper: install a tool from its GitHub release (latest Linux binary)
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

  # Prefer gh CLI (authenticated, avoids rate limits) if available.
  if command -v gh &>/dev/null; then
    url=$(gh release view --repo "$repo" --json assets -q \
      ".assets[].url" 2>/dev/null \
      | grep -i "linux" \
      | grep -i "$ARCH_PATTERN" \
      | head -1) || true
  fi

  # Fall back to unauthenticated GitHub API.
  if [ -z "${url:-}" ]; then
    url=$(curl -fsSL "https://api.github.com/repos/${repo}/releases/latest" \
      | grep -oi '"browser_download_url": *"[^"]*linux[^"]*"' \
      | grep -i "$ARCH_PATTERN" \
      | head -1 \
      | cut -d'"' -f4) || true
  fi

  if [ -z "${url:-}" ]; then
    echo "WARNING: Could not determine ${cmd} download URL — skipping."
    return
  fi

  local archive="/tmp/${cmd}-archive"
  curl -fsSL -L "$url" -o "$archive"

  local extract_dir="/tmp/${cmd}-extract"
  rm -rf "$extract_dir"
  mkdir -p "$extract_dir"

  # Handle both .zip and .tar.gz archives.
  case "$url" in
    *.tar.gz|*.tgz) tar -xzf "$archive" -C "$extract_dir" ;;
    *)              unzip -oq "$archive" -d "$extract_dir" ;;
  esac

  local bin
  bin=$(find "$extract_dir" -type f -name "$cmd" | head -1)

  if [ -z "$bin" ]; then
    echo "WARNING: Could not locate ${cmd} binary in archive — skipping."
  else
    sudo install -m 755 "$bin" "/usr/local/bin/${cmd}"
    echo "Installed ${cmd} $(${cmd} ${version_flag})"
  fi

  rm -rf "$archive" "$extract_dir"
}

# ---------------------------------------------------------------------------
# 2. Install apt packages while Swift downloads in parallel
# ---------------------------------------------------------------------------
sudo apt-get update -qq || true

# gh and git-lfs
if ! command -v gh &>/dev/null || ! command -v git-lfs &>/dev/null; then
  DEBIAN_FRONTEND=noninteractive sudo apt-get install -y -qq \
    gh git-lfs > /dev/null 2>&1 || echo "WARNING: apt-get install failed — gh/git-lfs may be unavailable."
fi

# Swift system dependencies (required for the toolchain and SPM builds).
# build-essential provides the default GCC/G++ toolchain, which transitively
# pulls in libgcc-*-dev and libstdc++-*-dev for the distro's default version.
DEBIAN_FRONTEND=noninteractive sudo apt-get install -y -qq \
  binutils \
  build-essential \
  gnupg2 \
  libcurl4-openssl-dev \
  libedit2 \
  libpython3-dev \
  libsqlite3-dev \
  libxml2-dev \
  libz3-dev \
  pkg-config \
  tzdata \
  unzip \
  zlib1g-dev \
  > /dev/null 2>&1 || echo "WARNING: Some Swift system dependencies could not be installed."

# ---------------------------------------------------------------------------
# 3. Install SwiftLint & SwiftFormat (parallel, while Swift still downloads)
# ---------------------------------------------------------------------------
install_github_release swiftlint realm/SwiftLint version &
install_github_release swiftformat nicklockwood/SwiftFormat --version &
wait %?swiftlint 2>/dev/null || true
wait %?swiftformat 2>/dev/null || true

# ---------------------------------------------------------------------------
# 4. Wait for Swift download and extract
# ---------------------------------------------------------------------------
if [ -n "$SWIFT_DOWNLOAD_PID" ]; then
  echo "Waiting for Swift download to finish..."
  if wait "$SWIFT_DOWNLOAD_PID"; then
    echo "Extracting Swift toolchain..."
    sudo tar -xzf /tmp/swift.tar.gz -C /usr/local --strip-components=2
    rm -f /tmp/swift.tar.gz
    if command -v swift &>/dev/null; then
      echo "Installed $(swift --version 2>&1 | head -1)"
    else
      echo "ERROR: Swift installation failed — binary not found after extraction."
      exit 1
    fi
  else
    echo "ERROR: Swift download failed."
    rm -f /tmp/swift.tar.gz
    exit 1
  fi
fi

echo "Swift development environment ready."
