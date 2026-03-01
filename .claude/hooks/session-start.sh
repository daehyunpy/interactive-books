#!/bin/bash
set -euo pipefail

# Only run in remote (web) environments
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

SWIFT_VERSION="6.1.2"
SWIFT_RELEASE="swift-${SWIFT_VERSION}-RELEASE"
SWIFT_PLATFORM="ubuntu24.04"
SWIFT_ARCHIVE="${SWIFT_RELEASE}-${SWIFT_PLATFORM}.tar.gz"
SWIFT_URL="https://download.swift.org/swift-${SWIFT_VERSION}-release/ubuntu2404/${SWIFT_RELEASE}/${SWIFT_ARCHIVE}"
SWIFT_INSTALL_DIR="/opt/swift"

SWIFTLINT_VERSION="0.63.2"
SWIFTLINT_URL="https://github.com/realm/SwiftLint/releases/download/${SWIFTLINT_VERSION}/swiftlint_linux_amd64.zip"

SWIFTFORMAT_VERSION="0.59.1"
SWIFTFORMAT_URL="https://github.com/nicklockwood/SwiftFormat/releases/download/${SWIFTFORMAT_VERSION}/swiftformat_linux.zip"

# ── Swift toolchain ──────────────────────────────────────────────────────────

if ! command -v swift &>/dev/null; then
  echo "Installing Swift ${SWIFT_VERSION}..."

  apt-get update -qq
  apt-get install -y -qq \
    binutils git gnupg2 libc6-dev libcurl4-openssl-dev \
    libedit2 libgcc-13-dev libncurses-dev libpython3-dev \
    libsqlite3-0 libsqlite3-dev libstdc++-13-dev libxml2-dev libz3-dev \
    pkg-config tzdata unzip zlib1g-dev >/dev/null

  cd /tmp
  curl -fsSL -O "${SWIFT_URL}"
  tar xzf "${SWIFT_ARCHIVE}"
  mkdir -p "${SWIFT_INSTALL_DIR}"
  mv "${SWIFT_RELEASE}-${SWIFT_PLATFORM}"/usr "${SWIFT_INSTALL_DIR}/"
  rm -rf "${SWIFT_ARCHIVE}" "${SWIFT_RELEASE}-${SWIFT_PLATFORM}"

  echo "export PATH=\"${SWIFT_INSTALL_DIR}/usr/bin:\$PATH\"" >> "$CLAUDE_ENV_FILE"
  export PATH="${SWIFT_INSTALL_DIR}/usr/bin:$PATH"

  echo "Swift $(swift --version 2>&1 | head -1) installed."
else
  echo "Swift already installed: $(swift --version 2>&1 | head -1)"
fi

# ── SwiftLint ────────────────────────────────────────────────────────────────

if ! command -v swiftlint &>/dev/null; then
  echo "Installing SwiftLint ${SWIFTLINT_VERSION}..."

  cd /tmp
  curl -fsSL -o swiftlint.zip "${SWIFTLINT_URL}"
  unzip -oq swiftlint.zip -d swiftlint_extracted
  install -m 755 swiftlint_extracted/swiftlint /usr/local/bin/swiftlint
  rm -rf swiftlint.zip swiftlint_extracted

  echo "SwiftLint $(swiftlint version) installed."
else
  echo "SwiftLint already installed: $(swiftlint version)"
fi

# ── SwiftFormat ──────────────────────────────────────────────────────────────

if ! command -v swiftformat &>/dev/null; then
  echo "Installing SwiftFormat ${SWIFTFORMAT_VERSION}..."

  cd /tmp
  curl -fsSL -o swiftformat.zip "${SWIFTFORMAT_URL}"
  unzip -oq swiftformat.zip -d swiftformat_extracted
  install -m 755 swiftformat_extracted/swiftformat /usr/local/bin/swiftformat
  rm -rf swiftformat.zip swiftformat_extracted

  echo "SwiftFormat $(swiftformat --version) installed."
else
  echo "SwiftFormat already installed: $(swiftformat --version)"
fi

# ── Python dependencies ──────────────────────────────────────────────────────

if [ -f "${CLAUDE_PROJECT_DIR}/python/pyproject.toml" ]; then
  echo "Installing Python dependencies..."
  cd "${CLAUDE_PROJECT_DIR}/python"
  uv sync --quiet
  echo "Python dependencies installed."
fi

echo "Session setup complete."
