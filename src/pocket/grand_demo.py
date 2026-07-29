"""Grand live demo — multi-worker skill choreography for recording.

Sequence designed for operator screen-record:
  SPECULUM may also record if ffmpeg free.
  1) Open top 5 GitHub repos
  2) On last repo: explore every tab + full SCRUTATOR research
  3) Tweet research + Outlook draft same body
  4) SpaceX.com
  5) Cursor, Antigravity, CONSILIARIUS Copilot chat paste+send
  6) Notepad hello world from Grokbuild and Pocket Agents
  7) Explorer + create file
  8) Calculator sum
  9) PowerShell command
  10) TradingView web + app + MetaTrader
  11) Close Edge only
"""

from __future__ import annotations

import time
from typing import Any, Dict, List

from pocket.live_events import emit


def run_grand_demo() -> Dict[str, Any]:
    from pocket.repos import list_github_repos, analyze_github_repo
    from pocket.skill_runner import (
        github_explore_all_tabs,
        notepad_type,
        explorer_create_file,
        calculator_sum,
        powershell_command,
        run_skill,
    )
    from pocket.browser_mode import open_edge_url, open_tweet_compose
    from pocket.screen_record import record_start, record_stop
    from pocket.ui_maneuver import close_edge_only

    log: List[Dict[str, Any]] = []
    t0 = time.time()

    def step(name: str, fn):
        emit("demo", f"▶ {name}", agent="ARCHON", role="python")
        try:
            r = fn()
            log.append({"step": name, "ok": bool(r.get("ok", True)), "detail": r})
            emit("demo", f"✓ {name}", agent="ARCHON", role="python")
            return r
        except Exception as e:
            log.append({"step": name, "ok": False, "error": str(e)})
            emit("demo", f"✗ {name}: {e}", agent="ARCHON", role="python", level="error")
            return {"ok": False, "error": str(e)}

    # Optional self-record (user also recording)
    rec = record_start(label="grand-demo")
    time.sleep(0.6)

    # 1) list + open 5 githubs
    listed = step("list_github", lambda: list_github_repos(5))
    repos = (listed or {}).get("repos") or []
    step("open_top5", lambda: run_skill("github_open_top5")[0] and {"ok": True})

    last = repos[-1] if repos else {"url": "https://github.com/FreddyCreates/neuroemergence-core", "name": "neuroemergence-core"}
    last_url = last.get("url") or f"https://github.com/{last.get('name')}"
    last_name = last.get("name") or "repo"

    # 2) explore all tabs on LAST github + research
    step("explore_tabs_last", lambda: github_explore_all_tabs(last_url))
    research = step("research_last", lambda: analyze_github_repo(last_name, useful_for="POCKET host co-pilot"))

    # Build research blurb for tweet + email
    recs = research.get("recommendations") or []
    files = research.get("useful_files") or []
    desc = research.get("description") or ""
    research_text = (
        f"POCKET research on {research.get('repo') or last_name}: {desc}. "
        f"Hits: {len(files)} useful files. "
        f"{'; '.join(recs[:3])}"
    )[:270]
    email_body = (
        f"POCKET / ARCHON research draft\n\n"
        f"Repo: {research.get('repo') or last_name}\n"
        f"URL: {research.get('url') or last_url}\n"
        f"Description: {desc}\n\n"
        f"Recommendations:\n- " + "\n- ".join(recs[:6]) + "\n\n"
        f"Useful files:\n"
        + "\n".join(f"- {u.get('file')} ({', '.join(u.get('hits') or [])})" for u in files[:12])
        + "\n\n— Latin workers: SCRUTATOR + REPOSITOR + ARCHON\n"
    )

    # 3) Tweet research + outlook
    step("tweet_research", lambda: open_tweet_compose(research_text, profile_url=""))
    time.sleep(0.8)
    step(
        "outlook_draft",
        lambda: run_skill(
            "outlook_draft_research",
            prompt=email_body,
            params={"subject": f"POCKET research: {last_name}"},
        )[0]
        and {"ok": True, "message": "outlook skill"},
    )
    # call outlook properly
    from pocket.outlook_agent import create_draft

    step("outlook_draft_com", lambda: create_draft(subject=f"POCKET research: {last_name}", body=email_body))

    # 4) SpaceX
    step("spacex", lambda: open_edge_url("https://www.spacex.com/"))

    # 5) Cursor, Antigravity, Copilot chat
    step("cursor", lambda: __import__("pocket.desktop", fromlist=["open_app"]).open_app("cursor"))
    time.sleep(0.5)
    step("antigravity", lambda: __import__("pocket.desktop", fromlist=["open_app"]).open_app("antigravity"))
    time.sleep(0.5)
    step(
        "copilot_chat",
        lambda: run_skill(
            "copilot_chat_send",
            prompt=(
                "Hello from CONSILIARIUS — POCKET Latin workers (ARCHON demo). "
                "We research GitHub, draft email, and control the host desk."
            ),
        )[0]
        and {"ok": True},
    )
    from pocket.copilot_agent import paste_and_send_copilot

    step(
        "copilot_paste_send",
        lambda: paste_and_send_copilot(
            "Hello from CONSILIARIUS / POCKET ARCHON live demo. Latin Python workers online."
        ),
    )

    # 6) Notepad hello
    step(
        "notepad",
        lambda: notepad_type("hello world from Grokbuild and Pocket Agents"),
    )

    # 7) Explorer file
    step(
        "explorer_file",
        lambda: explorer_create_file("pocket-archon-demo.txt", "Created by PORTARIUS during ARCHON grand demo.\n"),
    )

    # 8) Calculator
    step("calc", lambda: calculator_sum("12+34="))

    # 9) PowerShell
    step(
        "powershell",
        lambda: powershell_command("Write-Host 'POCKET PORTARIUS'; hostname; Get-Date"),
    )

    # 10) Close only Edge tabs (GitHub / SpaceX windows) before markets surfaces
    time.sleep(0.8)
    step("close_edge", lambda: close_edge_only())
    time.sleep(0.8)

    # 11) TradingView web (fresh Edge) + TradingView desktop app + MetaTrader 5
    step("tv_web", lambda: open_edge_url("https://www.tradingview.com/"))
    time.sleep(0.5)
    from pocket.ui_maneuver import shell_start_appuser

    step("tv_app", lambda: shell_start_appuser("TradingView.Desktop_n534cwy3pjxzj!TradingView.Desktop"))
    step("metatrader", lambda: run_skill("open_metatrader")[0] and {"ok": True})

    stop = record_stop()
    ok_n = sum(1 for x in log if x.get("ok"))
    return {
        "ok": True,
        "agent": "ARCHON",
        "skills_run": len(log),
        "ok_steps": ok_n,
        "duration_sec": round(time.time() - t0, 1),
        "research_tweet": research_text,
        "last_repo": last_url,
        "recording": stop,
        "self_record_start": rec,
        "log": [
            {"step": x["step"], "ok": x.get("ok"), "error": x.get("error"), "msg": (x.get("detail") or {}).get("message") if isinstance(x.get("detail"), dict) else None}
            for x in log
        ],
        "message": f"Grand demo complete · {ok_n}/{len(log)} steps · video={stop.get('path')}",
        "workers": [
            "ARCHON", "REPOSITOR", "SCRUTATOR", "NAVIGATOR", "TABELLARIUS",
            "PORTARIUS", "CONSILIARIUS", "SPECULUM",
        ],
    }
