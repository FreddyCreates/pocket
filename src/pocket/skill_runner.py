"""Execute named skills — the live link between desk/API and Latin workers."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit
from pocket.ui_maneuver import (
    close_edge_only,
    focus_window_title,
    send_keys,
    set_clipboard,
    shell_start_appuser,
    type_text,
)


def run_skill(
    skill_id: str,
    *,
    prompt: str = "",
    worker: str = "",
    params: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str, str]:
    sid = (skill_id or "").strip().lower().replace("-", "_")
    params = params or {}
    emit("skill", f"Run skill {sid}", agent=worker or "SKILL", role="python")

    # Prefer discrete REAL skills first
    real_ids = {
        "record_start", "record_stop", "github_one_page", "antigravity_explore",
        "github_desktop_peek", "email_hi_world", "research_interest",
        "focused_demo", "interface_demo",
    }
    if sid in real_ids or sid.replace(" ", "_") in real_ids:
        from pocket.skills_real import run_skill_real, run_focused_demo

        if sid in ("focused_demo", "interface_demo", "demo", "grand_demo"):
            r = run_focused_demo()
            return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "archon"
        return run_skill_real(sid, prompt=prompt, **(params or {}))

    # --- routing ---
    if sid in ("grand_demo", "demo"):
        from pocket.skills_real import run_focused_demo

        r = run_focused_demo()
        return _md("focused_demo", r), "" if r.get("ok") else r.get("error", ""), "archon"

    if sid == "github_open_top5":
        from pocket.repos import open_github_repos

        r = open_github_repos(5)
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "repositor"

    if sid == "github_explore_tabs":
        url = params.get("url") or prompt
        r = github_explore_all_tabs(url)
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "repositor"

    if sid in ("github_research", "research_repo"):
        from pocket.repos import analyze_github_repo

        r = analyze_github_repo(prompt or params.get("repo") or "neuroemergence-core")
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "scrutator"

    if sid == "open_spacex":
        from pocket.browser_mode import open_edge_url

        r = open_edge_url("https://www.spacex.com/")
        return _md(sid, r), "" if r.get("ok") else "fail", "portarius"

    if sid == "open_tradingview_web":
        from pocket.browser_mode import open_edge_url

        r = open_edge_url("https://www.tradingview.com/")
        return _md(sid, r), "" if r.get("ok") else "fail", "portarius"

    if sid == "open_tradingview_app":
        r = shell_start_appuser("TradingView.Desktop_n534cwy3pjxzj!TradingView.Desktop")
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "portarius"

    if sid == "open_metatrader":
        exe = r"C:\Program Files\MetaTrader 5\terminal64.exe"
        if os.path.isfile(exe):
            subprocess.Popen([exe], shell=False)
            r = {"ok": True, "path": exe, "message": "MetaTrader 5 launched"}
        else:
            from pocket.desktop import open_app

            r = open_app("metatrader")
        return _md(sid, r), "" if r.get("ok") else "fail", "portarius"

    if sid == "open_cursor":
        from pocket.desktop import open_app

        r = open_app("cursor")
        return _md(sid, r), "" if r.get("ok") else "fail", "portarius"

    if sid == "open_antigravity":
        from pocket.desktop import open_app

        r = open_app("antigravity")
        return _md(sid, r), "" if r.get("ok") else "fail", "portarius"

    if sid == "copilot_chat_send":
        from pocket.copilot_agent import paste_and_send_copilot, introduce_to_copilot

        text = prompt or params.get("text") or "Hello from CONSILIARIUS / POCKET Latin workers."
        # Prefer full introduce path (opens + paste + enter into chat when possible)
        r = paste_and_send_copilot(text, already_open=False)
        # Also try Win+C then paste (Windows Copilot hotkey)
        time.sleep(0.5)
        send_keys("^{ESC}", settle_ms=200)  # no - use Win+C
        # Win key is %% on SendKeys? Actually ^ is ctrl. Win is ^{ESC} no.
        # SendKeys: Win = ^{ESC} wrong. Use shell:
        try:
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command",
                 "Add-Type -AssemblyName System.Windows.Forms; "
                 # Windows key + C
                 "$wshell = New-Object -ComObject wscript.shell; $wshell.SendKeys('^%{ }'); "
                 ],
                shell=False,
            )
        except Exception:
            pass
        # Use explorer ms-copilot and then paste again after focus
        time.sleep(1.0)
        focus_window_title("Copilot")
        set_clipboard(text)
        send_keys("^a", settle_ms=200)
        send_keys("^v", settle_ms=400)
        send_keys("{ENTER}", settle_ms=400)
        r["chat_attempt"] = "focus+selectall+paste+enter"
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "consiliarius"

    if sid == "tweet_research" or sid == "research_to_tweet":
        from pocket.browser_mode import open_tweet_compose

        text = prompt or params.get("text") or "POCKET research note"
        r = open_tweet_compose(text[:280])
        return _md(sid, r), "" if r.get("ok") else "fail", "navigator"

    if sid == "outlook_draft_research":
        from pocket.outlook_agent import create_draft

        r = create_draft(
            subject=params.get("subject") or "POCKET research draft",
            body=prompt or params.get("body") or "Research body",
        )
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "tabellarius"

    if sid == "notepad_hello":
        r = notepad_type(prompt or "hello world from Grokbuild and Pocket Agents")
        return _md(sid, r), "" if r.get("ok") else "fail", "portarius"

    if sid == "explorer_new_file":
        r = explorer_create_file(params.get("name") or "pocket-demo.txt", params.get("content") or "POCKET file")
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "portarius"

    if sid == "calc_run":
        r = calculator_sum(params.get("expr") or "12+34=")
        return _md(sid, r), "" if r.get("ok") else "fail", "portarius"

    if sid == "powershell_run":
        cmd = prompt or params.get("cmd") or "Write-Host 'POCKET PORTARIUS PowerShell OK'; Get-Date"
        r = powershell_command(cmd)
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "portarius"

    if sid == "close_edge":
        r = close_edge_only()
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "portarius"

    if sid == "screenshot":
        from pocket.capture import run_capture_job

        return run_capture_job("screenshot")

    if sid == "record_start":
        from pocket.screen_record import record_start

        r = record_start(label=params.get("label") or "skill")
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "speculum"

    if sid == "record_stop":
        from pocket.screen_record import record_stop

        r = record_stop()
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "speculum"

    if sid == "open_edge_url":
        from pocket.browser_mode import open_edge_url

        r = open_edge_url(prompt or params.get("url") or "https://example.com")
        return _md(sid, r), "" if r.get("ok") else "fail", "portarius"

    if sid == "open_app":
        from pocket.desktop import open_app

        r = open_app((prompt or params.get("app") or "notepad").split()[0])
        return _md(sid, r), "" if r.get("ok") else r.get("error", ""), "portarius"

    return "", f"unknown skill: {skill_id}", "skill"


def github_explore_all_tabs(repo_url: str) -> Dict[str, Any]:
    """Open every major GitHub project tab for a repo (interface navigation via URLs + focus)."""
    from pocket.browser_mode import open_edge_url

    url = (repo_url or "").strip().rstrip("/")
    if not url.startswith("http"):
        url = f"https://github.com/{url}"
    # strip tree/blob paths
    parts = url.replace("https://github.com/", "").split("/")
    if len(parts) >= 2:
        base = f"https://github.com/{parts[0]}/{parts[1]}"
    else:
        base = url

    tabs = [
        ("Code", base),
        ("Issues", base + "/issues"),
        ("Pull requests", base + "/pulls"),
        ("Actions", base + "/actions"),
        ("Projects", base + "/projects"),
        ("Security", base + "/security"),
        ("Insights", base + "/pulse"),
        ("Network", base + "/network"),
    ]
    opened = []
    for name, tab_url in tabs:
        emit("github", f"Explore tab: {name}", agent="REPOSITOR", role="python")
        opened.append({"tab": name, "url": tab_url, **open_edge_url(tab_url)})
        time.sleep(0.55)
        focus_window_title("GitHub")
        # Page-down scroll to "click through" feel
        send_keys("{PGDN}", settle_ms=200)
        time.sleep(0.25)
    return {
        "ok": True,
        "base": base,
        "tabs": opened,
        "count": len(opened),
        "message": f"Explored {len(opened)} GitHub tabs on {base}",
        "skill": "github_explore_tabs",
    }


def notepad_type(text: str) -> Dict[str, Any]:
    from pocket.desktop import open_app

    open_app("notepad")
    time.sleep(1.0)
    focus_window_title("Notepad")
    set_clipboard(text)
    send_keys("^v", settle_ms=400)
    return {"ok": True, "message": f"Notepad typed {len(text)} chars", "text": text[:200]}


def explorer_create_file(name: str, content: str) -> Dict[str, Any]:
    desk = Path_home_desktop()
    desk.mkdir(parents=True, exist_ok=True)
    path = desk / name
    path.write_text(content, encoding="utf-8")
    from pocket.desktop import open_app

    open_app("explorer", path=str(desk))
    # also select file
    subprocess.Popen(["explorer", "/select,", str(path)], shell=False)
    emit("file", f"Created {path}", agent="PORTARIUS", role="python")
    return {"ok": True, "path": str(path), "message": f"Created file {path}"}


def Path_home_desktop() -> Path:
    from pathlib import Path

    d = Path.home() / "Desktop"
    if not d.is_dir():
        d = Path.home() / "OneDrive" / "Desktop"
    if not d.is_dir():
        d = Path.home() / ".pocket" / "workspaces"
    return d


def calculator_sum(expr: str = "12+34=") -> Dict[str, Any]:
    from pocket.desktop import open_app

    open_app("calc")
    time.sleep(1.2)
    focus_window_title("Calculator")
    # Calculator accepts digit keys
    for ch in expr:
        if ch == "+":
            send_keys("{ADD}", settle_ms=80)
        elif ch == "-":
            send_keys("{SUBTRACT}", settle_ms=80)
        elif ch == "*":
            send_keys("{MULTIPLY}", settle_ms=80)
        elif ch == "/":
            send_keys("{DIVIDE}", settle_ms=80)
        elif ch == "=":
            send_keys("{ENTER}", settle_ms=80)
        elif ch.isdigit() or ch == ".":
            send_keys(ch, settle_ms=60)
        time.sleep(0.05)
    return {"ok": True, "expr": expr, "message": f"Calculator ran {expr}"}


def powershell_command(cmd: str) -> Dict[str, Any]:
    # Open visible PowerShell and run
    full = f"Write-Host '=== POCKET PORTARIUS ==='; {cmd}; Write-Host '=== done ==='; pause"
    subprocess.Popen(
        ["powershell", "-NoExit", "-NoProfile", "-Command", full],
        shell=False,
    )
    emit("shell", f"PowerShell: {cmd[:80]}", agent="PORTARIUS", role="python")
    return {"ok": True, "cmd": cmd, "message": "PowerShell window opened with command"}


def _md(sid: str, r: Dict[str, Any]) -> str:
    import json

    return f"## Skill `{sid}`\n\n**{r.get('message') or ''}**\n\n```json\n{json.dumps(r, indent=2, default=str)[:5000]}\n```\n"
