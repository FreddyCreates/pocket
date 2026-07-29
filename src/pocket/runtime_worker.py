"""POCKET runtime worker — keep host alive with a ~873ms heartbeat.

This is the process Electron (and Launch-POCKET) should run, not a bare
`serve` that can hang on mesh bootstrap. Heartbeat is written every 873ms
to ~/.pocket/runtime_heartbeat.json so the UI/Electron can show "alive".
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

HEART_MS = int(os.environ.get("POCKET_HEART_MS") or "873")
HOST = os.environ.get("POCKET_HOST") or "127.0.0.1"
PORT = int(os.environ.get("POCKET_PORT") or "8787")
ROOT = Path(os.environ.get("POCKET_ROOT") or Path(__file__).resolve().parents[2])
STATE_DIR = Path.home() / ".pocket"
HEART_FILE = STATE_DIR / "runtime_heartbeat.json"
PID_FILE = STATE_DIR / "runtime_worker.pid"

_stop = threading.Event()
_serve_proc: Optional[subprocess.Popen] = None
_beats = 0
_started_at = time.time()


def _write_heart(extra: Optional[Dict[str, Any]] = None) -> None:
    global _beats
    _beats += 1
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": True,
        "ts": time.time(),
        "beat": _beats,
        "interval_ms": HEART_MS,
        "uptime_sec": round(time.time() - _started_at, 2),
        "host": HOST,
        "port": PORT,
        "serve_pid": _serve_proc.pid if _serve_proc and _serve_proc.poll() is None else None,
        "worker_pid": os.getpid(),
        "desk": f"http://{HOST}:{PORT}/desk",
        "landing": f"http://{HOST}:{PORT}/",
    }
    if extra:
        payload.update(extra)
    HEART_FILE.write_text(json.dumps(payload), encoding="utf-8")


def port_open(host: str = HOST, port: int = PORT) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.35):
            return True
    except Exception:
        return False


def _python() -> str:
    return sys.executable


def start_serve() -> None:
    global _serve_proc
    if _serve_proc and _serve_proc.poll() is None:
        return
    if port_open():
        return
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT / "src") + os.pathsep + env.get("PYTHONPATH", "")
    env["POCKET_AURO_TRAIN"] = env.get("POCKET_AURO_TRAIN") or "0"
    # Mesh hook async — never block first HTTP
    env["POCKET_MESH_HOOK_ASYNC"] = "1"
    creation = 0
    if sys.platform == "win32":
        creation = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    _serve_proc = subprocess.Popen(
        [_python(), "-u", "-m", "pocket", "serve", "--host", HOST, "--port", str(PORT)],
        cwd=str(ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation,
    )


def heartbeat_loop() -> None:
    while not _stop.is_set():
        try:
            alive = port_open()
            if not alive:
                start_serve()
            _write_heart({"port_open": alive or port_open()})
        except Exception as e:
            try:
                _write_heart({"ok": False, "error": str(e)[:200]})
            except Exception:
                pass
        _stop.wait(HEART_MS / 1000.0)


def run() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    print(f"[POCKET runtime] worker pid={os.getpid()} heart={HEART_MS}ms port={PORT}", flush=True)
    start_serve()
    t = threading.Thread(target=heartbeat_loop, name="pocket-heart-873", daemon=True)
    t.start()
    try:
        while not _stop.is_set():
            # Reap + restart serve if it died
            if _serve_proc is not None and _serve_proc.poll() is not None:
                print(f"[POCKET runtime] serve exited code={_serve_proc.returncode} — restart", flush=True)
                start_serve()
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        _stop.set()
        if _serve_proc and _serve_proc.poll() is None:
            try:
                _serve_proc.terminate()
            except Exception:
                pass
        print("[POCKET runtime] stopped", flush=True)


if __name__ == "__main__":
    run()
