"""Time Capsules — future-you leaves instructions for past-you's machine.

Capsules fire when conditions match:
  - after_sec / at_ts
  - file_changed: path
  - idle_sec
  - keyword in recent session prompts (best-effort)

Always-on checker runs with the host.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket" / "capsules"
ROOT.mkdir(parents=True, exist_ok=True)
STATE = ROOT / "capsules.json"

_lock = threading.Lock()
_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_started = False


def _load() -> Dict[str, Any]:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"capsules": []}


def _save(data: Dict[str, Any]) -> None:
    STATE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def list_capsules() -> List[Dict[str, Any]]:
    return list(_load().get("capsules") or [])


def create_capsule(
    message: str,
    *,
    after_sec: int = 0,
    at_ts: float = 0,
    file_changed: str = "",
    idle_sec: int = 0,
    keyword: str = "",
    action: str = "note",
    owner: str = "pocket",
) -> Dict[str, Any]:
    """
    action: note | dream | duel | build | wiki_reindex
    """
    cid = f"cap-{uuid.uuid4().hex[:10]}"
    now = time.time()
    fire_at = float(at_ts) if at_ts else (now + max(0, int(after_sec or 0)))
    rec = {
        "id": cid,
        "message": (message or "").strip()[:2000],
        "created_at": now,
        "fire_at": fire_at if (after_sec or at_ts) else 0,
        "file_changed": file_changed or "",
        "file_mtime": 0.0,
        "idle_sec": int(idle_sec or 0),
        "keyword": (keyword or "").strip().lower(),
        "action": (action or "note").lower(),
        "owner": owner,
        "status": "armed",
        "fired_at": 0,
        "result": "",
    }
    if rec["file_changed"]:
        p = Path(rec["file_changed"]).expanduser()
        if p.exists():
            rec["file_mtime"] = p.stat().st_mtime
    with _lock:
        data = _load()
        data.setdefault("capsules", []).append(rec)
        _save(data)
    ensure_running()
    return {"ok": True, **rec}


def cancel_capsule(cid: str) -> Dict[str, Any]:
    with _lock:
        data = _load()
        found = False
        for c in data.get("capsules") or []:
            if c.get("id") == cid and c.get("status") == "armed":
                c["status"] = "cancelled"
                found = True
        _save(data)
    return {"ok": found, "id": cid}


def status() -> Dict[str, Any]:
    caps = list_capsules()
    armed = [c for c in caps if c.get("status") == "armed"]
    return {
        "ok": True,
        "schema": "pocket.capsules.v1",
        "armed": len(armed),
        "total": len(caps),
        "running": _started and _thread is not None and _thread.is_alive(),
        "capsules": sorted(caps, key=lambda c: c.get("created_at") or 0, reverse=True)[:30],
    }


def ensure_running() -> Dict[str, Any]:
    global _started, _thread
    if _thread and _thread.is_alive():
        return status()
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="pocket-capsules", daemon=True)
    _thread.start()
    _started = True
    return status()


def _loop() -> None:
    while not _stop.is_set():
        try:
            tick()
        except Exception:
            pass
        for _ in range(15):
            if _stop.is_set():
                break
            time.sleep(1)


def tick() -> List[Dict[str, Any]]:
    fired = []
    now = time.time()
    with _lock:
        data = _load()
        caps = data.get("capsules") or []
        for c in caps:
            if c.get("status") != "armed":
                continue
            if _should_fire(c, now):
                result = _fire(c)
                c["status"] = "fired"
                c["fired_at"] = now
                c["result"] = result.get("summary") or result.get("error") or "fired"
                fired.append(c)
        _save(data)
    return fired


def _should_fire(c: Dict[str, Any], now: float) -> bool:
    if c.get("fire_at") and now >= float(c["fire_at"]):
        return True
    path = c.get("file_changed") or ""
    if path:
        p = Path(path).expanduser()
        if p.exists():
            try:
                mt = p.stat().st_mtime
                if mt > float(c.get("file_mtime") or 0) + 0.01:
                    return True
            except Exception:
                pass
    idle_need = int(c.get("idle_sec") or 0)
    if idle_need > 0:
        try:
            from pocket.dream_mode import _host_idle_sec

            if _host_idle_sec() >= idle_need:
                return True
        except Exception:
            pass
    kw = (c.get("keyword") or "").strip().lower()
    if kw:
        # scan recent session prompts
        sdir = Path.home() / ".pocket" / "sessions"
        if sdir.is_dir():
            try:
                files = sorted(sdir.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:8]
                for fp in files:
                    txt = fp.read_text(encoding="utf-8", errors="replace").lower()
                    if kw in txt and fp.stat().st_mtime > float(c.get("created_at") or 0):
                        return True
            except Exception:
                pass
    return False


def _fire(c: Dict[str, Any]) -> Dict[str, Any]:
    action = (c.get("action") or "note").lower()
    msg = c.get("message") or ""
    summary = f"capsule {c.get('id')}: {action}"
    try:
        if action == "dream":
            from pocket.dream_mode import dream_once

            r = dream_once(force=True)
            summary = f"dream {r.get('dream',{}).get('title')}"
        elif action == "duel":
            from pocket.agent_duels import duel

            r = duel(msg or "Resolve the open lab challenge")
            summary = f"duel winner={(r.get('verdict') or {}).get('winner')}"
        elif action == "build":
            from pocket.build_loop import start_loop

            r = start_loop(msg or "Capsule-triggered ship", owner=c.get("owner") or "capsule")
            summary = f"build {r.get('id')}"
        elif action == "wiki_reindex":
            from pocket.infinite_wiki import reindex_if_stale

            path = c.get("file_changed") or ""
            r = reindex_if_stale(path) if path else {"ok": True, "note": "no path"}
            summary = f"wiki reindex changed={r.get('changed')}"
        else:
            # note
            note = ROOT / f"{c.get('id')}-note.md"
            note.write_text(
                f"# Time Capsule\n\n{msg}\n\nFired at {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
                encoding="utf-8",
            )
            summary = f"note {note.name}"
        try:
            from pocket.proof_chain import mint_receipt

            mint_receipt("capsule", summary, meta={"id": c.get("id"), "action": action})
        except Exception:
            pass
        try:
            from pocket.live_events import emit

            emit("capsule", summary[:100], agent="CHRONOS", role="daemon")
        except Exception:
            pass
        return {"ok": True, "summary": summary}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
