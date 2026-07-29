"""Interface-first live demo — one GitHub, real UI, no Edge massacre, no competing recorder.

Designed for operator's own screen recording.
"""

from __future__ import annotations

import subprocess
import time
from typing import Any, Dict, List

from pocket.live_events import emit
from pocket.live_vision import ensure_vision, latest_frame
from pocket.ui_click import (
    app_open_max_scroll_exit,
    close_foreground_window,
    github_desktop_tour,
    github_use_interface,
    maximize_foreground,
    scroll_page,
)
from pocket.ui_maneuver import focus_window_title, send_keys, set_clipboard


def run_interface_demo() -> Dict[str, Any]:
    """Single-repo UI tour + apps + markets. Does NOT kill Edge process. Does NOT start ffmpeg record."""
    from pocket.repos import list_github_repos, analyze_github_repo
    from pocket.browser_mode import open_edge_url, open_tweet_compose
    from pocket.desktop import open_app
    from pocket.outlook_agent import create_draft
    from pocket.copilot_agent import paste_and_send_copilot  # scaffold only light touch
    from pocket.skill_runner import notepad_type, explorer_create_file
    from pocket.ui_maneuver import shell_start_appuser

    ensure_vision(interval=1.0)
    log: List[Dict[str, Any]] = []
    t0 = time.time()

    def step(name: str, fn):
        emit("demo", f"▶ {name}", agent="ARCHON", role="python")
        try:
            r = fn()
            ok = bool(r.get("ok", True)) if isinstance(r, dict) else True
            log.append({"step": name, "ok": ok, "detail": r if isinstance(r, dict) else {"raw": str(r)[:200]}})
            emit("demo", f"{'✓' if ok else '✗'} {name}", agent="ARCHON", role="python")
            return r
        except Exception as e:
            log.append({"step": name, "ok": False, "error": str(e)})
            emit("demo", f"✗ {name}: {e}", agent="ARCHON", role="python", level="error")
            return {"ok": False, "error": str(e)}

    # 1) ONE github only — same window interface
    listed = step("list_one", lambda: list_github_repos(1))
    repos = (listed or {}).get("repos") or []
    one = repos[0] if repos else {"url": "https://github.com/FreddyCreates/imagiEngine", "name": "imagiEngine"}
    url = one.get("url") or f"https://github.com/FreddyCreates/{one.get('name')}"
    name = one.get("name") or "imagiEngine"

    ui = step("github_same_window_ui", lambda: github_use_interface(url))
    research = step("research_same_repo", lambda: analyze_github_repo(name, useful_for="POCKET"))

    recs = (research or {}).get("recommendations") or []
    desc = (research or {}).get("description") or ""
    tweet = (
        f"POCKET live UI tour of {name}: {desc}. "
        f"{'; '.join(recs[:2])}"
    )[:270]
    email = (
        f"POCKET interface demo research\n\nRepo: {name}\nURL: {url}\n\n"
        f"{desc}\n\nRecommendations:\n- " + "\n- ".join(recs[:5])
        + "\n\n— ARCHON / SCRUTATOR / REPOSITOR (same-window UI)\n"
    )

    # 2) GitHub Desktop tour + brain dump
    step("github_desktop", lambda: github_desktop_tour())
    time.sleep(0.6)
    step("github_desktop_exit", lambda: (focus_window_title("GitHub Desktop"), close_foreground_window()))

    # 3) Twitter/X (separate window OK)
    step("tweet", lambda: open_tweet_compose(tweet))
    time.sleep(1.2)

    # 4) Outlook draft → maximize → 2s → exit
    def outlook_flow():
        r = create_draft(subject=f"POCKET UI research: {name}", body=email)
        time.sleep(1.5)
        focus_window_title("Mail")
        focus_window_title("Outlook")
        focus_window_title("Message")
        maximize_foreground()
        time.sleep(2.0)
        close_foreground_window()
        return {**r, "maximized": True, "exited": True}

    step("outlook_draft_max_exit", outlook_flow)

    # 5) Cursor load → scroll → exit
    def cursor_flow():
        open_app("cursor")
        time.sleep(3.0)  # let load
        focus_window_title("Cursor")
        maximize_foreground()
        scroll_page(3, direction="down")
        time.sleep(1.0)
        close_foreground_window()
        return {"ok": True, "message": "Cursor load→scroll→exit"}

    step("cursor", cursor_flow)

    # 6) Antigravity same
    def ag_flow():
        open_app("antigravity")
        time.sleep(2.5)
        focus_window_title("Antigravity")
        maximize_foreground()
        scroll_page(2, direction="down")
        time.sleep(1.0)
        close_foreground_window()
        return {"ok": True, "message": "Antigravity load→scroll→exit"}

    step("antigravity", ag_flow)

    # 7) PowerShell — type codex and launch
    def ps_codex():
        subprocess.Popen(
            ["powershell", "-NoExit", "-NoProfile", "-Command",
             "Write-Host 'POCKET → launching codex'; codex"],
            shell=False,
        )
        time.sleep(2.0)
        focus_window_title("PowerShell")
        # If command didn't run as arg, type it
        set_clipboard("codex")
        send_keys("^v", settle_ms=300)
        send_keys("{ENTER}", settle_ms=400)
        return {"ok": True, "message": "PowerShell launched codex"}

    step("powershell_codex", ps_codex)

    # 8) TradingView WEB only — open and scroll through interface
    def tv_web():
        open_edge_url("https://www.tradingview.com/", new_window=True)
        time.sleep(2.5)
        focus_window_title("TradingView")
        focus_window_title("Edge")
        maximize_foreground()
        scroll_page(6, direction="down")
        time.sleep(0.5)
        scroll_page(2, direction="up")
        time.sleep(0.5)
        scroll_page(3, direction="down")
        return {"ok": True, "message": "TradingView.com scrolled as user"}

    step("tradingview_web_scroll", tv_web)

    # 9) MetaTrader — open, big, exit
    def mt5():
        exe = r"C:\Program Files\MetaTrader 5\terminal64.exe"
        subprocess.Popen([exe], shell=False)
        time.sleep(3.0)
        focus_window_title("MetaTrader")
        maximize_foreground()
        time.sleep(2.0)
        close_foreground_window()
        return {"ok": True, "message": "MetaTrader open→max→exit"}

    step("metatrader", mt5)

    # 10) Notepad hello (quick, stays or soft exit)
    step("notepad", lambda: notepad_type("hello world from Grokbuild and Pocket Agents"))

    # Light Copilot scaffold (not center of video)
    try:
        paste_and_send_copilot("POCKET CONSILIARIUS scaffold — interface demo complete.")
    except Exception:
        pass

    frame = latest_frame(include_image=False)
    ok_n = sum(1 for x in log if x.get("ok"))
    return {
        "ok": True,
        "agent": "ARCHON",
        "demo": "interface_v2",
        "skills_run": len(log),
        "ok_steps": ok_n,
        "duration_sec": round(time.time() - t0, 1),
        "repo": url,
        "tweet": tweet,
        "no_edge_kill": True,
        "no_ffmpeg_record": True,
        "vision": frame,
        "github_ui": ui,
        "log": [{"step": x["step"], "ok": x.get("ok"), "error": x.get("error")} for x in log],
        "message": f"Interface demo {ok_n}/{len(log)} · one GitHub UI · vision live · no Edge kill",
        "workers": ["ARCHON", "REPOSITOR", "SCRUTATOR", "PORTARIUS", "NAVIGATOR", "TABELLARIUS", "OCULUS"],
    }
