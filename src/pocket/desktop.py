"""Product desktop control — open allowlisted Windows apps for agents/users."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from typing import Any, Dict, List, Tuple

from pocket.safety import ALLOWED_APPS, allow_app, audit
from pocket.tokenomics import burn


def _local_appdata(*parts: str) -> str:
    return os.path.join(os.environ.get("LOCALAPPDATA", ""), *parts)


def _program_files(*parts: str) -> str:
    return os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"), *parts)


def _program_files_x86(*parts: str) -> str:
    return os.path.join(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)"), *parts)


def _resolve_cmd(app_id: str, cmd: str) -> Tuple[str, bool]:
    """Resolve allowlisted app to a real executable / protocol when possible."""
    app_id = (app_id or "").strip().lower()

    # Protocol handlers (ms-*, bingmaps:, etc.) — launch via start
    if ":" in cmd and not cmd.lower().endswith(".exe"):
        return cmd, True

    which = shutil.which(cmd)
    if which:
        return which, True
    # also try .exe
    which2 = shutil.which(cmd if cmd.lower().endswith(".exe") else f"{cmd}.exe")
    if which2:
        return which2, True

    if os.name != "nt":
        return cmd, False

    candidates: List[str] = {
        "edge": [
            _program_files_x86("Microsoft", "Edge", "Application", "msedge.exe"),
            _program_files("Microsoft", "Edge", "Application", "msedge.exe"),
        ],
        "chrome": [
            _program_files("Google", "Chrome", "Application", "chrome.exe"),
            _program_files_x86("Google", "Chrome", "Application", "chrome.exe"),
            _local_appdata("Google", "Chrome", "Application", "chrome.exe"),
        ],
        "firefox": [
            _program_files("Mozilla Firefox", "firefox.exe"),
            _program_files_x86("Mozilla Firefox", "firefox.exe"),
        ],
        "brave": [
            _local_appdata("BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
            _program_files("BraveSoftware", "Brave-Browser", "Application", "brave.exe"),
        ],
        "word": [
            _program_files("Microsoft Office", "root", "Office16", "WINWORD.EXE"),
            _program_files_x86("Microsoft Office", "root", "Office16", "WINWORD.EXE"),
        ],
        "excel": [
            _program_files("Microsoft Office", "root", "Office16", "EXCEL.EXE"),
            _program_files_x86("Microsoft Office", "root", "Office16", "EXCEL.EXE"),
        ],
        "powerpoint": [
            _program_files("Microsoft Office", "root", "Office16", "POWERPNT.EXE"),
            _program_files_x86("Microsoft Office", "root", "Office16", "POWERPNT.EXE"),
        ],
        "outlook": [
            _program_files("Microsoft Office", "root", "Office16", "OUTLOOK.EXE"),
            _program_files_x86("Microsoft Office", "root", "Office16", "OUTLOOK.EXE"),
        ],
        "onenote": [
            _program_files("Microsoft Office", "root", "Office16", "ONENOTE.EXE"),
            _program_files_x86("Microsoft Office", "root", "Office16", "ONENOTE.EXE"),
        ],
        "teams": [
            _local_appdata("Microsoft", "WindowsApps", "ms-teams.exe"),
            _local_appdata("Microsoft", "Teams", "current", "Teams.exe"),
            _program_files("WindowsApps", "MSTeams_8wekyb3d8bbwe", "ms-teams.exe"),
        ],
        "code": [
            _local_appdata("Programs", "Microsoft VS Code", "Code.exe"),
            _program_files("Microsoft VS Code", "Code.exe"),
        ],
        "cursor": [
            _local_appdata("Programs", "cursor", "Cursor.exe"),
            _local_appdata("Programs", "Cursor", "Cursor.exe"),
        ],
        "windsurf": [
            _local_appdata("Programs", "Windsurf", "Windsurf.exe"),
            _local_appdata("Programs", "windsurf", "Windsurf.exe"),
        ],
        "antigravity": [
            _local_appdata("Programs", "Antigravity", "Antigravity.exe"),
            _local_appdata("Programs", "antigravity", "Antigravity.exe"),
        ],
        "discord": [
            _local_appdata("Discord", "Update.exe"),
            _local_appdata("Discord", "app-1.0.0", "Discord.exe"),
        ],
        "slack": [
            _local_appdata("slack", "slack.exe"),
            _program_files("Slack", "slack.exe"),
        ],
        "spotify": [
            _program_files("WindowsApps", "SpotifyAB.SpotifyMusic_zpdnekdrzrea0", "Spotify.exe"),
            _local_appdata("Microsoft", "WindowsApps", "Spotify.exe"),
            os.path.join(os.environ.get("APPDATA", ""), "Spotify", "Spotify.exe"),
        ],
        "notion": [
            _local_appdata("Programs", "Notion", "Notion.exe"),
        ],
        "obsidian": [
            _local_appdata("Obsidian", "Obsidian.exe"),
            _local_appdata("Programs", "Obsidian", "Obsidian.exe"),
        ],
        "zoom": [
            _program_files("Zoom", "bin", "Zoom.exe"),
            _local_appdata("Zoom", "bin", "Zoom.exe"),
        ],
        "telegram": [
            _local_appdata("Telegram Desktop", "Telegram.exe"),
            _program_files("Telegram Desktop", "Telegram.exe"),
        ],
        "steam": [
            _program_files("Steam", "steam.exe"),
            _program_files_x86("Steam", "steam.exe"),
        ],
        "docker": [
            _program_files("Docker", "Docker", "Docker Desktop.exe"),
            _local_appdata("Docker", "Docker Desktop.exe"),
        ],
        "postman": [
            _local_appdata("Postman", "Postman.exe"),
        ],
        "figma": [
            _local_appdata("Figma", "Figma.exe"),
            _local_appdata("Programs", "Figma", "Figma.exe"),
        ],
        "chatgpt": [
            _local_appdata("Programs", "ChatGPT", "ChatGPT.exe"),
            _local_appdata("ChatGPT", "ChatGPT.exe"),
        ],
        "claude_app": [
            _local_appdata("AnthropicClaude", "claude.exe"),
            _local_appdata("Programs", "Claude", "Claude.exe"),
            _local_appdata("Claude", "Claude.exe"),
        ],
        "grok_app": [
            _local_appdata("Programs", "Grok", "Grok.exe"),
            _local_appdata("Grok", "Grok.exe"),
        ],
        "perplexity": [
            _local_appdata("Programs", "Perplexity", "Perplexity.exe"),
            _local_appdata("Perplexity", "Perplexity.exe"),
        ],
        "github": [
            _local_appdata("GitHubDesktop", "GitHubDesktop.exe"),
            _program_files("GitHub, Inc", "GitHub Desktop", "GitHubDesktop.exe"),
        ],
        "obs": [
            _program_files("obs-studio", "bin", "64bit", "obs64.exe"),
            _program_files_x86("obs-studio", "bin", "64bit", "obs64.exe"),
        ],
        "vlc": [
            _program_files("VideoLAN", "VLC", "vlc.exe"),
            _program_files_x86("VideoLAN", "VLC", "vlc.exe"),
        ],
        "notepadpp": [
            _program_files("Notepad++", "notepad++.exe"),
            _program_files_x86("Notepad++", "notepad++.exe"),
        ],
        "metatrader": [
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        ],
        "mt5": [
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
        ],
        "clipchamp": [
            _local_appdata("Microsoft", "WindowsApps", "Clipchamp.Clipchamp_yxz26nhyzhsrt", "Clipchamp.exe"),
        ],
        "sticky": [
            _program_files("Windows NT", "Accessories", "StikyNot.exe"),
            r"C:\Windows\System32\StikyNot.exe",
        ],
    }.get(app_id, [])

    for p in candidates:
        if p and os.path.isfile(p):
            return p, True

    # Discord Update.exe needs --processStart
    if app_id == "discord":
        upd = _local_appdata("Discord", "Update.exe")
        if os.path.isfile(upd):
            return upd, True

    # Shell builtins / always present on Windows
    if app_id in (
        "notepad",
        "explorer",
        "calc",
        "paint",
        "cmd",
        "powershell",
        "snip",
        "taskmgr",
        "control",
        "wt",
    ):
        return cmd, True

    # Protocol-style even if listed without colon resolution
    if app_id in ("copilot", "settings", "store", "photos", "maps", "clock", "media"):
        proto = {
            "copilot": "ms-copilot:",
            "settings": "ms-settings:",
            "store": "ms-windows-store:",
            "photos": "ms-photos:",
            "maps": "bingmaps:",
            "clock": "ms-clock:",
            "media": "mswindowsmusic:",
        }.get(app_id, cmd)
        return proto, True

    return cmd, False


def list_apps() -> List[Dict[str, str]]:
    out = []
    for k, v in ALLOWED_APPS.items():
        resolved, available = _resolve_cmd(k, v["cmd"])
        out.append(
            {
                "id": k,
                "label": v["label"],
                "risk": v["risk"],
                "group": v.get("group", "native"),
                "resolved": resolved,
                "available": available,
            }
        )
    # natives first, then third-party; alphabetically within group
    out.sort(key=lambda a: (0 if a.get("group") == "native" else 1, a["id"]))
    return out


def open_edge_signed(url: str, *, profile: str = "Default") -> Dict[str, Any]:
    """Open Edge with user profile (signed-in X/Copilot/web). Used by Browser mode."""
    from pocket.browser_mode import open_edge_url

    return open_edge_url(url, profile=profile)


def open_app(app_id: str, *, args: str = "", path: str = "") -> Dict[str, Any]:
    ok, msg, meta = allow_app(app_id)
    if not ok or not meta:
        return {"ok": False, "error": msg}

    app_key = app_id.strip().lower()
    # normalize aliases already done in allow_app via key lookup — re-resolve id
    from pocket.safety import ALLOWED_APPS as _AA

    # allow_app may have aliased; find matching meta in map
    real_id = app_key
    for k, v in _AA.items():
        if v is meta:
            real_id = k
            break

    cmd = meta["cmd"]
    resolved, available = _resolve_cmd(real_id, cmd)
    argv: List[str] = [resolved]
    steps_done = 1  # launch

    if path:
        p = os.path.abspath(os.path.expandvars(path.strip().strip('"')))
        home = os.path.expanduser("~")
        roots = [home, os.path.join(home, "OneDrive"), os.path.join(home, "Documents"), os.path.join(home, ".pocket")]
        if not any(p.lower().startswith(os.path.abspath(r).lower()) for r in roots if r):
            return {"ok": False, "error": "path must be under home/OneDrive/Documents/.pocket"}
        argv.append(p)
        steps_done = 2

    if args:
        # URL or simple tokens only
        for a in args.split():
            if any(c in a for c in "|&;<>`"):
                continue
            argv.append(a)
        if args.strip().startswith("http"):
            steps_done = 2  # Edge pattern: open browser + navigate URL

    try:
        if os.name == "nt":
            is_protocol = ":" in resolved and not resolved.lower().endswith(".exe") and "\\" not in resolved
            if real_id == "copilot":
                # Prefer dedicated Windows Copilot launcher (app, not web)
                try:
                    from pocket.browser_mode import open_windows_copilot

                    q = (args or "").strip()
                    cop = open_windows_copilot(query=q)
                    if cop.get("ok"):
                        audit("app_open", app="copilot", path="", args=q[:100])
                        try:
                            burn("desktop_open", meta={"app": "copilot"})
                        except Exception:
                            pass
                        return {
                            "ok": True,
                            "app": "copilot",
                            "label": meta["label"],
                            "risk": meta["risk"],
                            "group": meta.get("group", "native"),
                            "resolved": "ms-copilot:",
                            "argv": ["ms-copilot:"],
                            "steps": 1 + (1 if q else 0),
                            "available": True,
                            "at": time.time(),
                            "message": cop.get("message") or "Opened Windows Copilot",
                            "detail": cop,
                        }
                except Exception:
                    pass
            if is_protocol or real_id in ("copilot", "settings", "store", "photos", "maps", "clock", "media"):
                # Protocol / URI scheme launch
                subprocess.Popen(
                    ["cmd", "/c", "start", "", resolved],
                    cwd=os.path.expanduser("~"),
                    shell=False,
                )
            elif real_id == "discord" and resolved.lower().endswith("update.exe"):
                subprocess.Popen(
                    [resolved, "--processStart", "Discord.exe"],
                    cwd=os.path.expanduser("~"),
                    shell=False,
                )
            elif real_id == "edge" and (args or "").strip().startswith("http"):
                from pocket.browser_mode import open_edge_url

                er = open_edge_url((args or "").strip())
                if er.get("ok"):
                    audit("app_open", app="edge", path="", args=(args or "")[:100])
                    try:
                        burn("desktop_open", meta={"app": "edge", "signed": True})
                    except Exception:
                        pass
                    return {
                        "ok": True,
                        "app": "edge",
                        "label": meta["label"],
                        "risk": meta["risk"],
                        "group": meta.get("group", "native"),
                        "resolved": er.get("exe") or resolved,
                        "argv": er.get("argv") or argv,
                        "steps": 2,
                        "available": True,
                        "at": time.time(),
                        "message": er.get("message") or f"Opened Edge signed-in: {args[:60]}",
                        "detail": er,
                    }
                parts = ["cmd", "/c", "start", "", resolved]
                parts.extend(argv[1:])
                subprocess.Popen(parts, cwd=os.path.expanduser("~"), shell=False)
            elif real_id in (
                "chrome",
                "edge",
                "firefox",
                "brave",
                "code",
                "cursor",
                "windsurf",
                "wt",
                "chatgpt",
                "claude_app",
                "grok_app",
                "perplexity",
            ):
                parts = ["cmd", "/c", "start", "", resolved]
                parts.extend(argv[1:])
                subprocess.Popen(parts, cwd=os.path.expanduser("~"), shell=False)
            else:
                subprocess.Popen(argv, cwd=os.path.expanduser("~"), shell=False)
        else:
            subprocess.Popen(argv)

        audit("app_open", app=real_id, path=(path or "")[:200], args=(args or "")[:100])
        try:
            burn("desktop_open", meta={"app": real_id})
        except Exception:
            burn("job_shell", meta={"desktop": real_id})
        return {
            "ok": True,
            "app": real_id,
            "label": meta["label"],
            "risk": meta["risk"],
            "group": meta.get("group", "native"),
            "resolved": resolved,
            "argv": argv,
            "steps": steps_done,
            "available": available,
            "at": time.time(),
            "message": f"Opened {meta['label']}"
            + (f" (step 1: launch + step 2: {args[:60]})" if steps_done >= 2 and args else ""),
        }
    except FileNotFoundError:
        try:
            if os.name == "nt":
                subprocess.Popen(f'start "" "{cmd}"', shell=True)
                audit("app_open_shell_fallback", app=real_id)
                return {
                    "ok": True,
                    "app": real_id,
                    "label": meta["label"],
                    "message": f"Opened {meta['label']} (shell)",
                    "at": time.time(),
                    "steps": steps_done,
                }
        except Exception as e2:
            return {"ok": False, "error": str(e2)}
        return {"ok": False, "error": f"not found: {cmd}"}
    except Exception as e:
        audit("app_open_fail", app=real_id, error=str(e))
        return {"ok": False, "error": str(e)}


def run_desktop_job(prompt: str) -> Tuple[str, str, str]:
    text = (prompt or "").strip()
    low = text.lower()

    # Multi-step chain (up to 5) — silent doer style
    if any(x in low for x in (" then ", " next ", ";")) or "\n" in text:
        try:
            from pocket.step_agent import parse_steps, run_step_agent

            if len(parse_steps(text)) > 1:
                return run_step_agent(text)
        except Exception:
            pass

    if low in ("list", "list apps", "apps", "help", ""):
        apps = list_apps()
        native = [a for a in apps if a.get("group") == "native"]
        third = [a for a in apps if a.get("group") == "third_party"]
        lines = [
            "## Desktop control (product)",
            "",
            f"Open real Windows apps from this desk. Allowlist only — **{len(apps)} apps** "
            f"({len(native)} native + {len(third)} third-party).",
            "",
            "### Multi-step (up to 10, headless Python)",
            "- `open edge https://example.com then open notepad then open calc`",
            "- `lookup climate data` — open Bing/Copilot **and** bring Python search back",
            "- Edge with URL is already **2 steps** inside one open: launch + navigate",
            "- Use **+ Guppy** for commercial local fish agent + daily schedules",
            "",
            "### Native / Microsoft",
            "",
            "| id | app | risk | available |",
            "|----|-----|------|-----------|",
        ]
        for a in native:
            lines.append(f"| `{a['id']}` | {a['label']} | {a['risk']} | {a.get('available')} |")
        lines += [
            "",
            "### Third-party / AI",
            "",
            "| id | app | risk | available |",
            "|----|-----|------|-----------|",
        ]
        for a in third:
            lines.append(f"| `{a['id']}` | {a['label']} | {a['risk']} | {a.get('available')} |")
        lines += [
            "",
            "### Commands",
            "- `list apps`",
            "- `open notepad` · `open explorer` · `open copilot`",
            "- `open edge https://example.com`  _(2 steps: Edge + URL)_",
            "- `open code` · `open cursor` · `open chrome` · `open discord`",
            "- Multi-step: `open edge https://x.com then open calc then open snip`",
        ]
        return "\n".join(lines), "", "desktop"

    if low.startswith("open "):
        rest = text[5:].strip()
        parts = rest.split(None, 1)
        app = parts[0].lower().replace(".exe", "")
        extra = parts[1] if len(parts) > 1 else ""
        if extra.startswith("http://") or extra.startswith("https://"):
            if app not in ("chrome", "edge", "firefox", "brave"):
                app = "edge"
            res = open_app(app, args=extra)
        elif extra:
            res = open_app(app, path=extra.strip('"'))
        else:
            res = open_app(app)
        if res.get("ok"):
            return f"## Desktop\n\n**{res.get('message')}**\n\n```json\n{res}\n```", "", "desktop"
        return "", res.get("error") or "open failed", "desktop"

    return (
        "Unknown desktop command. Try `list apps`, `open copilot`, or "
        "`open edge https://example.com then open notepad`.",
        "unknown command",
        "desktop",
    )
