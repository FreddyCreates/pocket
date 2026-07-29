"""POCKET mini brain + mini heart — always-alive organism state."""

from __future__ import annotations

import time
from typing import Any, Dict, List

_STARTED = time.time()
_BEATS = 0
_LAST_THOUGHT = ""
_LAST_THOUGHT_AT = 0.0


def _uptime() -> float:
    return time.time() - _STARTED


def heart(worker_alive: bool = True, sessions: int = 0, jobs_running: int = 0) -> Dict[str, Any]:
    """Mini heart — pulse of the desk."""
    global _BEATS
    _BEATS += 1
    # BPM metaphor: idle ~48, active scales with sessions/jobs
    bpm = 48 + min(80, sessions * 4 + jobs_running * 12)
    if not worker_alive:
        bpm = 20
    return {
        "name": "mini heart",
        "emoji": "❤️",
        "alive": worker_alive,
        "bpm": bpm,
        "beats": _BEATS,
        "uptime_sec": int(_uptime()),
        "uptime_human": _fmt_uptime(_uptime()),
        "status": "beating" if worker_alive else "weak",
        "note": "Keeps the desk warm. If heart stops, always-on watchdog restarts POCKET.",
    }


def brain(
    *,
    sessions: int = 0,
    deploys: int = 0,
    pock: int = 0,
    public: bool = False,
    codex: bool = False,
    grok: bool = False,
    recent_modes: Any = None,
) -> Dict[str, Any]:
    """Mini brain — light situational thoughts (not a full LLM)."""
    global _LAST_THOUGHT, _LAST_THOUGHT_AT
    thoughts: List[str] = []
    if not codex and not grok:
        thoughts.append("No coding CLIs on PATH — install Codex or Grok for heavy work.")
    elif codex and grok:
        thoughts.append("Codex + Grok ready. Spawn parallel agents; stream tokens while they run.")
    elif codex:
        thoughts.append("Codex ready. Open multi-session desk for real file work.")
    else:
        thoughts.append("Grok coding agent ready. Use plan handoff for deferred research.")

    if sessions == 0:
        thoughts.append("Quiet desk — open Live term or a Codex session.")
    elif sessions >= 5:
        thoughts.append(f"{sessions} sessions open — watch POCK burn on concurrent Codex/Grok.")
    else:
        thoughts.append(f"{sessions} session(s) active. Heart is warm.")

    if deploys:
        thoughts.append(f"{deploys} local deploy(s) live — check logs if anything looks stuck.")
    else:
        thoughts.append("No deploys yet — Static/npm/python when you're ready to ship local.")

    if not public:
        thoughts.append("Public tunnel: confirm CF Public Hostname → http://127.0.0.1:8787 and keep POCKET up.")
    else:
        thoughts.append("Public URL configured — far-away access needs heart (POCKET) + tunnel both alive.")

    if pock < 1000:
        thoughts.append(f"POCK low ({pock}) — mint topup or ease heavy agent loops.")
    else:
        thoughts.append(f"POCK balance {pock} — multi-agent spend is metered.")

    thought = thoughts[int(time.time() / 17) % len(thoughts)]
    _LAST_THOUGHT = thought
    _LAST_THOUGHT_AT = time.time()
    return {
        "name": "mini brain",
        "emoji": "🧠",
        "alive": True,
        "thought": thought,
        "thoughts": thoughts[:5],
        "focus": (recent_modes or ["desk"])[:6],
        "note": "Local cognition for the desk — not a replacement for Codex/Grok.",
    }


def snapshot(
    *,
    worker_alive: bool = True,
    sessions: int = 0,
    jobs_running: int = 0,
    deploys: int = 0,
    pock: int = 0,
    public: bool = False,
    codex: bool = False,
    grok: bool = False,
    modes: Any = None,
) -> Dict[str, Any]:
    h = heart(worker_alive, sessions, jobs_running)
    b = brain(
        sessions=sessions,
        deploys=deploys,
        pock=pock,
        public=public,
        codex=codex,
        grok=grok,
        recent_modes=modes,
    )
    return {
        "ok": True,
        "schema": "pocket.organism.v1",
        "product": "POCKET",
        "organism": "mini brain + mini heart",
        "always_on": True,
        "heart": h,
        "brain": b,
        "motto": "Brain plans. Heart stays on. Agents ship.",
    }


def _fmt_uptime(sec: float) -> str:
    s = int(sec)
    d, s = divmod(s, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if d:
        return f"{d}d {h}h {m}m"
    if h:
        return f"{h}h {m}m"
    return f"{m}m {s}s"
