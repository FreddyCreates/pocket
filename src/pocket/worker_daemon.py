"""Persistent Latin worker daemon — always-on, live-manipulable agents.

Background thread drains a command queue so ARCHON / API / desk can push jobs anytime.
State visible via GET /v1/workers/live.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket"
STATE = ROOT / "worker_daemon.json"

_lock = threading.Lock()
_queue: Deque[Dict[str, Any]] = deque()
_history: Deque[Dict[str, Any]] = deque(maxlen=100)
_worker_status: Dict[str, Dict[str, Any]] = {}
_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_started = False


def _init_status() -> None:
    from pocket.alpha_workers import WORKERS
    from pocket.skills_registry import skills_for

    for wid, meta in WORKERS.items():
        _worker_status[wid] = {
            "id": wid,
            "latin": meta.get("latin"),
            "class": meta.get("class"),
            "status": "idle",
            "last_job": None,
            "last_at": None,
            "skills": [s["id"] for s in skills_for(wid)],
            "runs": 0,
        }


def ensure_daemon() -> None:
    global _started, _thread
    with _lock:
        if _started and _thread and _thread.is_alive():
            return
        if not _worker_status:
            _init_status()
        _stop.clear()
        _thread = threading.Thread(target=_loop, name="pocket-latin-daemon", daemon=True)
        _thread.start()
        _started = True
        emit("daemon", "Latin worker daemon online", agent="ARCHON", role="host")


def enqueue(
    worker: str,
    skill_or_job: str,
    *,
    prompt: str = "",
    params: Optional[Dict] = None,
    priority: int = 5,
) -> Dict[str, Any]:
    ensure_daemon()
    cmd = {
        "id": f"wq-{uuid.uuid4().hex[:10]}",
        "worker": (worker or "ARCHON").upper(),
        "job": skill_or_job,
        "prompt": prompt,
        "params": params or {},
        "priority": priority,
        "queued_at": time.time(),
        "status": "queued",
    }
    with _lock:
        _queue.append(cmd)
        if cmd["worker"] in _worker_status:
            _worker_status[cmd["worker"]]["status"] = "queued"
    emit("daemon", f"Queued {cmd['worker']}.{cmd['job']}", agent=cmd["worker"], role="python")
    return cmd


def live_state() -> Dict[str, Any]:
    ensure_daemon()
    with _lock:
        return {
            "daemon": "running" if _started and _thread and _thread.is_alive() else "stopped",
            "queue_len": len(_queue),
            "workers": list(_worker_status.values()),
            "history": list(_history)[-20:],
        }


def _loop() -> None:
    while not _stop.is_set():
        cmd = None
        with _lock:
            if _queue:
                cmd = _queue.popleft()
        if not cmd:
            _stop.wait(0.25)
            continue
        wid = cmd["worker"]
        with _lock:
            if wid in _worker_status:
                _worker_status[wid]["status"] = "running"
                _worker_status[wid]["last_job"] = cmd["job"]
                _worker_status[wid]["last_at"] = time.time()
        try:
            from pocket.skill_runner import run_skill

            result, error, eng = run_skill(
                cmd["job"],
                prompt=cmd.get("prompt") or "",
                worker=wid,
                params=cmd.get("params") or {},
            )
            cmd["status"] = "done" if not error else "failed"
            cmd["result_preview"] = (result or "")[:1500]
            cmd["error"] = error
            cmd["engine"] = eng
        except Exception as e:
            cmd["status"] = "failed"
            cmd["error"] = str(e)
        cmd["finished_at"] = time.time()
        with _lock:
            _history.append(cmd)
            if wid in _worker_status:
                _worker_status[wid]["status"] = "idle"
                _worker_status[wid]["runs"] = int(_worker_status[wid].get("runs") or 0) + 1
            try:
                STATE.write_text(json.dumps(live_state(), indent=2, default=str)[:50000], encoding="utf-8")
            except Exception:
                pass
        emit(
            "daemon",
            f"{wid}.{cmd['job']} → {cmd['status']}",
            agent=wid,
            role="python",
            level="error" if cmd["status"] == "failed" else "info",
        )
