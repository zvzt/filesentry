#!/bin/zsh
set -e

BIN_DIR="$HOME/.local/bin"
TARGET="$BIN_DIR/sentry"
URL="https://zxt.lol/sentry/sentry.py"

if ! command -v python3 >/dev/null 2>&1; then
    echo "FileSentry requires Python 3."
    echo "Install it with: brew install python"
    exit 1
fi

if ! command -v curl >/dev/null 2>&1; then
    echo "FileSentry requires curl."
    exit 1
fi

mkdir -p "$BIN_DIR"
TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

echo "Downloading FileSentry..."
curl -fsSL "$URL" -o "$TMP"
python3 -m py_compile "$TMP"
mv "$TMP" "$TARGET"
chmod 755 "$TARGET"
trap - EXIT

if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    echo "Added ~/.local/bin to PATH."
fi

echo "FileSentry installed."
echo "Run: source ~/.zshrc"
echo "Then: sentry"
