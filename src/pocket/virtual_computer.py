"""POCKET Virtual Computer — Caster / Open-Computer-Use class host machine for agents.

Not a cloud sandbox by default: a **clean operator machine surface** agents own:

  · workspace FS (home for the virtual computer)
  · multi-terminals (PowerShell / cmd / WSL) — same as Caster-class desktops
  · shell exec (one-shot)
  · full fusion perception (200+ symbols) every step
  · act: click symbols, open apps, type, orchestrator skills
  · long missions that chain for hours (finish → next prompt)

Inspired by: E2B Open Computer Use (observe/act loop), Bytebot (self-hosted desktop),
Hermes+CUA (terminals + screen). POCKET difference: host-grounded UIA fusion + SPECULUM.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "vcomp"
WS = ROOT / "workspace"
MISSIONS = ROOT / "missions"
LOGS = ROOT / "logs"
for d in (ROOT, WS, MISSIONS, LOGS):
    d.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()
_state: Dict[str, Any] = {
    "id": None,
    "status": "off",
    "created_at": None,
    "terminals": [],
    "steps": [],
    "last_sense": None,
}


def status() -> Dict[str, Any]:
    try:
        from pocket.terminals import list_terminals

        terms = list_terminals()
    except Exception:
        terms = []
    return {
        "ok": True,
        "product": "POCKET Virtual Computer",
        "alpha": True,
        "state": {**_state, "steps": (_state.get("steps") or [])[-20:]},
        "workspace": str(WS),
        "terminals_live": terms,
        "api": {
            "open": "POST /v1/vcomp/open",
            "status": "GET /v1/vcomp",
            "sense": "POST /v1/vcomp/sense",
            "act": "POST /v1/vcomp/act",
            "shell": "POST /v1/vcomp/shell",
            "term": "POST /v1/vcomp/term",
            "mission": "POST /v1/vcomp/mission",
            "close": "POST /v1/vcomp/close",
        },
        "note": "Agents own this machine surface for multi-hour work; fusion symbols on every sense.",
    }


def open_computer(*, label: str = "main") -> Dict[str, Any]:
    """Boot the virtual computer: workspace + default terminal + perception warm."""
    with _lock:
        if _state.get("status") == "on" and _state.get("id"):
            return {"ok": True, "already": True, **status()}
        vid = f"vc-{uuid.uuid4().hex[:10]}"
        _state.update(
            {
                "id": vid,
                "status": "on",
                "label": label,
                "created_at": time.time(),
                "steps": [],
                "terminals": [],
            }
        )
    # default terminal in workspace
    from pocket.terminals import create_terminal

    t = create_terminal(kind="powershell", cwd=str(WS), session_id=vid)
    with _lock:
        _state["terminals"].append(t.get("id") or t.get("terminal_id"))
    # warm fusion
    try:
        from pocket.perception import sense

        s = sense(max_ui=300, force=True)
        with _lock:
            _state["last_sense"] = s.get("brief")
    except Exception as e:
        with _lock:
            _state["last_sense"] = f"sense error: {e}"

    # marker file
    (WS / "README_VCOMP.md").write_text(
        f"# POCKET Virtual Computer `{vid}`\n\n"
        f"Workspace for long-running agents. Opened {time.strftime('%Y-%m-%d %H:%M:%S')}.\n"
        f"Sense via fusion page render. Terminals under ~/.pocket/terminals.\n",
        encoding="utf-8",
    )
    emit("vcomp", f"Virtual computer ON {vid}", agent="ARCHON", role="host")
    return {"ok": True, "message": f"Virtual computer online ({label})", **status()}


def close_computer() -> Dict[str, Any]:
    with _lock:
        _state["status"] = "off"
        _state["id"] = None
    emit("vcomp", "Virtual computer OFF", agent="ARCHON", role="host")
    return {"ok": True, "status": "off"}


def _log_step(kind: str, payload: Dict[str, Any]) -> None:
    rec = {"at": time.time(), "kind": kind, **payload}
    with _lock:
        steps = _state.setdefault("steps", [])
        steps.append(rec)
        if len(steps) > 500:
            del steps[:250]
    try:
        p = LOGS / f"step_{int(time.time())}_{kind}.json"
        p.write_text(json.dumps(rec, indent=2, default=str)[:100000], encoding="utf-8")
    except Exception:
        pass


def sense_computer(*, max_ui: int = 500) -> Dict[str, Any]:
    from pocket.perception import sense, agent_context

    page = sense(max_ui=max_ui, force=True)
    ctx = agent_context(max_ui=max_ui)
    with _lock:
        _state["last_sense"] = page.get("brief")
    _log_step("sense", {"brief": page.get("brief"), "counts": page.get("counts")})
    return {
        "ok": True,
        "vcomp": _state.get("id"),
        "brief": page.get("brief"),
        "counts": page.get("counts"),
        "context": ctx,
        "page_text_head": (page.get("page_text") or "")[:2000],
        "symbols": (page.get("symbols") or [])[:80],
        "action_hints": page.get("action_hints"),
    }


def act(action: str, **params) -> Dict[str, Any]:
    """Unified act surface — always fusion-aware where possible."""
    action = (action or "").lower().strip()
    emit("vcomp", f"act {action}", agent="PORTARIUS", role="host")
    result: Dict[str, Any] = {"ok": False, "action": action}

    if action in ("click", "click_name", "click_symbol"):
        from pocket.sanity import guard_click

        name = params.get("name") or params.get("query") or params.get("text") or ""
        min_score = float(params.get("min_score") or 0.65)
        result = guard_click(name, min_score=min_score)
    elif action in ("click_xy", "xy"):
        from pocket.vision_core import click_xy

        result = click_xy(int(params.get("x") or 0), int(params.get("y") or 0))
    elif action in ("type", "type_text"):
        from pocket.ui_maneuver import type_text

        result = type_text(params.get("text") or params.get("prompt") or "")
    elif action in ("open_app", "app"):
        from pocket.desktop import open_app

        result = open_app(params.get("app") or params.get("name") or "notepad")
    elif action in ("open_url", "url", "edge"):
        url = params.get("url") or params.get("prompt") or "https://github.com"
        try:
            from pocket.browser_mode import open_edge_url

            result = open_edge_url(url)
        except Exception:
            try:
                from pocket.desktop import open_edge_signed

                result = open_edge_signed(url)
            except Exception:
                import subprocess as _sp

                _sp.Popen(["cmd", "/c", "start", "", url], shell=False)
                result = {"ok": True, "url": url, "method": "start"}
    elif action in ("scroll", "scroll_down", "scroll_up"):
        from pocket.ui_click import scroll_page

        direction = params.get("direction") or ("up" if "up" in action else "down")
        result = scroll_page(times=int(params.get("n") or 3), direction=direction)
    elif action in ("skill", "orch"):
        from pocket.orchestrator import get_orchestrator

        result = get_orchestrator().execute(
            params.get("skill") or params.get("id") or "screenshot",
            prompt=params.get("prompt") or "",
            params=params.get("params") or {},
        )
    elif action in ("codex", "run_codex"):
        result = shell(
            params.get("command")
            or params.get("prompt")
            or "codex --version",
            timeout=int(params.get("timeout") or 120),
        )
    elif action == "sense":
        result = sense_computer(max_ui=int(params.get("max_ui") or 400))
    elif action == "remake":
        from pocket.fusion_remake import remake

        result = remake(refresh_page=True, max_ui=int(params.get("max_ui") or 400))
    elif action in ("studio", "viral"):
        from pocket.video_studio import auto_viral_pack

        result = auto_viral_pack(
            params.get("source") or "",
            title=params.get("title") or "POCKET",
            subtitle=params.get("subtitle") or "Virtual computer demo",
        )
    else:
        result = {"ok": False, "error": f"unknown action {action}", "known": [
            "click", "click_xy", "type", "open_app", "open_url", "scroll",
            "skill", "codex", "sense", "remake", "studio",
        ]}

    _log_step("act", {"action": action, "ok": result.get("ok"), "message": result.get("message") or result.get("brief")})
    # re-sense after act (fusion always in the loop)
    try:
        from pocket.perception import sense

        s = sense(max_ui=250, force=True, cache_sec=0)
        result["after_sense"] = s.get("brief")
        result["after_counts"] = s.get("counts")
    except Exception:
        pass
    return result


def shell(command: str, *, timeout: int = 60, allow_destructive: bool = False) -> Dict[str, Any]:
    """One-shot shell in virtual workspace (plus terminal-friendly)."""
    cmd = (command or "").strip()
    if not cmd:
        return {"ok": False, "error": "empty command"}
    from pocket.sanity import guard_shell

    g = guard_shell(cmd, allow_destructive=allow_destructive)
    if not g.get("ok"):
        return g
    t0 = time.time()
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            cwd=str(WS),
            capture_output=True,
            timeout=max(5, min(timeout, 600)),
        )
        out = (r.stdout or b"").decode("utf-8", errors="replace")
        err = (r.stderr or b"").decode("utf-8", errors="replace")
        rec = {
            "ok": r.returncode == 0,
            "returncode": r.returncode,
            "stdout": out[-8000:],
            "stderr": err[-4000:],
            "ms": int((time.time() - t0) * 1000),
            "cwd": str(WS),
            "command": cmd[:500],
        }
        _log_step("shell", rec)
        return rec
    except Exception as e:
        return {"ok": False, "error": str(e), "command": cmd[:200]}


def open_terminal(*, kind: str = "powershell") -> Dict[str, Any]:
    from pocket.terminals import create_terminal

    t = create_terminal(kind=kind, cwd=str(WS), session_id=_state.get("id") or "vcomp")
    with _lock:
        _state.setdefault("terminals", []).append(t.get("id"))
    return {"ok": True, "terminal": t}


def write_file(rel: str, content: str) -> Dict[str, Any]:
    p = (WS / rel).resolve()
    if not str(p).startswith(str(WS.resolve())):
        return {"ok": False, "error": "path escape"}
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    return {"ok": True, "path": str(p), "bytes": len(content.encode("utf-8"))}


def read_file(rel: str) -> Dict[str, Any]:
    p = (WS / rel).resolve()
    if not str(p).startswith(str(WS.resolve())):
        return {"ok": False, "error": "path escape"}
    if not p.is_file():
        return {"ok": False, "error": "not found"}
    return {"ok": True, "path": str(p), "text": p.read_text(encoding="utf-8", errors="replace")[:50000]}


def list_workspace() -> Dict[str, Any]:
    files = []
    for p in sorted(WS.rglob("*"))[:200]:
        if p.is_file():
            files.append({"path": str(p.relative_to(WS)), "bytes": p.stat().st_size})
    return {"ok": True, "workspace": str(WS), "files": files}
