"""Job store — real lifecycle: queued → running → done/failed. Session-aware."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket"
JOBS_DIR = ROOT / "jobs"
WORK_DIR = ROOT / "workspace"
INBOX_MD = Path(__file__).resolve().parents[2] / "GROK_INBOX.md"
_lock = Lock()

JOBS_DIR.mkdir(parents=True, exist_ok=True)
WORK_DIR.mkdir(parents=True, exist_ok=True)

VALID_MODES = frozenset({
    "codex", "claude", "shell", "ask", "plan", "wsl", "grok", "handoff", "term",
    "desktop", "web", "nexus", "agent", "doer", "guppy", "browser",
    "capture", "repos", "copilot", "archon", "alpha", "workers",
    "woa", "wrapped-orch", "wrapped_orch", "mesie", "auro",
    "offload", "embody", "embodiment", "realworld",
})


def _path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def reclaim_orphans() -> int:
    """Mark stuck running jobs as failed after process restart."""
    n = 0
    for f in JOBS_DIR.glob("job-*.json"):
        try:
            j = json.loads(f.read_text(encoding="utf-8"))
        except Exception:
            continue
        if j.get("status") == "running":
            j["status"] = "failed"
            j["error"] = (j.get("error") or "") + " [reclaimed: server restart]"
            j["finished_at"] = time.time()
            try:
                f.write_text(json.dumps(j, indent=2), encoding="utf-8")
                n += 1
            except Exception:
                pass
    return n


def create_job(
    prompt: str,
    *,
    name: str = "desk",
    mode: str = "codex",
    cwd: str = "",
    workspace: str = "",
    session_id: str = "",
    message_id: str = "",
    client_device: Optional[Dict[str, Any]] = None,
    owner: str = "",
) -> Dict[str, Any]:
    mode = (mode or "codex").lower()
    if mode not in VALID_MODES:
        mode = "codex"
    jid = f"job-{uuid.uuid4().hex[:12]}"
    # Attach engine thread so Codex/Grok resume the same conversation
    engine_thread_id = ""
    engine_thread_engine = ""
    if session_id:
        try:
            from pocket.sessions import get as get_sess

            s = get_sess(session_id) or {}
            engine_thread_id = (s.get("engine_thread_id") or s.get("codex_session_id") or "").strip()
            engine_thread_engine = (s.get("engine_thread_engine") or "").strip()
        except Exception:
            pass

    job = {
        "id": jid,
        "schema": "pocket.job.v4",
        "product": "POCKET",
        "from": (name or "desk")[:40],
        "mode": mode,
        "prompt": (prompt or "").strip()[:20000],
        "cwd": cwd or "",
        "workspace": workspace or "",
        "session_id": session_id or "",
        "message_id": message_id or "",
        "owner": (owner or "").strip().lower() or "",
        "client_device": client_device or None,
        "engine_thread_id": engine_thread_id,
        "engine_thread_engine": engine_thread_engine,
        "status": "queued",
        "created_at": time.time(),
        "started_at": None,
        "finished_at": None,
        "result": "",
        "error": "",
        "engine": None,
        "log_tail": "",
    }
    if not job["prompt"]:
        raise ValueError("prompt required")
    save(job)
    _refresh_inbox_md()
    return job


def save(job: Dict[str, Any]) -> None:
    with _lock:
        _path(job["id"]).write_text(json.dumps(job, indent=2), encoding="utf-8")


def get(job_id: str) -> Optional[Dict[str, Any]]:
    p = _path(job_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def list_jobs(limit: int = 30) -> List[Dict[str, Any]]:
    files = sorted(JOBS_DIR.glob("job-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for f in files[:limit]:
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


def next_queued() -> Optional[Dict[str, Any]]:
    queued = [j for j in list_jobs(120) if j.get("status") == "queued"]
    if not queued:
        return None
    queued.sort(key=lambda j: j.get("created_at") or 0)
    return queued[0]


def claim(job_id: str) -> Optional[Dict[str, Any]]:
    with _lock:
        job = get(job_id)
        if not job or job.get("status") != "queued":
            return None
        job["status"] = "running"
        job["started_at"] = time.time()
        _path(job_id).write_text(json.dumps(job, indent=2), encoding="utf-8")
        return job


def set_pid(job_id: str, pid: int) -> None:
    """Record OS process id so cancel can kill the agent process tree."""
    if not job_id or not pid:
        return
    job = get(job_id)
    if not job:
        return
    job["pid"] = int(pid)
    save(job)


def is_cancelled(job_id: str) -> bool:
    job = get(job_id) or {}
    return (job.get("status") or "") == "cancelled" or bool(job.get("cancel_requested"))


def _kill_pid(pid: int) -> bool:
    if not pid:
        return False
    import subprocess
    import sys

    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                timeout=15,
            )
        else:
            import os
            import signal

            os.kill(pid, signal.SIGTERM)
        return True
    except Exception:
        return False


def cancel_job(job_id: str, *, reason: str = "cancelled by user") -> Optional[Dict[str, Any]]:
    """
    Stop a queued/running job. Kills the process tree when pid is known.
    Marks session message cancelled so the transcript reorganizes.
    """
    job = get(job_id)
    if not job:
        return None
    st = (job.get("status") or "").lower()
    if st in ("done", "failed", "cancelled"):
        return job
    job["cancel_requested"] = True
    job["status"] = "cancelled"
    job["error"] = (reason or "cancelled")[:4000]
    prev = (job.get("result") or job.get("log_tail") or "")[:4000]
    job["result"] = (prev + f"\n\n[POCKET] {reason}\n").strip()[:80000]
    job["finished_at"] = time.time()
    pid = int(job.get("pid") or 0)
    if pid:
        _kill_pid(pid)
        job["killed_pid"] = pid
    save(job)

    sid = job.get("session_id") or ""
    mid = job.get("message_id") or ""
    if sid and mid:
        try:
            from pocket.sessions import complete_message

            complete_message(
                sid,
                mid,
                result=job.get("result") or "",
                error=job.get("error") or "",
                engine=job.get("engine") or job.get("mode") or "",
                status="cancelled",
            )
        except Exception as e:
            print(f"[jobs] cancel session update failed: {e}", flush=True)
    _refresh_inbox_md()
    return job


def cancel_session_jobs(session_id: str, *, reason: str = "superseded by new message") -> List[str]:
    """Cancel all queued/running jobs bound to a POCKET session tab."""
    if not session_id:
        return []
    cancelled: List[str] = []
    for j in list_jobs(80):
        if (j.get("session_id") or "") != session_id:
            continue
        if (j.get("status") or "") not in ("queued", "running"):
            continue
        cid = j.get("id") or ""
        if cancel_job(cid, reason=reason):
            cancelled.append(cid)
    return cancelled


def finish(job_id: str, *, result: str = "", error: str = "", engine: str = "") -> Dict[str, Any]:
    job = get(job_id) or {"id": job_id}
    # Do not overwrite an explicit cancel
    if (job.get("status") or "") == "cancelled":
        return job
    if result and not error:
        job["status"] = "done"
        job["result"] = result[:80000]
        job["error"] = ""
    elif result and error:
        job["status"] = "done"
        job["result"] = (result + "\n\n--- warning ---\n" + error)[:80000]
        job["error"] = error[:4000]
    else:
        job["status"] = "failed"
        job["result"] = result[:20000] if result else ""
        job["error"] = (error or "unknown failure")[:8000]
    job["finished_at"] = time.time()
    if engine:
        job["engine"] = engine
    save(job)

    # Wire back to multi-agent session transcript
    sid = job.get("session_id") or ""
    mid = job.get("message_id") or ""
    if sid and mid:
        try:
            from pocket.sessions import complete_message

            complete_message(
                sid,
                mid,
                result=job.get("result") or "",
                error=job.get("error") or "",
                engine=job.get("engine") or "",
                status=job.get("status") or "done",
            )
        except Exception as e:
            print(f"[jobs] session update failed: {e}", flush=True)

    # AI Workspace auto-update (token saver for next agent turn)
    try:
        from pocket.ai_workspace import touch_from_job

        touch_from_job(job)
    except Exception as e:
        print(f"[jobs] ai_workspace update failed: {e}", flush=True)

    _refresh_inbox_md()
    return job


def _refresh_inbox_md() -> None:
    jobs = list_jobs(12)
    lines = [
        "# POCKET job inbox — multi-agent console",
        "",
        f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "Desktop console runs many Codex/Claude/shell/WSL sessions in parallel.",
        "Grok: say **check pocket** or open GROK_INBOX.md — also create a Grok handoff session in the UI.",
        "",
    ]
    for j in jobs:
        lines.append(
            f"## {j.get('id')} · **{j.get('status')}** · {j.get('mode')} · session={j.get('session_id') or '—'}"
        )
        lines.append("")
        lines.append("### Prompt")
        lines.append("```")
        lines.append((j.get("prompt") or "")[:1500])
        lines.append("```")
        if j.get("result"):
            lines.append("### Result")
            lines.append("```")
            lines.append((j.get("result") or "")[:2500])
            lines.append("```")
        if j.get("error"):
            lines.append(f"### Error\n{j.get('error')[:800]}")
        lines.append("")
    try:
        INBOX_MD.write_text("\n".join(lines), encoding="utf-8")
    except Exception:
        pass
