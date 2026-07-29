"""Discrete REAL skills — one action each, callable anytime via API / ARCHON.

No multi-repo link spam. GitHub skill opens ONE page and uses the interface only.
"""

from __future__ import annotations

import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit
from pocket.ui_click import (
    close_foreground_window,
    maximize_foreground,
    scroll_page,
    click_named_element,
)
from pocket.ui_maneuver import focus_window_title, send_keys, set_clipboard
from pocket.screen_record import record_start, record_stop, record_status


def skill_record_start(label: str = "demo") -> Dict[str, Any]:
    """Start full-desktop record (SPECULUM / ffmpeg). User's external recorder optional."""
    return record_start(label=label)


def skill_record_stop() -> Dict[str, Any]:
    return record_stop()


def skill_github_one_page(repo: str = "") -> Dict[str, Any]:
    """Open exactly ONE GitHub repo in one Edge window. Scroll + click files on THAT page only.

    Does NOT open Issues/PRs as separate multi-window floods.
    Does NOT open 5 repos.
    """
    from pocket.repos import list_github_repos
    from pocket.browser_mode import open_edge_url

    emit("skill", "github_one_page REAL", agent="REPOSITOR", role="python")
    if not repo:
        listed = list_github_repos(1)
        r0 = (listed.get("repos") or [{}])[0]
        repo = r0.get("url") or "https://github.com/FreddyCreates/imagiEngine"
        name = r0.get("name") or "repo"
    else:
        name = repo.rstrip("/").split("/")[-1]

    url = repo if str(repo).startswith("http") else f"https://github.com/{repo}"
    # Single navigation
    open_edge_url(url, profile="Default", new_window=True)
    time.sleep(2.5)
    focus_window_title("GitHub")
    maximize_foreground()
    time.sleep(0.6)

    actions: List[Dict[str, Any]] = []
    # Read the page like a human
    actions.append({"act": "scroll_down", **scroll_page(4, direction="down")})
    time.sleep(0.5)
    actions.append({"act": "scroll_up", **scroll_page(1, direction="up")})
    time.sleep(0.4)
    # Try click a file in tree (common names) — same page
    for fname in ("README.md", "README", "package.json", "src", "docs", "LICENSE"):
        r = click_named_element(fname)
        actions.append({"act": "click_file", "name": fname, **r})
        if r.get("ok"):
            time.sleep(1.0)
            scroll_page(2, direction="down")
            time.sleep(0.4)
            # go back in same window (browser back) — not new link spam from us
            send_keys("%{LEFT}", settle_ms=400)  # Alt+Left
            time.sleep(0.8)
            break
    # more reading
    scroll_page(3, direction="down")
    time.sleep(0.4)
    scroll_page(2, direction="up")

    return {
        "ok": True,
        "skill": "github_one_page",
        "repo": url,
        "name": name,
        "actions": actions,
        "message": f"ONE GitHub page only: {url} — scrolled and used UI on that page",
    }


def skill_antigravity_explore() -> Dict[str, Any]:
    from pocket.desktop import open_app

    emit("skill", "antigravity_explore", agent="PORTARIUS", role="python")
    open_app("antigravity")
    time.sleep(2.8)
    focus_window_title("Antigravity")
    maximize_foreground()
    time.sleep(0.5)
    scroll_page(3, direction="down")
    time.sleep(0.6)
    scroll_page(1, direction="up")
    # leave open for a moment for recording, then soft close optional — keep open for video
    return {"ok": True, "skill": "antigravity_explore", "message": "Antigravity open, maximized, scrolled"}


def skill_github_desktop_peek() -> Dict[str, Any]:
    from pocket.desktop import open_app
    from pocket.ui_click import github_desktop_tour

    # reuse tour but don't force long exit if we want people to see
    r = github_desktop_tour()
    time.sleep(1.5)
    return {**r, "skill": "github_desktop_peek"}


def skill_email_hi_world() -> Dict[str, Any]:
    """Outlook/mailto draft — hi to the world (never Send). Maximize 2s."""
    from pocket.outlook_agent import create_draft

    body = (
        "Hi world,\n\n"
        "This is a live message from POCKET — Latin Python workers on a real Windows host "
        "(ItsNotAI Labs / Medina Tech Labs). We open apps, use real interfaces, and learn skills over time.\n\n"
        "Hello from the desk.\n\n"
        "— ARCHON / TABELLARIUS\n"
    )
    r = create_draft(subject="Hi world — from POCKET", body=body)
    time.sleep(1.2)
    focus_window_title("Mail")
    focus_window_title("Outlook")
    focus_window_title("Message")
    maximize_foreground()
    time.sleep(2.0)
    return {
        **r,
        "skill": "email_hi_world",
        "maximized": True,
        "message": "Draft email 'Hi world' open and maximized (not sent)",
    }


def skill_research_interest(repo_hint: str = "") -> Dict[str, Any]:
    """SCRUTATOR: what interests us about this repo (API/README — real fetch)."""
    from pocket.repos import analyze_github_repo

    target = repo_hint or "imagiEngine"
    r = analyze_github_repo(target, useful_for="POCKET host co-pilot — what interests us")
    interest = []
    for u in (r.get("useful_files") or [])[:8]:
        interest.append(f"{u.get('file')}: {', '.join(u.get('hits') or [])}")
    r["interest_summary"] = interest
    r["skill"] = "research_interest"
    return r


def run_skill_real(skill_id: str, **kwargs) -> Tuple[str, str, str]:
    sid = (skill_id or "").lower().replace("-", "_")
    mapping = {
        "record_start": lambda: skill_record_start(kwargs.get("label") or "pocket-demo"),
        "record_stop": skill_record_stop,
        "github_one_page": lambda: skill_github_one_page(kwargs.get("repo") or kwargs.get("prompt") or ""),
        "antigravity_explore": skill_antigravity_explore,
        "github_desktop_peek": skill_github_desktop_peek,
        "email_hi_world": skill_email_hi_world,
        "research_interest": lambda: skill_research_interest(kwargs.get("repo") or kwargs.get("prompt") or ""),
    }
    if sid not in mapping:
        return "", f"unknown real skill: {sid}", "skill"
    r = mapping[sid]()
    import json

    md = f"## Skill `{sid}`\n\n**{r.get('message') or ''}**\n\n```json\n{json.dumps(r, indent=2, default=str)[:5000]}\n```\n"
    return md, "" if r.get("ok", True) else r.get("error", "fail"), sid


def run_focused_demo() -> Dict[str, Any]:
    """Recorded focused demo: real discrete skills only.

    1 record_start
    2 github_one_page (ONE)
    3 research_interest
    4 antigravity_explore
    5 github_desktop_peek
    6 email_hi_world
    7 record_stop + learn
    """
    from pocket.learn import record_run
    from pocket.live_vision import ensure_vision

    ensure_vision(interval=1.0)
    log: List[Dict[str, Any]] = []
    t0 = time.time()

    def do(skill: str, **kw):
        emit("demo", f"▶ skill {skill}", agent="ARCHON", role="python")
        try:
            if skill == "record_start":
                r = skill_record_start(kw.get("label") or "focused-demo")
            elif skill == "record_stop":
                r = skill_record_stop()
            elif skill == "github_one_page":
                r = skill_github_one_page(kw.get("repo") or "")
            elif skill == "research_interest":
                r = skill_research_interest(kw.get("repo") or "")
            elif skill == "antigravity_explore":
                r = skill_antigravity_explore()
            elif skill == "github_desktop_peek":
                r = skill_github_desktop_peek()
            elif skill == "email_hi_world":
                r = skill_email_hi_world()
            else:
                r = {"ok": False, "error": skill}
            log.append({"skill": skill, "ok": bool(r.get("ok", True)), "detail": {k: r.get(k) for k in ("message", "repo", "path", "bytes") if k in r}})
            emit("demo", f"✓ {skill}", agent="ARCHON", role="python")
            return r
        except Exception as e:
            log.append({"skill": skill, "ok": False, "error": str(e)})
            emit("demo", f"✗ {skill}: {e}", agent="ARCHON", role="python", level="error")
            return {"ok": False, "error": str(e)}

    rec0 = do("record_start", label="focused-demo")
    time.sleep(1.0)
    gh = do("github_one_page")
    repo_name = (gh or {}).get("name") or ""
    do("research_interest", repo=repo_name)
    do("antigravity_explore")
    do("github_desktop_peek")
    do("email_hi_world")
    time.sleep(0.8)
    rec1 = do("record_stop")

    learned = record_run(
        name="focused_github_antigravity_desktop_email",
        steps=log,
        notes="Real discrete skills; one GitHub page UI; SPECULUM recording",
        worker="ARCHON",
    )

    ok_n = sum(1 for x in log if x.get("ok"))
    return {
        "ok": True,
        "demo": "focused_real_v1",
        "ok_steps": ok_n,
        "skills_run": len(log),
        "duration_sec": round(time.time() - t0, 1),
        "recording": rec1,
        "recording_start": rec0,
        "recording_path": (rec1 or {}).get("path"),
        "learned_skill": learned.get("id"),
        "log": log,
        "message": f"Focused real demo {ok_n}/{len(log)} · video={(rec1 or {}).get('path')}",
        "api": "Each step is a discrete skill — call anytime via POST /v1/skills/run",
    }
