# FileSentry

A terminal-based static ZIP inspector for **macOS and Windows**.

FileSentry lets you inspect suspicious ZIP archives without performing a normal extraction or executing archive contents.

## Run FileSentry

After installation, open Terminal, PowerShell, or Command Prompt and run:

```text
sentry
```

Drop a ZIP file into the terminal, press Enter, then use the arrow keys to browse its contents.

## macOS

### Requirements

- macOS
- Python 3

### Install / Update

**One command — installs or updates FileSentry to the latest version:**

```bash
curl -fsSL https://zxt.lol/sentry/install.sh | zsh
```

Then run:

```bash
source ~/.zshrc
sentry
```

The installer checks for an existing FileSentry installation, removes the old executable and cached preview data, then downloads and installs the current version. Scan reports in `~/Downloads` are not removed.

### Run

```bash
sentry
```

### Uninstall

```bash
curl -fsSL https://zxt.lol/sentry/uninstall.sh | zsh
```

## Windows

Requires Windows 10/11 and Python 3.

If Python is missing:

```powershell
winget install Python.Python.3.13
```

### Install / Update with PowerShell

**One command — installs or updates FileSentry to the latest version:**

```powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
```

Then open a new terminal if needed and run:

```powershell
sentry
```

The installer checks for an existing FileSentry installation, removes the old installation and cached preview data, then downloads and installs the current version. Scan reports are not removed.

### Install from Command Prompt

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"
```

Then open a new terminal window and run:

```cmd
sentry
```

### Direct GitHub fallback

If the `zxt.lol` installer endpoint is temporarily unavailable:

```cmd
git clone https://github.com/zvzt/filesentry.git
cd filesentry
python windows\sentry.py
```

If `python` is not recognized:

```cmd
py -3 windows\sentry.py
```

### Update Windows

Re-run the installer:

```powershell
irm https://zxt.lol/sentry/windows/install.ps1 | iex
```

Or, from Command Prompt:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/install.ps1' | iex"
```

If you use the direct GitHub copy:

```cmd
cd filesentry
git pull
python windows\sentry.py
```

### Uninstall Windows

PowerShell:

```powershell
irm https://zxt.lol/sentry/windows/uninstall.ps1 | iex
```

Command Prompt:

```cmd
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm 'https://zxt.lol/sentry/windows/uninstall.ps1' | iex"
```

If you only cloned the repository, nothing was installed system-wide; delete the cloned `filesentry` folder.

## Controls

```text
Up / Down   Select a file
Enter       Open a safe text preview
f           View security findings
d           Download full scan report
r           Scan another ZIP
q           Quit
```

## Security model

FileSentry performs static inspection only.

- Archive contents are not executed.
- It does not perform a normal ZIP extraction.
- Selected text is copied into a generated `.txt` preview with a randomized temporary filename.
- Selected binary data is rendered as hexadecimal text.
- Preview files are cleaned at startup and normal exit; the macOS preview cache is private to the current user.
- Pressing `d` saves a complete plain-text scan report to the user's Downloads folder, including every archive entry and a separated risky/flagged-items section.
- Symlink previews are blocked.
- Preview size is capped.
- Compression-bomb indicators are checked before previewing.
- Encrypted files are not silently executed or extracted.
- Archive paths attempting to escape the normal extraction directory are flagged.

Preview files are never given the archive entry's original executable extension, and FileSentry does not launch archive contents directly.

Static inspection reduces exposure, but no parser or viewer should be treated as impossible to exploit. Review findings and use normal security precautions with untrusted files.

## Source and install endpoints

The source code is maintained in this repository. `zxt.lol` provides the public install/download endpoints for the macOS and Windows builds.

## License

MIT — see [LICENSE](LICENSE).
