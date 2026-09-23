# FileSentry for Windows

Lightweight terminal-based static ZIP inspection for Windows.

## How to run FileSentry

After FileSentry is installed, open **PowerShell**, **Windows Terminal**, or **Command Prompt** and run:

~~~text
sentry
~~~

FileSentry will open in the terminal and show:

~~~text
Drop ZIP here and press Enter:
>
~~~

Drag a ZIP file from File Explorer into the terminal window, press Enter, then use the arrow keys to browse the files inside it.

## Requirements

- Windows 10 or Windows 11
- Python 3

Check Python:

~~~powershell
py -3 --version
~~~

If Python is missing:

~~~powershell
winget install Python.Python.3.13
~~~

## Install with PowerShell

Open PowerShell or a PowerShell tab in Windows Terminal and run:

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

## Run

After installation, run:

~~~powershell
sentry
~~~

If `sentry` is not found immediately, close the terminal and open a new one, then run `sentry` again.

## Install from Command Prompt

`irm` and `iex` are PowerShell commands, so they do not work directly in cmd.exe.

From Command Prompt run:

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"
~~~

Then open a new terminal window and run:

~~~cmd
sentry
~~~

## Update

Re-run the same installer command.

PowerShell:

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

Command Prompt:

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"
~~~

## Uninstall

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
Enter       Open a safe Notepad preview
f           View security findings
r           Scan another ZIP
q           Quit
~~~

## Notes

- The installer files are served through `zxt.lol`.
- The source remains in the FileSentry GitHub repository.
- FileSentry inspects ZIP contents statically and does not perform a normal extraction.
