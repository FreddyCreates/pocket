"""Durable real-world task offload queue.

AIs post multi-step work here, release the chat turn, and pick up receipts later.
Stored under ~/.pocket/offload/ — survives restarts.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket" / "offload"
ROOT.mkdir(parents=True, exist_ok=True)
QPATH = ROOT / "queue.jsonl"
_lock = Lock()
_worker_started = False


def _read_all() -> List[Dict[str, Any]]:
    if not QPATH.exists():
        return []
    out: List[Dict[str, Any]] = []
    for ln in QPATH.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def _rewrite(items: List[Dict[str, Any]]) -> None:
    tmp = QPATH.with_suffix(".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for it in items[-200:]:
            f.write(json.dumps(it, default=str) + "\n")
    tmp.replace(QPATH)


def enqueue(
    goal: str,
    *,
    steps: Optional[List[Dict[str, Any]]] = None,
    agent: str = "AI",
    session_id: str = "",
    workspace: str = "parallax",
    priority: int = 5,
    kind: str = "embodiment",
) -> Dict[str, Any]:
    """Post work for background execution. Returns ticket immediately."""
    tid = f"off-{uuid.uuid4().hex[:12]}"
    task = {
        "id": tid,
        "schema": "pocket.offload.v1",
        "goal": (goal or "").strip()[:4000],
        "steps": steps
        or [
            {"action": "capability_snapshot"},
            {"action": "screenshot"},
            {"action": "note", "text": goal},
        ],
        "agent": (agent or "AI").upper()[:32],
        "session_id": session_id or "",
        "workspace": workspace or "parallax",
        "priority": int(priority),
        "kind": kind,
        "status": "queued",
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "result": "",
        "error": "",
        "proof": None,
        "log": [],
    }
    if not task["goal"]:
        return {"ok": False, "error": "goal required"}
    with _lock:
        items = _read_all()
        items.append(task)
        _rewrite(items)
    try:
        from pocket.mesh_disk import send_message

        send_message(
            task["agent"],
            "ARCHON",
            f"offload queued {tid}: {task['goal'][:160]}",
            channel="freq-coding",
            kind="offload",
        )
    except Exception:
        pass
    ensure_worker()
    return {"ok": True, "ticket": tid, "task": task, "message": f"Offloaded {tid} — chat turn free"}


def get_task(tid: str) -> Optional[Dict[str, Any]]:
    for t in _read_all():
        if t.get("id") == tid:
            return t
    return None


def list_tasks(*, status: str = "", limit: int = 40) -> List[Dict[str, Any]]:
    items = _read_all()
    if status:
        items = [t for t in items if t.get("status") == status]
    return list(reversed(items[-limit:]))


def _update(tid: str, **fields: Any) -> Optional[Dict[str, Any]]:
    with _lock:
        items = _read_all()
        out = None
        for t in items:
            if t.get("id") == tid:
                t.update(fields)
                out = t
        if out is not None:
            _rewrite(items)
        return out


def claim_next() -> Optional[Dict[str, Any]]:
    with _lock:
        items = _read_all()
        # priority then age
        queued = [t for t in items if t.get("status") == "queued"]
        if not queued:
            return None
        queued.sort(key=lambda t: (int(t.get("priority") or 5), float(t.get("created_at") or 0)))
        pick = queued[0]
        for t in items:
            if t.get("id") == pick["id"]:
                t["status"] = "running"
                t["started_at"] = time.time()
                pick = t
                break
        _rewrite(items)
        return pick


def run_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Execute embodiment steps for one offloaded task."""
    from pocket.embodiment import run_embodiment_plan

    tid = task["id"]
    try:
        result = run_embodiment_plan(
            task.get("goal") or "",
            steps=task.get("steps") or [],
            agent=task.get("agent") or "AI",
            workspace=task.get("workspace") or "parallax",
        )
        status = "done" if result.get("ok") else "failed"
        _update(
            tid,
            status=status,
            finished_at=time.time(),
            result=result.get("summary") or "",
            error=result.get("error") or "",
            proof=result.get("proof"),
            log=result.get("log") or [],
        )
        # skill memory
        if result.get("ok"):
            try:
                from pocket.learn import record_run

                record_run(
                    name=f"offload_{(task.get('goal') or '')[:40]}",
                    steps=result.get("log") or [],
                    notes=f"offload {tid}",
                    worker=task.get("agent") or "AI",
                )
            except Exception:
                pass
        try:
            from pocket.mesh_disk import leave_artifact, send_message

            leave_artifact(
                task.get("agent") or "AI",
                f"offload_{tid}_proof.md",
                result.get("proof_md") or result.get("summary") or "",
                notify=["ARCHON", "GROK", "CODEX"],
            )
            send_message(
                task.get("agent") or "AI",
                "ARCHON",
                f"offload {status} {tid}: {(task.get('goal') or '')[:120]}",
                channel="freq-coding",
                kind="receipt",
            )
        except Exception:
            pass
        return get_task(tid) or task
    except Exception as e:
        _update(tid, status="failed", finished_at=time.time(), error=str(e))
        return get_task(tid) or task


def process_one() -> bool:
    task = claim_next()
    if not task:
        return False
    run_task(task)
    return True


def _worker_loop() -> None:
    while True:
        try:
            if not process_one():
                time.sleep(1.2)
            else:
                time.sleep(0.2)
        except Exception:
            time.sleep(2.0)


def ensure_worker() -> None:
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    t = Thread(target=_worker_loop, name="pocket-offload", daemon=True)
    t.start()
