"""SPECULUM — screen recording for real demos (ffmpeg when available)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

_lock = Lock()
_proc: Optional[subprocess.Popen] = None
_out_path: Optional[Path] = None
_started_at: float = 0.0

# Keep recordings under .pocket so they are findable; also return path in result
REC_DIR = Path.home() / ".pocket" / "recordings"
REC_DIR.mkdir(parents=True, exist_ok=True)


def _ffmpeg() -> str:
    w = shutil.which("ffmpeg")
    if w:
        return w
    # winget common path from real verify
    root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if root.is_dir():
        for p in root.rglob("ffmpeg.exe"):
            return str(p)
    return ""


def record_status() -> Dict[str, Any]:
    alive = _proc is not None and _proc.poll() is None
    return {
        "ok": True,
        "recording": alive,
        "path": str(_out_path) if _out_path else None,
        "started_at": _started_at or None,
        "ffmpeg": bool(_ffmpeg()),
        "agent": "SPECULUM",
    }


def record_start(*, label: str = "demo") -> Dict[str, Any]:
    global _proc, _out_path, _started_at
    with _lock:
        if _proc is not None and _proc.poll() is None:
            return {"ok": True, "already": True, "path": str(_out_path), "message": "Already recording"}
        ff = _ffmpeg()
        if not ff:
            return {"ok": False, "error": "ffmpeg not found — install ffmpeg for SPECULUM recording"}
        ts = time.strftime("%Y%m%d-%H%M%S")
        _out_path = REC_DIR / f"pocket-{label}-{ts}.mp4"
        # gdigrab primary display
        cmd = [
            ff,
            "-y",
            "-f",
            "gdigrab",
            "-framerate",
            "12",
            "-i",
            "desktop",
            "-c:v",
            "libx264",
            "-preset",
            "ultrafast",
            "-pix_fmt",
            "yuv420p",
            "-an",
            str(_out_path),
        ]
        try:
            _proc = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _started_at = time.time()
            emit("record", f"SPECULUM recording started → {_out_path.name}", agent="SPECULUM", role="python")
            return {
                "ok": True,
                "path": str(_out_path),
                "pid": _proc.pid,
                "message": f"Recording desktop to {_out_path}",
                "agent": "SPECULUM",
            }
        except Exception as e:
            _proc = None
            return {"ok": False, "error": str(e)}


def record_stop() -> Dict[str, Any]:
    global _proc, _out_path, _started_at
    with _lock:
        if _proc is None:
            return {"ok": False, "error": "not recording"}
        try:
            if _proc.stdin:
                try:
                    _proc.stdin.write(b"q")
                    _proc.stdin.flush()
                except Exception:
                    pass
            try:
                _proc.wait(timeout=8)
            except Exception:
                _proc.terminate()
                try:
                    _proc.wait(timeout=3)
                except Exception:
                    _proc.kill()
            path = str(_out_path) if _out_path else ""
            dur = time.time() - _started_at if _started_at else 0
            size = Path(path).stat().st_size if path and Path(path).exists() else 0
            emit("record", f"SPECULUM stopped · {size} bytes · {dur:.1f}s", agent="SPECULUM", role="python")
            _proc = None
            return {
                "ok": True,
                "path": path,
                "bytes": size,
                "duration_sec": round(dur, 1),
                "message": f"Recording saved: {path} ({size} bytes)",
                "agent": "SPECULUM",
            }
        except Exception as e:
            _proc = None
            return {"ok": False, "error": str(e)}


def run_recorded_demo(plan: str) -> Dict[str, Any]:
    """Start record → run multi-step plan → stop record. Real demo capture."""
    from pocket.step_agent import run_step_agent

    start = record_start(label="archon-demo")
    if not start.get("ok") and not start.get("already"):
        # still run plan without record
        text, err, eng = run_step_agent(plan, max_steps=10)
        return {
            "ok": not bool(err),
            "recorded": False,
            "record_error": start.get("error"),
            "plan_result": text[:8000],
            "error": err,
            "message": "Demo ran without recording (ffmpeg issue)",
        }
    time.sleep(0.8)  # let encoder settle
    emit("demo", f"ARCHON demo plan: {plan[:120]}", agent="ARCHON", role="python")
    text, err, eng = run_step_agent(plan, max_steps=10)
    time.sleep(0.5)
    stop = record_stop()
    return {
        "ok": True,
        "recorded": stop.get("ok"),
        "recording_path": stop.get("path"),
        "recording_bytes": stop.get("bytes"),
        "duration_sec": stop.get("duration_sec"),
        "plan": plan,
        "plan_result": (text or "")[:10000],
        "plan_error": err,
        "engine": eng,
        "message": f"Demo complete. Video: {stop.get('path')} · watch Live actions for steps",
        "agents": ["ARCHON", "SPECULUM", "PORTARIUS", "OCULUS", "SCRUTATOR"],
    }
