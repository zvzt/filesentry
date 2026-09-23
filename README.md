# FileSentry

A tiny terminal-based static ZIP inspector for **macOS and Windows**.

FileSentry lets you inspect suspicious ZIP archives without extracting or executing their contents. It lists archive entries, highlights common autorun/persistence and extraction-risk indicators, and opens selected entries only as generated plain-text previews.

## macOS

Requires Python 3.

Install:

~~~bash
curl -fsSL https://raw.githubusercontent.com/zvzt/filesentry/main/install.sh | zsh
source ~/.zshrc
~~~

Run:

~~~bash
sentry
~~~

The macOS build uses TextEdit for generated safe previews.

## Windows

Requires Windows 10/11 and Python 3.

Install from PowerShell or Windows Terminal:

~~~powershell
irm https://raw.githubusercontent.com/zvzt/filesentry/main/windows/install.ps1 | iex
~~~

Run:

~~~powershell
sentry
~~~

The Windows build uses Notepad for generated safe previews.

More Windows details: [windows/README.md](windows/README.md)

## Controls

~~~text
Up / Down   Select a file
Enter       Open a safe text preview
f           View security findings
r           Scan another ZIP
q           Quit
~~~

## Core safety model

FileSentry performs static inspection only.

- It does not execute archive contents.
- It does not perform a normal ZIP extraction.
- Selected text is copied into a generated .txt preview.
- Selected binary data is rendered as hexadecimal text.
- Symlink previews are blocked.
- Preview size is capped.
- Compression-bomb indicators are checked before previewing.
- Encrypted files are not silently executed or extracted.

Static inspection greatly reduces exposure, but no parser or viewer should be described as impossible to exploit.

## macOS checks

The macOS build checks for indicators including:

- extraction-path traversal
- symbolic links
- LaunchAgents / LaunchDaemons
- launchd RunAtLoad / KeepAlive
- login-item related commands
- cron persistence
- shell startup modifications
- quarantine/Gatekeeper-related commands
- executable permissions
- executable scripts
- downloader commands
- compression-bomb indicators

## Windows checks

The Windows build checks for indicators including:

- extraction-path traversal
- NTFS alternate-stream style names
- symbolic links
- Startup-folder targeting
- Registry Run / RunOnce persistence
- scheduled tasks
- Windows services
- WMI subscription persistence
- encoded PowerShell
- downloader / LOLBin commands
- LNK / URL shortcuts
- executable scripts and binaries
- registry files
- autorun.inf
- compression-bomb indicators

## Dependencies

No pip packages are required. Both builds use Python's standard library.

## Uninstall macOS

~~~bash
curl -fsSL https://raw.githubusercontent.com/zvzt/filesentry/main/uninstall.sh | zsh
~~~

## Uninstall Windows

~~~powershell
irm https://raw.githubusercontent.com/zvzt/filesentry/main/windows/uninstall.ps1 | iex
~~~
