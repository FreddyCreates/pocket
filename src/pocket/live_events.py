"""Live action event bus — see host work happen in real time.

UI polls GET /v1/live/events. Every desktop/browser/github/capture step emits here.
"""

from __future__ import annotations

import time
import uuid
from collections import deque
from threading import Lock
from typing import Any, Deque, Dict, List, Optional

_lock = Lock()
_EVENTS: Deque[Dict[str, Any]] = deque(maxlen=400)
_SEQ = 0


def emit(
    kind: str,
    message: str,
    *,
    agent: str = "",
    role: str = "",  # python | llm | host | user
    level: str = "info",
    session_id: str = "",
    job_id: str = "",
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    global _SEQ
    with _lock:
        _SEQ += 1
        ev = {
            "id": f"ev-{uuid.uuid4().hex[:10]}",
            "seq": _SEQ,
            "at": time.time(),
            "ts": time.strftime("%H:%M:%S"),
            "kind": (kind or "action")[:40],
            "message": (message or "")[:500],
            "agent": (agent or "")[:40],
            "role": (role or "host")[:20],
            "level": level,
            "session_id": session_id or "",
            "job_id": job_id or "",
            "meta": meta or {},
        }
        _EVENTS.append(ev)
        return ev


def list_events(*, after_seq: int = 0, limit: int = 80) -> List[Dict[str, Any]]:
    with _lock:
        items = [e for e in _EVENTS if int(e.get("seq") or 0) > int(after_seq or 0)]
    return items[-limit:]


def snapshot() -> Dict[str, Any]:
    with _lock:
        last = list(_EVENTS)[-12:]
        seq = _SEQ
    return {
        "seq": seq,
        "count": len(_EVENTS),
        "recent": last,
        "note": "Poll GET /v1/live/events?after=<seq> for live host actions",
    }
