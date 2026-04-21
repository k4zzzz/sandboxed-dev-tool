#!/usr/bin/env bash
set -euo pipefail

TOOL_REPO="https://github.com/k4zzzz/sandboxed-dev-tool"
INSTALL_DIR="$HOME/.dev-tool"
SHELL_RC=""

echo ""
echo "  dev tool installer"
echo "  ──────────────────"
echo ""

# ── Detect shell rc file ──────────────────────────────────────────────────────
case "$SHELL" in
  */zsh)  SHELL_RC="$HOME/.zshrc" ;;
  */bash) SHELL_RC="$HOME/.bash_profile" ;;
  *)      SHELL_RC="$HOME/.profile" ;;
esac

# ── Homebrew ──────────────────────────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
  echo "==> Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  # Add brew to PATH for Apple Silicon vs Intel
  if [[ -f /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$SHELL_RC"
  else
    eval "$(/usr/local/bin/brew shellenv)"
    echo 'eval "$(/usr/local/bin/brew shellenv)"' >> "$SHELL_RC"
  fi
else
  echo "==> Homebrew already installed, skipping."
fi

# ── Lima ──────────────────────────────────────────────────────────────────────
if ! command -v limactl &>/dev/null; then
  echo "==> Installing Lima..."
  brew install lima
else
  echo "==> Lima already installed, skipping."
fi

# ── uv ────────────────────────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  echo "==> Installing uv..."
  brew install uv
else
  echo "==> uv already installed, skipping."
fi

# ── Clone dev-tool ────────────────────────────────────────────────────────────
echo "==> Fetching dev-tool from GitHub..."
rm -rf "$INSTALL_DIR"
git clone --depth=1 "$TOOL_REPO" "$INSTALL_DIR"

# ── Install CLI via uv ────────────────────────────────────────────────────────
echo "==> Installing dev CLI..."
uv tool install "$INSTALL_DIR" --force

# ── Ensure uv tool bin is on PATH ─────────────────────────────────────────────
UV_BIN_DIR="$(uv tool bin)"
if [[ ":$PATH:" != *":$UV_BIN_DIR:"* ]]; then
  echo "==> Adding $UV_BIN_DIR to PATH in $SHELL_RC..."
  echo "" >> "$SHELL_RC"
  echo "# dev-tool (added by installer)" >> "$SHELL_RC"
  echo "export PATH=\"$UV_BIN_DIR:\$PATH\"" >> "$SHELL_RC"
  export PATH="$UV_BIN_DIR:$PATH"
fi

echo ""
echo "  ✓ Installation complete."
echo ""
echo "  Start fresh:   dev vm create"
echo "  Start/stop:    dev vm start | dev vm stop"
echo "  Tear down:     dev vm delete"
echo ""
echo "  Restart your terminal (or run: source $SHELL_RC)"
echo ""
