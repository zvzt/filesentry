# FileSentry

A tiny terminal-based static ZIP inspector for **macOS and Windows**.

FileSentry lets you inspect suspicious ZIP archives without extracting or executing their contents.

## How to run FileSentry

After FileSentry is installed, open Terminal, PowerShell, or Command Prompt and run:

~~~text
sentry
~~~

FileSentry will open in the terminal and ask you to drop a ZIP file into the window. Drag the ZIP into the terminal, press Enter, then use the arrow keys to browse its contents.

## macOS

### Install

Run:

~~~bash
curl -fsSL https://zxt.lol/sentry/install.sh | zsh
source ~/.zshrc
~~~

### Run

After installation, start FileSentry with:

~~~bash
sentry
~~~

### Uninstall

Run:

~~~bash
curl -fsSL https://zxt.lol/sentry/uninstall.sh | zsh
~~~

## Windows

Requires Windows 10/11 and Python 3.

If Python is missing, install it with:

~~~powershell
winget install Python.Python.3.13
~~~

### Install with PowerShell

Open **PowerShell** or a **PowerShell tab in Windows Terminal** and run:

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

### Run

After installation, close and reopen the terminal if needed, then run:

~~~powershell
sentry
~~~

FileSentry will ask you to drop a ZIP into the terminal. Drag the ZIP in, press Enter, and use the controls below.

### Install from Command Prompt

If you are using **cmd.exe**, do not use `irm` directly. Run:

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"
~~~

Then open a new Command Prompt or PowerShell window and run:

~~~cmd
sentry
~~~

### Update Windows

Re-run the installer.

PowerShell:

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

Command Prompt:

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"
~~~

### Uninstall Windows

PowerShell:

~~~powershell
irm https://zxt.lol/sentry/windows/uninstall.ps1 | iex
~~~

Command Prompt:

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/uninstall.ps1' | iex"
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

Static inspection reduces exposure, but no parser or viewer should be described as impossible to exploit.

## Source

The source code remains hosted in this GitHub repository. zxt.lol provides the public install/download endpoints.
