# FileSentry

A tiny terminal-based static ZIP inspector for **macOS and Windows**.

FileSentry lets you inspect suspicious ZIP archives without extracting or executing their contents.

## macOS

~~~bash
curl -fsSL https://zxt.lol/sentry/install.sh | zsh
source ~/.zshrc
sentry
~~~

## Windows

Open PowerShell or Windows Terminal:

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
sentry
~~~

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

## Uninstall macOS

~~~bash
curl -fsSL https://zxt.lol/sentry/uninstall.sh | zsh
~~~

## Uninstall Windows

~~~powershell
irm https://zxt.lol/sentry/windows/uninstall.ps1 | iex
~~~

## Source

The source code remains hosted in this GitHub repository. zxt.lol provides the public install/download endpoints.
