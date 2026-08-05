"""Multi-agent / multi-terminal sessions — many Codex, shell, WSL, Claude at once."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket"
SESS_DIR = ROOT / "sessions"
USAGE_PATH = ROOT / "usage.json"
_lock = Lock()

SESS_DIR.mkdir(parents=True, exist_ok=True)

MODES = frozenset({
    "codex", "claude", "shell", "wsl", "ask", "plan", "grok", "handoff", "term",
    "desktop", "web", "nexus", "agent", "doer", "guppy", "browser",
    "capture", "repos", "copilot", "archon", "alpha", "workers",
    "woa", "wrapped-orch", "wrapped_orch",
    "offload", "embody", "embodiment", "realworld",
    "cowork", "work", "demo", "git", "forge", "sovereign-git", "ghost", "ghost-math", "math",
    # Novae hands — Grok/Codex instances in platform workspace
    "novae_grok", "novae_codex", "novae-grok", "novae-codex", "novae",
    "mesie", "auro", "auro14b",
    "wsl_native", "wsl-native", "linux",
    "build", "ship", "use_case", "emergent", "loop", "custom_agent",
    "dual", "cortex", "subcortex", "swarm", "work",
    "wiki", "infinite_wiki", "codebase",
    "dream", "duel", "capsule", "serendipity", "proof",
})


def _spath(sid: str) -> Path:
    return SESS_DIR / f"{sid}.json"


def _load_usage() -> Dict[str, Any]:
    if USAGE_PATH.exists():
        try:
            return json.loads(USAGE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "runs": 0,
        "codex_runs": 0,
        "claude_runs": 0,
        "shell_runs": 0,
        "wsl_runs": 0,
        "grok_runs": 0,
        "handoff_runs": 0,
        "est_tokens": 0,
        "llm_tokens": 0,
        "llm_tokens_by_engine": {},
        "by_day": {},
    }


def _save_usage(u: Dict[str, Any]) -> None:
    try:
        USAGE_PATH.write_text(json.dumps(u, indent=2), encoding="utf-8")
    except Exception:
        pass


def record_usage(mode: str, result_text: str = "") -> None:
    with _lock:
        u = _load_usage()
        u["runs"] = int(u.get("runs") or 0) + 1
        key = f"{mode}_runs"
        u[key] = int(u.get(key) or 0) + 1
        # rough token estimate ~4 chars/token for display
        est = max(1, len(result_text or "") // 4)
        u["est_tokens"] = int(u.get("est_tokens") or 0) + est
        day = time.strftime("%Y-%m-%d")
        by = u.setdefault("by_day", {})
        by[day] = int(by.get(day) or 0) + est
        # open session pressure
        u["sessions_seen"] = int(u.get("sessions_seen") or 0)
        _save_usage(u)
    # Embedded tokenomics burn (grok/handoff burn inside grok_bridge)
    if (mode or "").lower() not in ("grok", "handoff"):
        try:
            from pocket.tokenomics import burn, cost_for_mode

            burn(cost_for_mode(mode), meta={"mode": mode, "chars": len(result_text or "")})
        except Exception:
            pass
    # Parse real token counts from Codex/etc logs when present
    if result_text:
        try:
            import re

            for m in re.finditer(r"tokens used[:\s]*([0-9,]+)", result_text, re.I):
                record_llm_tokens(int(m.group(1).replace(",", "")), engine=mode or "unknown")
        except Exception:
            pass


def record_llm_tokens(n: int, engine: str = "unknown") -> None:
    """Accumulate real or estimated LLM tokens from agent runs."""
    if not n or n < 0:
        return
    with _lock:
        u = _load_usage()
        u["llm_tokens"] = int(u.get("llm_tokens") or 0) + int(n)
        by = u.setdefault("llm_tokens_by_engine", {})
        by[engine] = int(by.get(engine) or 0) + int(n)
        u["est_tokens"] = int(u.get("est_tokens") or 0) + int(n)
        day = time.strftime("%Y-%m-%d")
        bd = u.setdefault("by_day", {})
        bd[day] = int(bd.get(day) or 0) + int(n)
        _save_usage(u)


def get_usage() -> Dict[str, Any]:
    with _lock:
        return _load_usage()


def create_session(
    *,
    mode: str = "codex",
    title: str = "",
    workspace: str = "workspace",
    cwd: str = "",
    client_device: Optional[Dict[str, Any]] = None,
    owner: str = "",
) -> Dict[str, Any]:
    mode = (mode or "codex").lower()
    if mode not in MODES:
        mode = "codex"
    sid = f"s-{uuid.uuid4().hex[:10]}"
    titles = {
        "codex": "Codex agent",
        "claude": "Claude agent",
        "shell": "Shell terminal",
        "wsl": "WSL terminal",
        "ask": "Quick plan",
        "plan": "Planning AI chat",
        "grok": "Grok coding agent",
        "handoff": "Plan handoff",
        "term": "Live terminal",
        "desktop": "Desktop apps",
        "web": "Web research",
        "nexus": "NEXUS intelligence",
        "agent": "Headless doer (≤10 steps)",
        "doer": "Headless doer (≤10 steps)",
        "guppy": "GUPPY · local fish agent",
        "browser": "Browser · real world desk",
        "capture": "Capture · screenshot / snip",
        "repos": "Repos · GitHub",
        "copilot": "CONSILIARIUS · Copilot",
        "archon": "ARCHON · desk alpha",
        "alpha": "ARCHON · desk alpha",
        "workers": "Latin workers roster",
        "novae_grok": "Grok Novae · hands",
        "novae_codex": "Codex Novae · hands",
        "novae-grok": "Grok Novae · hands",
        "novae-codex": "Codex Novae · hands",
        "novae": "Grok Novae · hands",
        "offload": "Offload · real world",
        "mesie": "MESIE spectral",
        "auro": "Auro14B",
        "wsl": "WSL · native Linux hands",
        "wsl_native": "WSL · native Linux hands",
        "wsl-native": "WSL · native Linux hands",
        "linux": "WSL · native Linux hands",
        "build": "Build loop · multi-agent ship",
        "ship": "Build loop · multi-agent ship",
        "use_case": "Real use case runner",
        "emergent": "Emergent-parity ship factory",
        "loop": "Managed agent loop",
        "custom_agent": "Custom agent builder",
        "wiki": "Infinite Wiki · hierarchical code",
        "infinite_wiki": "Infinite Wiki · hierarchical code",
        "codebase": "Infinite Wiki · hierarchical code",
        "dream": "Dream Mode · idle consolidator",
        "duel": "Agent Duels · propose & judge",
        "capsule": "Time Capsules · future instructions",
        "serendipity": "Serendipity · unexpected links",
        "proof": "Proof chain · work receipts",
    }
    # Number parallel sessions of same mode so tabs stay distinct (Codex 1, Codex 2…)
    mode_n = 1
    try:
        own = (owner or "pocket").strip().lower()
        peers = [
            s
            for s in list_sessions(80, owner=own, admin=False)
            if s.get("mode") == mode and (s.get("owner") or "pocket").lower() == own
        ]
        mode_n = len(peers) + 1
    except Exception:
        mode_n = 1
    default_title = titles.get(mode) or "Session"
    if mode in (
        "codex", "claude", "grok", "term", "shell", "agent", "doer", "guppy",
        "browser", "capture", "repos", "copilot", "archon", "alpha", "workers",
    ) and not title:
        default_title = f"{titles.get(mode, mode)} · {mode_n}"

    sess = {
        "id": sid,
        "schema": "pocket.session.v2",
        "mode": mode,
        "title": (title or default_title)[:80],
        "workspace": workspace or "workspace",
        "cwd": cwd or "",
        "owner": (owner or "pocket").strip().lower() or "pocket",
        "status": "idle",  # idle | running | error
        "created_at": time.time(),
        "updated_at": time.time(),
        "messages": [],
        "job_ids": [],
        "pinned": False,
        "client_device": client_device or None,
        # Codex/Claude CLI thread id — ONE POCKET session tab = ONE engine conversation.
        # Follow-up messages resume; +Codex creates a new isolated thread.
        "engine_thread_id": "",
        "codex_session_id": "",
        "engine_thread_engine": "",
        "engine_resumes": 0,
        "slot": mode_n,
        "color": {
            "codex": "#2EE6A6",
            "claude": "#D4A574",
            "shell": "#5B8CFF",
            "wsl": "#A78BFA",
            "ask": "#F0B429",
            "plan": "#FBBF24",
            "grok": "#7DD3FC",
            "handoff": "#E8EEF7",
            "term": "#34D399",
            "desktop": "#F472B6",
            "web": "#38BDF8",
            "nexus": "#C084FC",
            "agent": "#FB7185",
            "doer": "#FB7185",
            "guppy": "#38BDF8",
            "browser": "#F97316",
            "capture": "#A3E635",
            "repos": "#94A3B8",
            "copilot": "#818CF8",
            "archon": "#F43F5E",
            "alpha": "#F43F5E",
            "workers": "#E11D48",
        }.get(mode, "#2EE6A6"),
    }
    # Live terminal binding for interactive PTY-like sessions
    if mode == "term":
        try:
            from pocket.terminals import create_terminal

            term = create_terminal(
                kind="powershell",
                workspace=workspace or "workspace",
                session_id=sid,
            )
            sess["terminal_id"] = term.get("id")
            sess["terminal_kind"] = term.get("kind")
        except Exception as e:
            sess["terminal_error"] = str(e)
    save(sess)
    try:
        from pocket.tokenomics import burn

        if mode != "term":  # terminal create already burns
            burn("session_open", meta={"session_id": sid, "mode": mode})
    except Exception:
        pass
    with _lock:
        u = _load_usage()
        u["sessions_seen"] = int(u.get("sessions_seen") or 0) + 1
        _save_usage(u)
    return sess


def save(sess: Dict[str, Any]) -> None:  # used by server term bind
    with _lock:
        sess["updated_at"] = time.time()
        _spath(sess["id"]).write_text(json.dumps(sess, indent=2), encoding="utf-8")


def get(sid: str) -> Optional[Dict[str, Any]]:
    p = _spath(sid)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_sessions(limit: int = 40, *, owner: str = "", admin: bool = False) -> List[Dict[str, Any]]:
    files = sorted(SESS_DIR.glob("s-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    own = (owner or "").strip().lower()
    for f in files:
        if len(out) >= limit:
            break
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not admin and own:
            so = (s.get("owner") or "pocket").lower()
            if so != own:
                continue
        out.append(s)
    return out


def session_visible(sess: Optional[Dict[str, Any]], *, owner: str = "", admin: bool = False) -> bool:
    if not sess:
        return False
    if admin:
        return True
    return (sess.get("owner") or "pocket").lower() == (owner or "").lower()


def delete_session(sid: str) -> bool:
    p = _spath(sid)
    if p.exists():
        p.unlink()
        return True
    return False


def add_user_message(sid: str, text: str) -> Optional[Dict[str, Any]]:
    sess = get(sid)
    if not sess:
        return None
    mid = f"m-{uuid.uuid4().hex[:10]}"
    msg = {
        "id": mid,
        "role": "user",
        "text": text[:20000],
        "at": time.time(),
        "status": "queued",
        "job_id": None,
        "result": "",
        "error": "",
        "engine": None,
    }
    sess["messages"].append(msg)
    sess["status"] = "running"
    save(sess)
    return msg


def bind_job(sid: str, mid: str, job_id: str) -> None:
    sess = get(sid)
    if not sess:
        return
    for m in sess["messages"]:
        if m.get("id") == mid:
            m["job_id"] = job_id
            m["status"] = "running"
            break
    if job_id not in sess.get("job_ids", []):
        sess.setdefault("job_ids", []).append(job_id)
    sess["status"] = "running"
    save(sess)


def patch_message_stream(
    sid: str,
    mid: str,
    *,
    result: str = "",
    engine: str = "",
    stream_tokens: int = 0,
) -> None:
    """Partial update while job is running (streaming logs + tokens)."""
    sess = get(sid)
    if not sess:
        return
    for m in sess["messages"]:
        if m.get("id") == mid:
            m["status"] = "running"
            m["result"] = (result or "")[-50000:]
            m["stream_tokens"] = stream_tokens
            m["stream_updated_at"] = time.time()
            if engine:
                m["engine"] = engine
            break
    sess["status"] = "running"
    save(sess)


def complete_message(
    sid: str,
    mid: str,
    *,
    result: str = "",
    error: str = "",
    engine: str = "",
    status: str = "done",
) -> None:
    sess = get(sid)
    if not sess:
        return
    mode = sess.get("mode") or "codex"
    for m in sess["messages"]:
        if m.get("id") == mid:
            m["status"] = status
            m["result"] = (result or "")[:80000]
            m["error"] = (error or "")[:8000]
            m["engine"] = engine
            m["finished_at"] = time.time()
            break
    # session idle if no running messages
    if any(m.get("status") in ("queued", "running") for m in sess["messages"]):
        sess["status"] = "running"
    else:
        sess["status"] = "error" if error and status == "failed" else "idle"
    save(sess)
    if result or error:
        record_usage(mode, result or error)


def rename(sid: str, title: str) -> Optional[Dict[str, Any]]:
    sess = get(sid)
    if not sess:
        return None
    sess["title"] = (title or sess["title"])[:80]
    save(sess)
    return sess


def bind_engine_thread(
    sid: str,
    thread_id: str,
    *,
    engine: str = "codex",
    resumed: bool = False,
) -> Optional[Dict[str, Any]]:
    """Bind a CLI conversation id to this POCKET session (resume on next message)."""
    sess = get(sid)
    if not sess or not thread_id:
        return sess
    tid = thread_id.strip()
    prev = (sess.get("engine_thread_id") or sess.get("codex_session_id") or "").strip()
    sess["engine_thread_id"] = tid
    if engine == "codex" or not sess.get("codex_session_id"):
        sess["codex_session_id"] = tid  # alias for older clients
    sess["engine_thread_engine"] = engine
    if resumed or (prev and prev == tid):
        sess["engine_resumes"] = int(sess.get("engine_resumes") or 0) + 1
    save(sess)
    return sess


def clear_engine_thread(sid: str) -> Optional[Dict[str, Any]]:
    """Drop bound CLI thread (next message starts a fresh engine conversation)."""
    sess = get(sid)
    if not sess:
        return None
    sess["engine_thread_id"] = ""
    sess["codex_session_id"] = ""
    sess["engine_thread_engine"] = ""
    save(sess)
    return sess
