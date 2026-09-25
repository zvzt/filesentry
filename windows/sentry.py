#!/usr/bin/env python3
import atexit
import hashlib
import msvcrt
import os
import re
import shlex
import stat
import subprocess
import sys
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

VERSION="0.1.1"
MAX_PREVIEW=2*1024*1024
MAX_BINARY_PREVIEW=256*1024
MAX_SCAN_FILE=384*1024
MAX_SCAN_TOTAL=10*1024*1024
MAX_ENTRIES=20000
ZIP_BOMB_SIZE=20*1024*1024
ZIP_BOMB_RATIO=200

LOCALAPPDATA=Path(os.environ.get("LOCALAPPDATA",str(Path.home()/"AppData"/"Local")))
CACHE_DIR=LOCALAPPDATA/"FileSentry"/"previews"

TEXT_EXTENSIONS={
    ".txt",".md",".json",".xml",".ini",".cfg",".conf",".yaml",".yml",".toml",
    ".csv",".log",".html",".css",".py",".js",".ts",".lua",".ps1",".psm1",
    ".psd1",".bat",".cmd",".vbs",".vbe",".wsf",".wsh",".hta",".reg",".inf",
    ".url",".properties",".config"
}
SCRIPT_EXTENSIONS={".ps1",".psm1",".bat",".cmd",".vbs",".vbe",".js",".jse",".wsf",".wsh",".hta"}
EXECUTABLE_EXTENSIONS={".exe",".dll",".scr",".com",".msi",".msp",".msix",".appx",".cpl",".sys",".ocx"}

CONTENT_RULES=[
    ("\\software\\microsoft\\windows\\currentversion\\runonce","HIGH","Registry Autorun","References the Windows RunOnce autorun key."),
    ("\\software\\microsoft\\windows\\currentversion\\run","HIGH","Registry Autorun","References the Windows Run autorun key."),
    ("currentversion/runonce","HIGH","Registry Autorun","References the Windows RunOnce autorun key."),
    ("currentversion/run","HIGH","Registry Autorun","References the Windows Run autorun key."),
    ("schtasks /create","HIGH","Scheduled Task","Creates a Windows scheduled task."),
    ("register-scheduledtask","HIGH","Scheduled Task","Registers a Windows scheduled task."),
    ("new-scheduledtask","HIGH","Scheduled Task","Creates a Windows scheduled task."),
    ("<logontrigger","HIGH","Scheduled Task","Task XML contains a logon trigger."),
    ("<boottrigger","HIGH","Scheduled Task","Task XML contains a boot trigger."),
    ("new-service","HIGH","Windows Service","Creates a Windows service."),
    ("sc.exe create","HIGH","Windows Service","Creates a Windows service."),
    ("sc create","HIGH","Windows Service","Creates a Windows service."),
    ("root\\subscription","HIGH","WMI Persistence","References the WMI subscription namespace."),
    ("commandlineeventconsumer","HIGH","WMI Persistence","References a WMI command-line event consumer."),
    ("__eventfilter","HIGH","WMI Persistence","References a WMI event filter."),
    ("shell:startup","HIGH","Startup Folder","References the Windows Startup folder."),
    ("start menu\\programs\\startup","HIGH","Startup Folder","References the Windows Startup folder."),
    ("powershell -enc","REVIEW","Encoded PowerShell","Uses encoded PowerShell."),
    ("powershell.exe -enc","REVIEW","Encoded PowerShell","Uses encoded PowerShell."),
    ("-encodedcommand","REVIEW","Encoded PowerShell","Uses PowerShell EncodedCommand."),
    ("frombase64string","REVIEW","Obfuscation","Decodes Base64 data."),
    ("invoke-expression","REVIEW","PowerShell Execution","Uses Invoke-Expression."),
    ("iex(","REVIEW","PowerShell Execution","Uses the IEX alias."),
    ("invoke-webrequest","REVIEW","Network Download","Downloads content with PowerShell."),
    ("downloadstring","REVIEW","Network Download","Downloads content into memory."),
    ("bitsadmin","REVIEW","Network Download","Uses BITSAdmin."),
    ("certutil -urlcache","REVIEW","Network Download","Uses CertUtil to retrieve content."),
    ("mshta ","REVIEW","Living-off-the-land","Launches MSHTA."),
    ("rundll32 ","REVIEW","Living-off-the-land","Launches Rundll32."),
    ("regsvr32 ","REVIEW","Living-off-the-land","Launches Regsvr32."),
    ("wscript ","REVIEW","Script Host","Launches Windows Script Host."),
    ("cscript ","REVIEW","Script Host","Launches Windows Script Host.")
]

BINARY_PATTERNS=[
    ("currentversion\\run","REVIEW","Registry Autorun String","Binary contains a string referencing the Windows Run key."),
    ("currentversion\\runonce","REVIEW","Registry Autorun String","Binary contains a string referencing the Windows RunOnce key."),
    ("schtasks.exe","REVIEW","Scheduled Task String","Binary contains a scheduled-task related string."),
    ("taskschd.dll","REVIEW","Scheduled Task String","Binary references Task Scheduler components."),
    ("start menu\\programs\\startup","REVIEW","Startup Folder String","Binary references the Windows Startup folder."),
    ("powershell.exe","REVIEW","PowerShell String","Binary contains a PowerShell executable string."),
    ("cmd.exe","REVIEW","Command Shell String","Binary contains a command-shell string.")
]

RESERVED_NAMES={"CON","PRN","AUX","NUL",*(f"COM{i}" for i in range(1,10)),*(f"LPT{i}" for i in range(1,10))}

@dataclass
class Entry:
    name:str
    size:int
    compressed:int
    kind:str

@dataclass
class Finding:
    severity:str
    category:str
    file:str
    reason:str
    evidence:str

def clean(value):
    return str(value).replace("\r","\\r").replace("\n","\\n").replace("\t","\\t")

def prepare_cache():
    CACHE_DIR.mkdir(parents=True,exist_ok=True)

def cleanup_previews():
    try:
        if not CACHE_DIR.exists():
            return
        for path in CACHE_DIR.glob("preview-*.txt"):
            try:
                path.unlink()
            except OSError:
                pass
    except OSError:
        pass

def clear():
    os.system("cls")

def dropped_path(raw):
    raw=raw.strip()
    if not raw:
        return None
    if raw.startswith("& "):
        raw=raw[2:].strip()
    try:
        parts=shlex.split(raw,posix=False)
        if parts:
            return Path(parts[0].strip('"')).expanduser()
    except ValueError:
        pass
    return Path(raw.strip("'\"")).expanduser()

def zip_symlink(info):
    mode=(info.external_attr>>16)&0xFFFF
    return stat.S_ISLNK(mode)

def executable_mode(info):
    mode=(info.external_attr>>16)&0xFFFF
    return bool(mode&0o111)

def unsafe_archive_path(name):
    normalized=name.replace("\\","/")
    if normalized.startswith("/") or normalized.startswith("//"):
        return True
    if re.match(r"^[A-Za-z]:",normalized):
        return True
    try:
        return ".." in PurePosixPath(normalized).parts
    except Exception:
        return True

def has_ads_name(name):
    normalized=name.replace("\\","/")
    return any(":" in part for part in normalized.split("/") if part)

def has_reserved_name(name):
    normalized=name.replace("\\","/")
    for part in normalized.split("/"):
        stem=part.rstrip(" .").split(".")[0].upper()
        if stem in RESERVED_NAMES:
            return True
    return False

def kind_of(info):
    if info.is_dir():
        return "directory"
    if zip_symlink(info):
        return "symlink"
    lower=info.filename.lower()
    suffix=Path(lower).suffix
    if suffix==".zip":
        return "zip"
    if suffix in SCRIPT_EXTENSIONS:
        return "script"
    if suffix in EXECUTABLE_EXTENSIONS:
        return "executable"
    if suffix in TEXT_EXTENSIONS:
        return "text"
    if suffix==".lnk":
        return "shortcut"
    return "file"

def add(findings,severity,category,file,reason,evidence=""):
    findings.append(Finding(severity,category,file,reason,evidence))

def read_limited(zf,info,limit):
    with zf.open(info,"r") as handle:
        return handle.read(limit)

def scan_text(name,data,findings):
    text=data.decode("utf-8","replace")
    lower=text.lower()
    path_lower=lower.replace("/","\\")
    for pattern,severity,category,reason in CONTENT_RULES:
        if pattern in lower or pattern in path_lower:
            add(findings,severity,category,name,reason,pattern)

def extract_binary_strings(data):
    ascii_strings=re.findall(rb"[\x20-\x7e]{6,}",data)
    wide_strings=re.findall(rb"(?:[\x20-\x7e]\x00){6,}",data)
    out=[]
    for value in ascii_strings[:2500]:
        out.append(value.decode("ascii","ignore"))
    for value in wide_strings[:2500]:
        out.append(value.decode("utf-16le","ignore"))
    return "\n".join(out).lower()

def scan_binary(name,data,findings):
    strings=extract_binary_strings(data)
    for pattern,severity,category,reason in BINARY_PATTERNS:
        if pattern in strings:
            add(findings,severity,category,name,reason,pattern)

def sha256_file(path):
    digest=hashlib.sha256()
    with open(path,"rb") as handle:
        for chunk in iter(lambda:handle.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()

def scan_archive(path):
    entries=[]
    findings=[]
    scan_used=0
    total_uncompressed=0
    with zipfile.ZipFile(path,"r") as zf:
        infos=zf.infolist()
        if len(infos)>MAX_ENTRIES:
            add(findings,"HIGH","Archive Size","[archive]",f"Archive contains {len(infos):,} entries.","Possible archive bomb.")
        for info in infos:
            name=info.filename
            lower=name.lower().replace("\\","/")
            suffix=Path(lower).suffix
            total_uncompressed+=info.file_size
            entries.append(Entry(name,info.file_size,info.compress_size,kind_of(info)))

            if unsafe_archive_path(name):
                add(findings,"CRITICAL","Extraction Escape",name,"Archive path attempts to escape the normal extraction folder.",name)
            if has_ads_name(name):
                add(findings,"HIGH","NTFS Alternate Stream",name,"Archive entry contains ':' in a path component, which can represent an NTFS alternate data stream.",name)
            if has_reserved_name(name):
                add(findings,"REVIEW","Reserved Windows Name",name,"Archive uses a Windows reserved device name.",name)
            if zip_symlink(info):
                add(findings,"HIGH","Symbolic Link",name,"Archive contains a symbolic link. FileSentry never creates it.",name)
            if "appdata/roaming/microsoft/windows/start menu/programs/startup/" in lower:
                add(findings,"HIGH","Startup Folder",name,"Targets the current-user Windows Startup folder.",name)
            if "programdata/microsoft/windows/start menu/programs/startup/" in lower:
                add(findings,"HIGH","Startup Folder",name,"Targets the all-users Windows Startup folder.",name)
            if "windows/system32/tasks/" in lower:
                add(findings,"HIGH","Scheduled Task",name,"Targets the Windows Task Scheduler storage directory.",name)
            if lower.endswith("autorun.inf"):
                add(findings,"REVIEW","Autorun Configuration",name,"Contains autorun.inf. Modern Windows restricts AutoRun, and it does not run merely from ZIP extraction.",name)
            if suffix==".lnk":
                add(findings,"REVIEW","Windows Shortcut",name,"Windows shortcut files can launch programs or commands when opened.",name)
            if suffix==".url":
                add(findings,"REVIEW","Internet Shortcut",name,"Internet shortcut files can open a URL or registered protocol when opened.",name)
            if suffix in SCRIPT_EXTENSIONS:
                add(findings,"REVIEW","Executable Script",name,f"{suffix} can execute commands when opened or invoked. It does not normally run just because a ZIP is extracted.",name)
            if suffix in EXECUTABLE_EXTENSIONS:
                add(findings,"REVIEW","Executable Content",name,f"Archive contains a Windows executable/installable file ({suffix}).",name)
            if suffix==".reg":
                add(findings,"REVIEW","Registry File",name,"Registry files can modify Windows configuration when imported.",name)
            if suffix==".zip":
                add(findings,"REVIEW","Nested Archive",name,"Archive contains another ZIP. It is listed but not recursively extracted.",name)
            if executable_mode(info) and not info.is_dir():
                add(findings,"REVIEW","Executable Permission",name,"ZIP metadata marks this file as executable.",name)

            ratio=info.file_size/max(info.compress_size,1)
            if info.file_size>=ZIP_BOMB_SIZE and ratio>=ZIP_BOMB_RATIO:
                add(findings,"HIGH","Compression Bomb",name,f"Very high compression ratio detected: {ratio:.0f}:1.",f"{info.file_size:,} bytes -> {info.compress_size:,} bytes")
            if info.flag_bits&0x1:
                add(findings,"REVIEW","Encrypted File",name,"Archive entry is encrypted and cannot be fully inspected without a password.","")
                continue
            if info.is_dir() or info.file_size==0 or info.file_size>MAX_SCAN_FILE or scan_used>=MAX_SCAN_TOTAL:
                continue

            should_text=suffix in TEXT_EXTENSIONS
            should_binary=suffix in EXECUTABLE_EXTENSIONS or suffix==".lnk"
            if not should_text and not should_binary:
                continue

            try:
                limit=min(MAX_SCAN_FILE,MAX_SCAN_TOTAL-scan_used)
                data=read_limited(zf,info,limit)
            except Exception:
                continue

            scan_used+=len(data)
            if should_text:
                scan_text(name,data,findings)
            elif should_binary:
                scan_binary(name,data,findings)

    if total_uncompressed>5*1024*1024*1024:
        add(findings,"HIGH","Archive Size","[archive]",f"Archive claims {total_uncompressed/1024/1024/1024:.1f} GB uncompressed.","Possible archive bomb.")

    if any(item.severity=="CRITICAL" for item in findings):
        risk="CRITICAL"
    elif any(item.severity=="HIGH" for item in findings):
        risk="HIGH"
    elif any(item.severity=="REVIEW" for item in findings):
        risk="REVIEW"
    else:
        risk="LOW"

    return entries,findings,risk,sha256_file(path)

def looks_text(data,name):
    if Path(name.lower()).suffix in TEXT_EXTENSIONS:
        return True
    sample=data[:8192]
    if not sample:
        return True
    if b"\x00" in sample:
        return False
    printable=sum(1 for byte in sample if byte in b"\n\r\t" or 32<=byte<=126)
    return printable/max(len(sample),1)>.80

def hex_dump(data):
    lines=[]
    for offset in range(0,len(data),16):
        chunk=data[offset:offset+16]
        hexpart=" ".join(f"{byte:02x}" for byte in chunk)
        text="".join(chr(byte) if 32<=byte<=126 else "." for byte in chunk)
        lines.append(f"{offset:08x}  {hexpart:<47}  {text}")
    return "\n".join(lines)

def open_preview(zip_path,entry):
    prepare_cache()
    output=None
    try:
        with zipfile.ZipFile(zip_path,"r") as zf:
            info=zf.getinfo(entry.name)
            if info.flag_bits&0x1:
                return "Preview blocked: encrypted entry."
            ratio=info.file_size/max(info.compress_size,1)
            if info.file_size>=ZIP_BOMB_SIZE and ratio>=ZIP_BOMB_RATIO:
                return "Preview blocked: possible compression bomb."
            data=read_limited(zf,info,MAX_PREVIEW)
    except Exception as exc:
        return f"Preview failed: {exc}"

    header=(
        "FileSentry SAFE PREVIEW\r\n"
        "=======================\r\n"
        f"Archive: {zip_path}\r\n"
        f"Entry:   {clean(entry.name)}\r\n"
        f"Size:    {entry.size:,} bytes\r\n\r\n"
        "The original archive entry was NOT extracted to disk or executed.\r\n"
        "This is a separate plain-text preview generated by FileSentry.\r\n\r\n"
    )

    if looks_text(data,entry.name):
        body=data.decode("utf-8","replace")
        if entry.size>MAX_PREVIEW:
            body+=f"\r\n\r\n[Preview truncated at {MAX_PREVIEW:,} bytes]"
    else:
        binary=data[:MAX_BINARY_PREVIEW]
        body="[Binary file converted to hexadecimal text]\r\n\r\n"+hex_dump(binary)
        if entry.size>MAX_BINARY_PREVIEW:
            body+=f"\r\n\r\n[Binary preview truncated at {MAX_BINARY_PREVIEW:,} bytes]"

    fd=None
    try:
        fd,name=tempfile.mkstemp(prefix="preview-",suffix=".txt",dir=CACHE_DIR)
        output=Path(name)
        with os.fdopen(fd,"w",encoding="utf-8",errors="replace",newline="") as handle:
            fd=None
            handle.write(header+body)
        subprocess.Popen(["notepad.exe",str(output)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except Exception as exc:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
        if output is not None:
            try:
                output.unlink()
            except OSError:
                pass
        return f"Could not open Notepad preview: {exc}"

    return f"Opened safe text preview: {clean(entry.name)}"

def fmt_size(size):
    if size<1024:
        return f"{size} B"
    if size<1024*1024:
        return f"{size/1024:.1f} KB"
    if size<1024*1024*1024:
        return f"{size/1024/1024:.1f} MB"
    return f"{size/1024/1024/1024:.1f} GB"

def get_key():
    char=msvcrt.getwch()
    if char in ("\x00","\xe0"):
        code=msvcrt.getwch()
        return {"H":"UP","P":"DOWN","I":"PAGEUP","Q":"PAGEDOWN"}.get(code,"SPECIAL")
    if char=="\r":
        return "ENTER"
    if char=="\x1b":
        return "ESC"
    return char.lower()

def prompt_zip():
    while True:
        clear()
        print(f"  FileSentry v{VERSION}")
        print("  Safe static ZIP inspector for Windows")
        print()
        print("  Drop ZIP here and press Enter:")
        raw=input("  > ")
        path=dropped_path(raw)
        if path and path.is_file() and zipfile.is_zipfile(path):
            return path
        print()
        print("  That is not a valid ZIP. Press any key and try again.")
        msvcrt.getwch()

def show_findings(findings):
    offset=0
    while True:
        clear()
        try:
            height=os.get_terminal_size().lines
        except OSError:
            height=30
        print("  Security Findings")
        print("  Up/Down scroll   q/ESC return")
        print()
        lines=[]
        if not findings:
            lines=["No indicators were detected by the current static rules."]
        else:
            for finding in findings:
                lines.extend([f"[{finding.severity}] {finding.category}",f"File: {clean(finding.file)}",finding.reason])
                if finding.evidence:
                    lines.append(f"Evidence: {clean(finding.evidence)}")
                lines.append("")
        visible=max(1,height-5)
        for line in lines[offset:offset+visible]:
            print("  "+line)
        key=get_key()
        if key in ("q","ESC"):
            return
        if key=="DOWN" and offset<max(0,len(lines)-visible):
            offset+=1
        elif key=="UP" and offset>0:
            offset-=1
        elif key=="PAGEDOWN":
            offset=min(max(0,len(lines)-visible),offset+visible)
        elif key=="PAGEUP":
            offset=max(0,offset-visible)

def archive_ui(path,entries,findings,risk,digest):
    selected=0
    top=0
    status=""
    flagged={item.file for item in findings}
    while True:
        clear()
        try:
            width,height=os.get_terminal_size()
        except OSError:
            width,height=120,30
        print("  FileSentry")
        print(f"  {path.name}   Risk: {risk}   Files: {len(entries)}   Findings: {len(findings)}")
        print(f"  SHA256: {digest}")
        print("  Up/Down select   Enter preview   f findings   r new ZIP   q quit")
        print()
        list_height=max(1,height-8)
        if entries:
            if selected<top:
                top=selected
            if selected>=top+list_height:
                top=selected-list_height+1
        for index in range(top,min(len(entries),top+list_height)):
            entry=entries[index]
            marker="!" if entry.name in flagged else " "
            kind={"directory":"DIR","symlink":"LINK","zip":"ZIP","text":"TXT","script":"SCRIPT","executable":"EXE","shortcut":"LNK"}.get(entry.kind,"FILE")
            line=f"{marker} {kind:<6} {fmt_size(entry.size):>10}  {clean(entry.name)}"
            prefix="> " if index==selected else "  "
            print((prefix+line)[:max(20,width-4)])
        if status:
            print()
            print("  "+status[:max(20,width-4)])
        key=get_key()
        if key=="q":
            return "quit"
        if key=="r":
            return "reload"
        if key=="f":
            show_findings(findings)
            continue
        if key=="DOWN" and selected<len(entries)-1:
            selected+=1
        elif key=="UP" and selected>0:
            selected-=1
        elif key=="PAGEDOWN":
            selected=min(max(0,len(entries)-1),selected+list_height)
        elif key=="PAGEUP":
            selected=max(0,selected-list_height)
        elif key=="ENTER" and entries:
            entry=entries[selected]
            if entry.kind=="directory":
                status="Directory selected."
            elif entry.kind=="symlink":
                status="Symlink preview blocked."
            else:
                status=open_preview(path,entry)

def main():
    if os.name!="nt":
        print("This FileSentry build is for Windows.")
        sys.exit(1)
    try:
        os.system("title FileSentry")
    except Exception:
        pass
    while True:
        path=prompt_zip()
        clear()
        print("  Scanning archive...")
        try:
            entries,findings,risk,digest=scan_archive(path)
        except Exception as exc:
            print()
            print(f"  Scan failed: {exc}")
            print("  Press any key.")
            msvcrt.getwch()
            continue
        action=archive_ui(path,entries,findings,risk,digest)
        if action=="quit":
            break

if __name__=="__main__":
    prepare_cache()
    cleanup_previews()
    atexit.register(cleanup_previews)
    try:
        main()
    except KeyboardInterrupt:
        pass
