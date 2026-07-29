"""Central safety policy for POCKET desktop + web + nexus actions."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path.home() / ".pocket"
LOG = ROOT / "safety.log"
_lock = Lock()

# Explicit allowlist — agents cannot open arbitrary executables.
# group: native = Windows / Microsoft built-ins · third_party = common installs (esp. AI)
ALLOWED_APPS: Dict[str, Dict[str, str]] = {
    # ---- Native / Microsoft (20+) ----
    "notepad": {"cmd": "notepad.exe", "label": "Notepad", "risk": "low", "group": "native"},
    "explorer": {"cmd": "explorer.exe", "label": "File Explorer", "risk": "low", "group": "native"},
    "calc": {"cmd": "calc.exe", "label": "Calculator", "risk": "low", "group": "native"},
    "paint": {"cmd": "mspaint.exe", "label": "Paint", "risk": "low", "group": "native"},
    "cmd": {"cmd": "cmd.exe", "label": "Command Prompt", "risk": "medium", "group": "native"},
    "powershell": {"cmd": "powershell.exe", "label": "PowerShell", "risk": "medium", "group": "native"},
    "wt": {"cmd": "wt.exe", "label": "Windows Terminal", "risk": "medium", "group": "native"},
    "edge": {"cmd": "msedge", "label": "Microsoft Edge", "risk": "medium", "group": "native"},
    "word": {"cmd": "winword.exe", "label": "Microsoft Word", "risk": "medium", "group": "native"},
    "excel": {"cmd": "excel.exe", "label": "Microsoft Excel", "risk": "medium", "group": "native"},
    "powerpoint": {"cmd": "powerpnt.exe", "label": "PowerPoint", "risk": "medium", "group": "native"},
    "outlook": {"cmd": "outlook.exe", "label": "Outlook", "risk": "medium", "group": "native"},
    "onenote": {"cmd": "onenote.exe", "label": "OneNote", "risk": "low", "group": "native"},
    "teams": {"cmd": "ms-teams.exe", "label": "Microsoft Teams", "risk": "medium", "group": "native"},
    "snip": {"cmd": "snippingtool.exe", "label": "Snipping Tool", "risk": "low", "group": "native"},
    "screenclip": {"cmd": "ms-screenclip:", "label": "Screen Clip (Win+Shift+S)", "risk": "low", "group": "native"},
    "photos": {"cmd": "ms-photos:", "label": "Photos", "risk": "low", "group": "native"},
    "settings": {"cmd": "ms-settings:", "label": "Windows Settings", "risk": "low", "group": "native"},
    "store": {"cmd": "ms-windows-store:", "label": "Microsoft Store", "risk": "low", "group": "native"},
    "taskmgr": {"cmd": "taskmgr.exe", "label": "Task Manager", "risk": "low", "group": "native"},
    "control": {"cmd": "control.exe", "label": "Control Panel", "risk": "low", "group": "native"},
    "copilot": {"cmd": "ms-copilot:", "label": "Microsoft Copilot", "risk": "low", "group": "native"},
    "clipchamp": {"cmd": "clipchamp.exe", "label": "Clipchamp", "risk": "low", "group": "native"},
    "sticky": {"cmd": "stikynot.exe", "label": "Sticky Notes", "risk": "low", "group": "native"},
    "voice": {"cmd": "soundrecorder.exe", "label": "Voice Recorder", "risk": "low", "group": "native"},
    "maps": {"cmd": "bingmaps:", "label": "Windows Maps", "risk": "low", "group": "native"},
    "clock": {"cmd": "ms-clock:", "label": "Clock / Alarms", "risk": "low", "group": "native"},
    "media": {"cmd": "mswindowsmusic:", "label": "Media Player", "risk": "low", "group": "native"},
    # ---- Third-party / AI-friendly (20+) ----
    "chrome": {"cmd": "chrome", "label": "Google Chrome", "risk": "medium", "group": "third_party"},
    "firefox": {"cmd": "firefox", "label": "Firefox", "risk": "medium", "group": "third_party"},
    "brave": {"cmd": "brave", "label": "Brave Browser", "risk": "medium", "group": "third_party"},
    "code": {"cmd": "code", "label": "VS Code", "risk": "medium", "group": "third_party"},
    "cursor": {"cmd": "cursor", "label": "Cursor", "risk": "medium", "group": "third_party"},
    "windsurf": {"cmd": "windsurf", "label": "Windsurf", "risk": "medium", "group": "third_party"},
    "antigravity": {"cmd": "antigravity", "label": "Antigravity", "risk": "medium", "group": "third_party"},
    "linear": {"cmd": "Linear", "label": "Linear", "risk": "medium", "group": "third_party"},
    "notion_calendar": {"cmd": "Notion Calendar", "label": "Notion Calendar", "risk": "low", "group": "third_party"},
    "1password": {"cmd": "1Password", "label": "1Password", "risk": "medium", "group": "third_party"},
    "raycast": {"cmd": "Raycast", "label": "Raycast", "risk": "low", "group": "third_party"},
    "arc": {"cmd": "Arc", "label": "Arc Browser", "risk": "medium", "group": "third_party"},
    "warp": {"cmd": "warp", "label": "Warp Terminal", "risk": "medium", "group": "third_party"},
    "terminal_app": {"cmd": "WindowsTerminal", "label": "Windows Terminal (app)", "risk": "medium", "group": "native"},
    "discord": {"cmd": "Discord", "label": "Discord", "risk": "medium", "group": "third_party"},
    "slack": {"cmd": "slack", "label": "Slack", "risk": "medium", "group": "third_party"},
    "spotify": {"cmd": "spotify", "label": "Spotify", "risk": "low", "group": "third_party"},
    "notion": {"cmd": "notion", "label": "Notion", "risk": "medium", "group": "third_party"},
    "obsidian": {"cmd": "obsidian", "label": "Obsidian", "risk": "medium", "group": "third_party"},
    "zoom": {"cmd": "Zoom", "label": "Zoom", "risk": "medium", "group": "third_party"},
    "telegram": {"cmd": "Telegram", "label": "Telegram", "risk": "medium", "group": "third_party"},
    "steam": {"cmd": "steam", "label": "Steam", "risk": "low", "group": "third_party"},
    "docker": {"cmd": "Docker Desktop", "label": "Docker Desktop", "risk": "medium", "group": "third_party"},
    "postman": {"cmd": "Postman", "label": "Postman", "risk": "medium", "group": "third_party"},
    "figma": {"cmd": "Figma", "label": "Figma", "risk": "medium", "group": "third_party"},
    "chatgpt": {"cmd": "ChatGPT", "label": "ChatGPT app", "risk": "medium", "group": "third_party"},
    "claude_app": {"cmd": "Claude", "label": "Claude Desktop", "risk": "medium", "group": "third_party"},
    "grok_app": {"cmd": "Grok", "label": "Grok app", "risk": "medium", "group": "third_party"},
    "perplexity": {"cmd": "Perplexity", "label": "Perplexity", "risk": "medium", "group": "third_party"},
    "github": {"cmd": "GitHubDesktop", "label": "GitHub Desktop", "risk": "medium", "group": "third_party"},
    "obs": {"cmd": "obs64", "label": "OBS Studio", "risk": "low", "group": "third_party"},
    "vlc": {"cmd": "vlc", "label": "VLC Media Player", "risk": "low", "group": "third_party"},
    "notepadpp": {"cmd": "notepad++", "label": "Notepad++", "risk": "low", "group": "third_party"},
    "tradingview": {"cmd": "TradingView", "label": "TradingView Desktop", "risk": "medium", "group": "third_party"},
    "metatrader": {"cmd": "terminal64.exe", "label": "MetaTrader 5", "risk": "medium", "group": "third_party"},
    "mt5": {"cmd": "terminal64.exe", "label": "MetaTrader 5", "risk": "medium", "group": "third_party"},
}

BLOCKED_URL_RE = re.compile(
    r"(file://|javascript:|data:|localhost:\d+.*(admin|secret)|169\.254\.|metadata\.google)",
    re.I,
)

# Shell substrings already blocked in executor — mirrored for policy docs
SHELL_BLOCK = (
    "format c:",
    "rm -rf /",
    "del /s /q c:\\",
    "shutdown",
    "mkfs",
    "rd /s /q c:\\",
    "reg delete",
    "net user",
)


def audit(event: str, **meta: Any) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    rec = {"at": time.time(), "event": event, **meta}
    with _lock:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, default=str) + "\n")


def allow_app(app_id: str) -> Tuple[bool, str, Optional[Dict[str, str]]]:
    key = (app_id or "").strip().lower()
    # aliases
    aliases = {
        "msedge": "edge",
        "microsoftedge": "edge",
        "copilotai": "copilot",
        "windows-copilot": "copilot",
        "vscode": "code",
        "vs-code": "code",
        "ppt": "powerpoint",
        "powerpnt": "powerpoint",
        "winword": "word",
        "ms-teams": "teams",
        "microsoft-teams": "teams",
        "claude": "claude_app",
        "chatgpt-app": "chatgpt",
        "github-desktop": "github",
        "npp": "notepadpp",
        "notepad++": "notepadpp",
        "screen-clip": "screenclip",
        "screenshot-tool": "screenclip",
        "agy": "antigravity",
    }
    key = aliases.get(key, key)
    if key not in ALLOWED_APPS:
        audit("app_denied", app=key)
        return (
            False,
            f"App '{key}' not on allowlist. Allowed: {', '.join(sorted(ALLOWED_APPS))}",
            None,
        )
    return True, "ok", ALLOWED_APPS[key]


def allow_url(url: str) -> Tuple[bool, str]:
    u = (url or "").strip()
    if not u.startswith("http://") and not u.startswith("https://"):
        return False, "Only http/https URLs allowed"
    if BLOCKED_URL_RE.search(u):
        audit("url_denied", url=u[:200])
        return False, "URL blocked by safety policy"
    if len(u) > 2000:
        return False, "URL too long"
    return True, "ok"


def allow_shell(cmd: str) -> Tuple[bool, str]:
    low = (cmd or "").lower()
    for b in SHELL_BLOCK:
        if b in low:
            audit("shell_denied", cmd=cmd[:200])
            return False, f"Blocked pattern: {b}"
    return True, "ok"


def policy_summary() -> Dict[str, Any]:
    apps = [
        {"id": k, "label": v["label"], "risk": v["risk"], "group": v.get("group", "native")}
        for k, v in ALLOWED_APPS.items()
    ]
    return {
        "auth_required": True,
        "apps_allowlist": apps,
        "apps_count": len(apps),
        "native_count": sum(1 for a in apps if a["group"] == "native"),
        "third_party_count": sum(1 for a in apps if a["group"] == "third_party"),
        "web": "http/https only; no file/javascript; size-capped fetch",
        "shell_blocklist": list(SHELL_BLOCK),
        "nexus": "Worker tools billed as NEXUS credits; drafts never auto-publish",
        "audit_log": str(LOG),
        "note": "Authenticated users still run powerful tools they approve. Safety is allowlist + auth + metering + audit.",
    }
