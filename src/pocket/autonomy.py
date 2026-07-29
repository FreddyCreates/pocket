"""Autonomous scheduled Python workers — daily/hourly fetch without LLM tokens.

Stores schedules under ~/.pocket/schedules.json
Background thread polls and runs desktop/web/lookup jobs via step_agent.
Results land in ~/.pocket/autonomy_inbox/ and GROK_INBOX style markdown.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path.home() / ".pocket"
SCHED_PATH = ROOT / "schedules.json"
INBOX = ROOT / "autonomy_inbox"
_lock = threading.Lock()
_runner_started = False
_runner_thread: Optional[threading.Thread] = None
_stop = threading.Event()

INTERVALS = {
    "minute": 60,
    "hourly": 3600,
    "hour": 3600,
    "daily": 86400,
    "day": 86400,
    "every_6h": 21600,
    "weekly": 604800,
}


def _load() -> Dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    if SCHED_PATH.exists():
        try:
            return json.loads(SCHED_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"schedules": [], "runs": 0}


def _save(data: Dict[str, Any]) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    SCHED_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def list_schedules() -> List[Dict[str, Any]]:
    with _lock:
        return list(_load().get("schedules") or [])


def runner_status() -> str:
    return "running" if _runner_started and _runner_thread and _runner_thread.is_alive() else "stopped"


def create_schedule(
    *,
    prompt: str,
    interval: str = "daily",
    title: str = "",
    owner: str = "pocket",
) -> Dict[str, Any]:
    iv = (interval or "daily").lower().replace("-", "_")
    secs = INTERVALS.get(iv, INTERVALS["daily"])
    sid = f"sch-{uuid.uuid4().hex[:10]}"
    rec = {
        "id": sid,
        "title": (title or prompt[:60])[:80],
        "prompt": (prompt or "").strip()[:4000],
        "interval": iv,
        "interval_sec": secs,
        "owner": owner,
        "enabled": True,
        "created_at": time.time(),
        "next_run_at": time.time() + 5,  # first run soon
        "last_run_at": None,
        "last_status": "pending",
        "last_result_path": "",
        "run_count": 0,
        "engine": "guppy-python",
    }
    with _lock:
        data = _load()
        data.setdefault("schedules", []).append(rec)
        _save(data)
    ensure_runner()
    return rec


def cancel_schedule(sid: str) -> Dict[str, Any]:
    with _lock:
        data = _load()
        before = len(data.get("schedules") or [])
        data["schedules"] = [s for s in (data.get("schedules") or []) if s.get("id") != sid]
        _save(data)
        ok = len(data["schedules"]) < before
    return {"ok": ok, "id": sid}


def _write_result(sid: str, prompt: str, result: str, error: str) -> str:
    INBOX.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = INBOX / f"{sid}-{ts}.md"
    body = (
        f"# Autonomy run · {sid}\n\n"
        f"- at: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"- prompt: {prompt}\n"
        f"- error: {error or 'none'}\n\n"
        f"## Result\n\n{result}\n"
    )
    path.write_text(body, encoding="utf-8")
    # Append short note to project inbox if present
    try:
        inbox_md = Path(__file__).resolve().parents[2] / "GROK_INBOX.md"
        if inbox_md.exists() or True:
            with open(inbox_md, "a", encoding="utf-8") as f:
                f.write(f"\n\n## autonomy {sid} · {ts}\n\n{(result or error)[:2000]}\n")
    except Exception:
        pass
    return str(path)


def _execute_one(rec: Dict[str, Any]) -> None:
    prompt = rec.get("prompt") or ""
    try:
        from pocket.step_agent import run_step_agent

        result, error, engine = run_step_agent(prompt, max_steps=10)
    except Exception as e:
        result, error, engine = "", str(e), "autonomy"
    path = _write_result(rec["id"], prompt, result, error)
    with _lock:
        data = _load()
        for s in data.get("schedules") or []:
            if s.get("id") == rec["id"]:
                s["last_run_at"] = time.time()
                s["next_run_at"] = time.time() + int(s.get("interval_sec") or 86400)
                s["last_status"] = "failed" if error else "done"
                s["last_result_path"] = path
                s["run_count"] = int(s.get("run_count") or 0) + 1
                s["last_engine"] = engine
                break
        data["runs"] = int(data.get("runs") or 0) + 1
        _save(data)


def _loop() -> None:
    while not _stop.is_set():
        try:
            now = time.time()
            due = []
            with _lock:
                data = _load()
                for s in data.get("schedules") or []:
                    if not s.get("enabled", True):
                        continue
                    if float(s.get("next_run_at") or 0) <= now:
                        due.append(dict(s))
            for rec in due:
                _execute_one(rec)
        except Exception:
            pass
        _stop.wait(20)


def ensure_runner() -> None:
    global _runner_started, _runner_thread
    if _runner_started and _runner_thread and _runner_thread.is_alive():
        return
    _stop.clear()
    _runner_thread = threading.Thread(target=_loop, name="pocket-autonomy", daemon=True)
    _runner_thread.start()
    _runner_started = True


def handle_schedule_command(text: str) -> Tuple[str, str, str]:
    """Parse: schedule daily lookup … | schedule list | schedule cancel sch-…"""
    parts = (text or "").strip().split(None, 2)
    if len(parts) == 1 or (len(parts) >= 2 and parts[1].lower() in ("list", "ls", "status")):
        items = list_schedules()
        ensure_runner()
        lines = [
            "## Schedules (Python autonomy)",
            "",
            f"Runner: **{runner_status()}** · count: {len(items)}",
            "",
            "Create: `schedule daily lookup AI agent news`",
            "Cancel: `schedule cancel sch-…`",
            "",
        ]
        for s in items:
            lines.append(
                f"- `{s.get('id')}` · {s.get('interval')} · next={time.strftime('%Y-%m-%d %H:%M', time.localtime(s.get('next_run_at') or 0))} · "
                f"runs={s.get('run_count')} · {s.get('last_status')} · {s.get('title')}"
            )
        if not items:
            lines.append("_No schedules yet._")
        return "\n".join(lines), "", "autonomy"

    if len(parts) >= 2 and parts[1].lower() in ("cancel", "delete", "rm", "stop"):
        sid = parts[2].strip() if len(parts) > 2 else ""
        res = cancel_schedule(sid)
        return f"## Schedule cancel\n\n```json\n{json.dumps(res)}\n```", "" if res.get("ok") else "not found", "autonomy"

    # schedule <interval> <prompt>
    interval = "daily"
    prompt = text
    low = text.lower().strip()
    if low.startswith("schedule "):
        rest = text[9:].strip()
        bits = rest.split(None, 1)
        if bits and bits[0].lower().replace("-", "_") in INTERVALS:
            interval = bits[0].lower().replace("-", "_")
            prompt = bits[1] if len(bits) > 1 else "lookup daily brief"
        else:
            prompt = rest

    if not prompt:
        return "", "schedule needs a task prompt", "autonomy"

    rec = create_schedule(prompt=prompt, interval=interval)
    return (
        f"## Schedule created (GUPPY / Python worker)\n\n"
        f"**{rec['id']}** · interval=`{rec['interval']}` · first run in ~5s\n\n"
        f"Task: `{rec['prompt']}`\n\n"
        f"Results → `~/.pocket/autonomy_inbox/` and GROK_INBOX.md\n\n"
        f"This path does **not** burn LLM tokens — desktop open + Python web fetch only.\n",
        "",
        "autonomy",
    )
