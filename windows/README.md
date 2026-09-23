# FileSentry for Windows

Lightweight terminal-based static ZIP inspection for Windows.

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

Open PowerShell or a PowerShell tab in Windows Terminal:

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

Then run:

~~~powershell
sentry
~~~

If `sentry` is not found immediately, close the terminal and open a new one.

## Install from Command Prompt

`irm` and `iex` are PowerShell commands, so they do not work directly in cmd.exe.

From Command Prompt use:

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"
~~~

Then open a new terminal window and run:

~~~cmd
sentry
~~~

## Update

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
