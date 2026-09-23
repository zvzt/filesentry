#!/bin/zsh
rm -f "$HOME/.local/bin/sentry"
rm -rf "$HOME/Library/Caches/FileSentry"
echo "FileSentry removed."
echo "A ~/.local/bin PATH entry may remain in ~/.zshrc because other tools may use it."
