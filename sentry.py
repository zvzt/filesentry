#!/usr/bin/env python3
import curses
import hashlib
import os
import plistlib
import re
import shlex
import stat
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

VERSION="0.1.0"
MAX_PREVIEW=2*1024*1024
MAX_BINARY_PREVIEW=256*1024
MAX_SCAN_FILE=256*1024
MAX_SCAN_TOTAL=8*1024*1024
MAX_ENTRIES=20000
ZIP_BOMB_SIZE=20*1024*1024
ZIP_BOMB_RATIO=200
CACHE_DIR=Path.home()/"Library"/"Caches"/"FileSentry"/"previews"

TEXT_EXTENSIONS={
    ".txt",".md",".json",".xml",".plist",".sh",".command",".zsh",".bash",
    ".py",".js",".ts",".lua",".cfg",".conf",".ini",".yaml",".yml",".toml",
    ".html",".css",".csv",".log",".rb",".php",".java",".c",".h",".cpp",
    ".hpp",".rs",".go"
}

CONTENT_RULES=[
    ("launchctl load","HIGH","Launchd","Loads a macOS LaunchAgent or LaunchDaemon."),
    ("launchctl bootstrap","HIGH","Launchd","Loads a macOS LaunchAgent or LaunchDaemon."),
    ("library/launchagents","HIGH","Persistence","References the macOS LaunchAgents autorun directory."),
    ("library/launchdaemons","HIGH","Persistence","References the macOS LaunchDaemons autorun directory."),
    ("smappservice","HIGH","Login Item","References Apple's login-item API."),
    ("smloginitemsetenabled","HIGH","Login Item","Attempts to enable a macOS login item."),
    ("crontab ","HIGH","Scheduled Execution","Creates or modifies scheduled commands."),
    (".zshrc","REVIEW","Shell Startup","References the zsh startup configuration."),
    (".zprofile","REVIEW","Shell Startup","References the zsh login configuration."),
    (".bash_profile","REVIEW","Shell Startup","References the bash startup configuration."),
    ("xattr -d com.apple.quarantine","HIGH","Quarantine Removal","Attempts to remove the macOS quarantine attribute."),
    ("xattr -dr com.apple.quarantine","HIGH","Quarantine Removal","Attempts to recursively remove quarantine attributes."),
    ("spctl --master-disable","HIGH","Gatekeeper","Attempts to disable Gatekeeper."),
    ("osascript","REVIEW","AppleScript","Executes AppleScript commands."),
    ("chmod +x","REVIEW","Executable","Makes another file executable."),
    ("curl ","REVIEW","Network","Downloads data from a network location."),
    ("wget ","REVIEW","Network","Downloads data from a network location.")
]

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
    return str(value).replace("\n","\\n").replace("\r","\\r").replace("\t","\\t")

def dropped_path(raw):
    raw=raw.strip()
    if not raw:
        return None
    try:
        parts=shlex.split(raw)
        if parts:
            return Path(parts[0]).expanduser()
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
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:",normalized):
        return True
    try:
        return ".." in PurePosixPath(normalized).parts
    except Exception:
        return True

def kind_of(info):
    if info.is_dir():
        return "directory"
    if zip_symlink(info):
        return "symlink"
    lower=info.filename.lower()
    if lower.endswith(".zip"):
        return "zip"
    if Path(lower).suffix in TEXT_EXTENSIONS:
        return "text"
    return "file"

def add(findings,severity,category,file,reason,evidence=""):
    findings.append(Finding(severity,category,file,reason,evidence))

def scan_plist(name,data,findings):
    try:
        value=plistlib.loads(data)
    except Exception:
        return
    if not isinstance(value,dict):
        return
    run=value.get("RunAtLoad",False)
    keep=value.get("KeepAlive",False)
    program=value.get("Program","")
    args=value.get("ProgramArguments",[])
    label=value.get("Label","")
    if run or keep:
        evidence=f"Label: {label}\nProgram: {program}\nArguments: {args}\nRunAtLoad: {run}\nKeepAlive: {keep}"
        add(findings,"HIGH","Automatic Execution",name,"Launchd configuration is set to start automatically.",evidence)

def scan_text(name,data,findings):
    text=data.decode("utf-8","replace")
    lower=text.lower()
    for pattern,severity,category,reason in CONTENT_RULES:
        if pattern in lower:
            add(findings,severity,category,name,reason,pattern)

def read_limited(zf,info,limit):
    with zf.open(info,"r") as handle:
        return handle.read(limit)

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
            lower=name.lower()
            total_uncompressed+=info.file_size
            entries.append(Entry(name,info.file_size,info.compress_size,kind_of(info)))
            if unsafe_archive_path(name):
                add(findings,"CRITICAL","Extraction Escape",name,"Archive path attempts to escape the normal extraction folder.",name)
            if zip_symlink(info):
                add(findings,"HIGH","Symbolic Link",name,"Archive contains a symbolic link. FileSentry never creates it.",name)
            if "library/launchagents/" in lower:
                add(findings,"HIGH","LaunchAgent",name,"Targets the macOS LaunchAgents persistence location.",name)
            if "library/launchdaemons/" in lower:
                add(findings,"HIGH","LaunchDaemon",name,"Targets the macOS LaunchDaemons persistence location.",name)
            if lower.endswith(".command"):
                add(findings,"REVIEW","Executable Script",name,"macOS .command files can execute shell commands if manually opened. They do not normally run just because a ZIP is extracted.",name)
            if "/contents/macos/" in lower:
                add(findings,"REVIEW","macOS Application",name,"File is inside a macOS application's executable directory.",name)
            if executable_mode(info) and not info.is_dir():
                add(findings,"REVIEW","Executable Permission",name,"ZIP metadata marks this file as executable.",name)
            if lower.endswith(".zip") and not info.is_dir():
                add(findings,"REVIEW","Nested Archive",name,"Archive contains another ZIP. FileSentry lists it but does not recursively unpack it.",name)
            ratio=info.file_size/max(info.compress_size,1)
            if info.file_size>=ZIP_BOMB_SIZE and ratio>=ZIP_BOMB_RATIO:
                add(findings,"HIGH","Compression Bomb",name,f"Very high compression ratio detected: {ratio:.0f}:1.",f"{info.file_size:,} bytes -> {info.compress_size:,} bytes")
            if info.is_dir() or info.file_size==0:
                continue
            suffix=Path(lower).suffix
            if suffix not in TEXT_EXTENSIONS or info.file_size>MAX_SCAN_FILE or scan_used>=MAX_SCAN_TOTAL:
                continue
            try:
                limit=min(MAX_SCAN_FILE,MAX_SCAN_TOTAL-scan_used)
                data=read_limited(zf,info,limit)
            except RuntimeError:
                add(findings,"REVIEW","Encrypted File",name,"File is encrypted and could not be inspected.","")
                continue
            except Exception:
                continue
            scan_used+=len(data)
            if suffix==".plist":
                scan_plist(name,data,findings)
            scan_text(name,data,findings)
    if total_uncompressed>5*1024*1024*1024:
        add(findings,"HIGH","Archive Size","[archive]",f"Archive claims {total_uncompressed/1024/1024/1024:.1f} GB uncompressed.","Possible archive bomb.")
    if any(x.severity=="CRITICAL" for x in findings):
        risk="CRITICAL"
    elif any(x.severity=="HIGH" for x in findings):
        risk="HIGH"
    elif any(x.severity=="REVIEW" for x in findings):
        risk="REVIEW"
    else:
        risk="LOW"
    return entries,findings,risk

def looks_text(data,name):
    if Path(name.lower()).suffix in TEXT_EXTENSIONS:
        return True
    sample=data[:8192]
    if not sample:
        return True
    if b"\x00" in sample:
        return False
    printable=sum(1 for b in sample if b in b"\n\r\t" or 32<=b<=126)
    return printable/max(len(sample),1)>.80

def hex_dump(data):
    lines=[]
    for offset in range(0,len(data),16):
        chunk=data[offset:offset+16]
        hx=" ".join(f"{b:02x}" for b in chunk)
        asc="".join(chr(b) if 32<=b<=126 else "." for b in chunk)
        lines.append(f"{offset:08x}  {hx:<47}  {asc}")
    return "\n".join(lines)

def plist_preview(data):
    try:
        value=plistlib.loads(data)
        return plistlib.dumps(value,fmt=plistlib.FMT_XML,sort_keys=False).decode("utf-8","replace")
    except Exception:
        return None

def open_preview(zip_path,entry):
    CACHE_DIR.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256((str(zip_path)+"|"+entry.name).encode()).hexdigest()[:16]
    output=CACHE_DIR/f"preview-{digest}.txt"
    try:
        with zipfile.ZipFile(zip_path,"r") as zf:
            info=zf.getinfo(entry.name)
            ratio=info.file_size/max(info.compress_size,1)
            if info.file_size>=ZIP_BOMB_SIZE and ratio>=ZIP_BOMB_RATIO:
                return "Preview blocked: possible compression bomb."
            data=read_limited(zf,info,MAX_PREVIEW)
    except RuntimeError as exc:
        return f"Could not read file: {exc}"
    except Exception as exc:
        return f"Preview failed: {exc}"
    header=(
        "FileSentry SAFE PREVIEW\n"
        "=======================\n"
        f"Archive: {zip_path}\n"
        f"Entry:   {clean(entry.name)}\n"
        f"Size:    {entry.size:,} bytes\n\n"
        "The original archive entry was not written to disk or executed.\n"
        "This is a separate plain-text preview generated by FileSentry.\n\n"
    )
    plist_text=plist_preview(data) if entry.name.lower().endswith(".plist") else None
    if plist_text is not None:
        body=plist_text
    elif looks_text(data,entry.name):
        body=data.decode("utf-8","replace")
        if entry.size>MAX_PREVIEW:
            body+=f"\n\n[Preview truncated at {MAX_PREVIEW:,} bytes]"
    else:
        binary=data[:MAX_BINARY_PREVIEW]
        body="[Binary file converted to hexadecimal text]\n\n"+hex_dump(binary)
        if entry.size>MAX_BINARY_PREVIEW:
            body+=f"\n\n[Binary preview truncated at {MAX_BINARY_PREVIEW:,} bytes]"
    try:
        if output.exists():
            os.chmod(output,0o600)
        output.write_text(header+body,encoding="utf-8",errors="replace")
        os.chmod(output,0o400)
        subprocess.Popen(["open","-a","TextEdit",str(output)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    except Exception as exc:
        return f"Could not open TextEdit preview: {exc}"
    return f"Opened safe text preview: {clean(entry.name)}"

def fmt_size(size):
    if size<1024:
        return f"{size} B"
    if size<1024*1024:
        return f"{size/1024:.1f} KB"
    if size<1024*1024*1024:
        return f"{size/1024/1024:.1f} MB"
    return f"{size/1024/1024/1024:.1f} GB"

def safe_add(win,y,x,text,attr=0):
    h,w=win.getmaxyx()
    if y<0 or y>=h or x>=w:
        return
    try:
        win.addnstr(y,x,clean(text),max(0,w-x-1),attr)
    except curses.error:
        pass

def prompt_zip(stdscr):
    while True:
        stdscr.clear()
        safe_add(stdscr,1,2,f"FileSentry v{VERSION}",curses.A_BOLD)
        safe_add(stdscr,2,2,"Safe static ZIP inspector for macOS")
        safe_add(stdscr,4,2,"Drop ZIP here and press Enter:")
        safe_add(stdscr,5,2,"> ")
        safe_add(stdscr,7,2,"Nothing is extracted or executed.")
        stdscr.refresh()
        curses.echo()
        try:
            raw=stdscr.getstr(5,4,4096).decode("utf-8","replace")
        finally:
            curses.noecho()
        path=dropped_path(raw)
        if path and path.is_file() and zipfile.is_zipfile(path):
            return path
        safe_add(stdscr,9,2,"That is not a valid ZIP. Press any key and try again.",curses.A_BOLD)
        stdscr.refresh()
        stdscr.getch()

def show_findings(stdscr,findings):
    offset=0
    while True:
        stdscr.clear()
        h,_=stdscr.getmaxyx()
        safe_add(stdscr,0,2,"Security Findings",curses.A_BOLD)
        safe_add(stdscr,1,2,"Up/Down scroll   q/ESC return")
        lines=[]
        if not findings:
            lines=["No indicators were detected by the current static rules."]
        else:
            for finding in findings:
                lines.extend([
                    f"[{finding.severity}] {finding.category}",
                    f"File: {finding.file}",
                    finding.reason
                ])
                if finding.evidence:
                    lines.append(f"Evidence: {finding.evidence}")
                lines.append("")
        visible=max(1,h-4)
        for i,line in enumerate(lines[offset:offset+visible]):
            safe_add(stdscr,3+i,2,line)
        stdscr.refresh()
        key=stdscr.getch()
        if key in (ord("q"),27):
            return
        if key==curses.KEY_DOWN and offset<max(0,len(lines)-visible):
            offset+=1
        elif key==curses.KEY_UP and offset>0:
            offset-=1
        elif key==curses.KEY_NPAGE:
            offset=min(max(0,len(lines)-visible),offset+visible)
        elif key==curses.KEY_PPAGE:
            offset=max(0,offset-visible)

def archive_ui(stdscr,path,entries,findings,risk):
    selected=0
    top=0
    status=""
    flagged={f.file for f in findings}
    while True:
        stdscr.clear()
        h,_=stdscr.getmaxyx()
        safe_add(stdscr,0,2,"FileSentry",curses.A_BOLD)
        safe_add(stdscr,1,2,f"{path.name}   Risk: {risk}   Files: {len(entries)}   Findings: {len(findings)}")
        safe_add(stdscr,2,2,"Up/Down select   Enter preview   f findings   r new ZIP   q quit")
        list_top=4
        list_height=max(1,h-7)
        if selected<top:
            top=selected
        if selected>=top+list_height:
            top=selected-list_height+1
        for screen_y,index in enumerate(range(top,min(len(entries),top+list_height)),start=list_top):
            entry=entries[index]
            marker="!" if entry.name in flagged else " "
            kind={"directory":"DIR","symlink":"LINK","zip":"ZIP","text":"TXT"}.get(entry.kind,"FILE")
            line=f"{marker} {kind:<4} {fmt_size(entry.size):>10}  {entry.name}"
            safe_add(stdscr,screen_y,1,line,curses.A_REVERSE if index==selected else 0)
        if status:
            safe_add(stdscr,h-2,2,status)
        stdscr.refresh()
        key=stdscr.getch()
        if key==ord("q"):
            return "quit"
        if key==ord("r"):
            return "reload"
        if key==ord("f"):
            show_findings(stdscr,findings)
            continue
        if key==curses.KEY_DOWN and selected<len(entries)-1:
            selected+=1
        elif key==curses.KEY_UP and selected>0:
            selected-=1
        elif key==curses.KEY_NPAGE:
            selected=min(len(entries)-1,selected+list_height)
        elif key==curses.KEY_PPAGE:
            selected=max(0,selected-list_height)
        elif key in (10,13,curses.KEY_ENTER) and entries:
            entry=entries[selected]
            if entry.kind=="directory":
                status="Directory selected."
            elif entry.kind=="symlink":
                status="Symlink preview blocked."
            else:
                status=open_preview(path,entry)

def main(stdscr):
    curses.curs_set(1)
    stdscr.keypad(True)
    while True:
        path=prompt_zip(stdscr)
        stdscr.clear()
        safe_add(stdscr,2,2,"Scanning archive...")
        stdscr.refresh()
        try:
            entries,findings,risk=scan_archive(path)
        except Exception as exc:
            safe_add(stdscr,4,2,f"Scan failed: {exc}")
            safe_add(stdscr,6,2,"Press any key.")
            stdscr.refresh()
            stdscr.getch()
            continue
        curses.curs_set(0)
        action=archive_ui(stdscr,path,entries,findings,risk)
        if action=="quit":
            break
        curses.curs_set(1)

if __name__=="__main__":
    try:
        curses.wrapper(main)
    except KeyboardInterrupt:
        pass
