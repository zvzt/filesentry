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

## Install

Open PowerShell or Windows Terminal and run:

~~~powershell
irm https://raw.githubusercontent.com/zvzt/filesentry/main/windows/install.ps1 | iex
~~~

Then run:

~~~powershell
sentry
~~~

If the command is not found in the current window, close Terminal/PowerShell and open it again.

## Controls

~~~text
Up / Down   Select a file
Enter       Open a safe Notepad preview
f           View security findings
r           Scan another ZIP
q           Quit
~~~

## Windows checks

FileSentry looks for indicators including:

- ZIP path traversal / extraction escape attempts
- NTFS alternate-stream style names
- symbolic links
- Startup-folder targeting
- Registry Run / RunOnce persistence
- scheduled-task creation and task XML triggers
- Windows-service creation
- WMI subscription persistence
- PowerShell encoded commands
- common downloader / LOLBin commands
- Windows shortcuts
- executable scripts
- EXE/DLL/MSI and related executable content
- registry files
- autorun.inf
- suspicious executable strings
- compression-bomb indicators
- nested ZIPs

## Safe previews

FileSentry never writes an archive entry to disk under its original executable/script name.

When Enter is pressed:

- text is copied into a generated .txt preview
- binary files are converted to hexadecimal text
- symlink previews are blocked
- encrypted entries are blocked
- suspicious compression-bomb entries are blocked
- preview size is limited
- Notepad opens only the generated text file

Generated previews are stored under:

~~~text
%LOCALAPPDATA%\FileSentry\previews
~~~

Static inspection reduces risk, but no file parser or viewer can truthfully be described as impossible to exploit.

## Update

Re-run:

~~~powershell
irm https://raw.githubusercontent.com/zvzt/filesentry/main/windows/install.ps1 | iex
~~~

## Uninstall

~~~powershell
irm https://raw.githubusercontent.com/zvzt/filesentry/main/windows/uninstall.ps1 | iex
~~~
