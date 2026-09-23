# FileSentry

A tiny terminal-based static ZIP inspector for **macOS and Windows**.

FileSentry lets you inspect suspicious ZIP archives without extracting or executing their contents.

## How to run FileSentry

After FileSentry is installed, open Terminal, PowerShell, or Command Prompt and run:

~~~text
sentry
~~~

FileSentry will ask you to drop a ZIP file into the terminal. Drag the ZIP in, press Enter, then use the arrow keys to browse its contents.

## macOS

### Install

~~~bash
curl -fsSL https://zxt.lol/sentry/install.sh | zsh
source ~/.zshrc
~~~

### Run

~~~bash
sentry
~~~

### Uninstall

~~~bash
curl -fsSL https://zxt.lol/sentry/uninstall.sh | zsh
~~~

## Windows

Requires Windows 10/11 and Python 3.

If Python is missing:

~~~powershell
winget install Python.Python.3.13
~~~

### Install with PowerShell

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

Then close and reopen the terminal if needed and run:

~~~powershell
sentry
~~~

### Install from Command Prompt

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"
~~~

Then open a new terminal window and run:

~~~cmd
sentry
~~~

### Direct GitHub fallback

If the `zxt.lol` installer URL is temporarily unavailable, you can run FileSentry directly from GitHub instead.

PowerShell or Command Prompt:

~~~cmd
git clone https://github.com/zvzt/filesentry.git
cd filesentry
python windows\sentry.py
~~~

If `python` is not recognized, use:

~~~cmd
py -3 windows\sentry.py
~~~

This runs the Windows scanner directly from the cloned repository without using the `zxt.lol` installer.

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

If you are using the direct GitHub fallback instead:

~~~cmd
cd filesentry
git pull
python windows\sentry.py
~~~

### Uninstall Windows

If you installed with the installer:

~~~powershell
irm https://zxt.lol/sentry/windows/uninstall.ps1 | iex
~~~

From Command Prompt:

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/uninstall.ps1' | iex"
~~~

If you only used the direct GitHub fallback, nothing was installed system-wide. Delete the cloned `filesentry` folder.

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

The source code is hosted in this GitHub repository. `zxt.lol` provides the public install/download endpoints.
