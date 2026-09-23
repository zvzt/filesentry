# FileSentry

A tiny terminal-based static ZIP inspector for macOS.

FileSentry lets you inspect suspicious ZIP archives without extracting or executing their contents. It lists everything inside the archive, flags common macOS autorun/persistence indicators, and opens selected files only as generated plain-text previews.

## Install

Requires macOS and Python 3.

```bash
python3 --version
```

Install FileSentry:

```bash
curl -fsSL https://raw.githubusercontent.com/zvzt/filesentry/main/install.sh | zsh
source ~/.zshrc
```

Run:

```bash
sentry
```

Drag a ZIP from Finder into Terminal when FileSentry asks for one, then press Enter.

## Controls

```text
Up / Down   Select a file
Enter       Open a safe TextEdit preview
f           View security findings
r           Scan another ZIP
q           Quit
```

## What it checks

- ZIP path traversal / extraction escape attempts
- Symbolic links
- LaunchAgents and LaunchDaemons
- launchd RunAtLoad / KeepAlive plists
- Login-item related commands
- cron persistence
- shell startup files
- Gatekeeper/quarantine-removal commands
- executable permissions
- .command scripts
- suspicious downloader commands
- large/high-ratio compression entries
- nested ZIP indicators

## Safe previews

FileSentry does not extract an entry under its original name and does not execute archive contents.

When you press Enter:

- Text is copied into a separate `.txt` preview.
- Binary data is converted to hexadecimal text.
- Plists are converted to readable XML when possible.
- Symlink previews are blocked.
- Preview size is capped.
- TextEdit opens only the generated preview.

The preview is stored under:

```text
~/Library/Caches/FileSentry/previews/
```

Static inspection reduces risk, but no parser or viewer should be described as impossible to exploit.

## Update

Re-run the installer:

```bash
curl -fsSL https://raw.githubusercontent.com/zvzt/filesentry/main/install.sh | zsh
```

## Uninstall

```bash
curl -fsSL https://raw.githubusercontent.com/zvzt/filesentry/main/uninstall.sh | zsh
```

## Dependencies

No pip packages are required. FileSentry uses only Python's standard library and macOS TextEdit.
