# FileSentry for Windows

Lightweight terminal-based static ZIP inspection for Windows.

## Requirements

- Windows 10 or Windows 11
- Python 3

If Python is missing:

~~~powershell
winget install Python.Python.3.13
~~~

## Install

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

Then:

~~~powershell
sentry
~~~

## Update

Re-run:

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

## Uninstall

~~~powershell
irm https://zxt.lol/sentry/windows/uninstall.ps1 | iex
~~~

## Controls

~~~text
Up / Down   Select a file
Enter       Open a safe Notepad preview
f           View security findings
r           Scan another ZIP
q           Quit
~~~
