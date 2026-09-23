# FileSentry for Windows

Lightweight terminal-based static ZIP inspection for Windows.

## How to run FileSentry

After FileSentry is installed, open **PowerShell**, **Windows Terminal**, or **Command Prompt** and run:

~~~text
sentry
~~~

FileSentry will show:

~~~text
Drop ZIP here and press Enter:
>
~~~

Drag a ZIP file from File Explorer into the terminal, press Enter, then use the arrow keys to browse the files inside it.

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

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

Then run:

~~~powershell
sentry
~~~

If `sentry` is not found immediately, close the terminal and open a new one.

## Install from Command Prompt

`irm` and `iex` are PowerShell commands, so from cmd.exe use:

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"
~~~

Then open a new terminal and run:

~~~cmd
sentry
~~~

## Direct GitHub fallback

If the `zxt.lol` installer gives a 404 or is temporarily unavailable, clone the repository and run the scanner directly:

~~~cmd
git clone https://github.com/zvzt/filesentry.git
cd filesentry
python windows\sentry.py
~~~

If `python` is not recognized:

~~~cmd
py -3 windows\sentry.py
~~~

This does not install FileSentry as a global command. It simply runs the scanner from the cloned folder.

## Update

Installer version:

~~~powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
~~~

Direct GitHub version:

~~~cmd
cd filesentry
git pull
python windows\sentry.py
~~~

## Uninstall

Installer version:

~~~powershell
irm https://zxt.lol/sentry/windows/uninstall.ps1 | iex
~~~

Command Prompt:

~~~cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/uninstall.ps1' | iex"
~~~

If you only cloned the repository, simply delete the `filesentry` folder.

## Controls

~~~text
Up / Down   Select a file
Enter       Open a safe Notepad preview
f           View security findings
r           Scan another ZIP
q           Quit
~~~

## Notes

- The normal installer is served through `zxt.lol`.
- The source remains in the FileSentry GitHub repository.
- The GitHub clone method is a fallback if the hosted installer is unavailable.
- FileSentry inspects ZIP contents statically and does not perform a normal extraction.
