"""Long-lived interactive terminals (PTY-like) — not one-shot shell jobs."""

from __future__ import annotations

import os
import subprocess
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.executor import resolve_cwd
from pocket.tokenomics import burn

ROOT = Path.home() / ".pocket" / "terminals"
ROOT.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()
_TERMS: Dict[str, "LiveTerminal"] = {}


class LiveTerminal:
    def __init__(
        self,
        tid: str,
        *,
        kind: str = "powershell",
        cwd: str = "",
        session_id: str = "",
    ):
        self.id = tid
        self.kind = kind  # powershell | cmd | wsl
        self.cwd = cwd
        self.session_id = session_id
        self.created_at = time.time()
        self.log_path = ROOT / f"{tid}.log"
        self._proc: Optional[subprocess.Popen] = None
        self._lock = threading.Lock()
        self._buffer = ""
        self.alive = False

    def start(self) -> None:
        if self.kind == "wsl":
            cmd = ["wsl", "-d", "Debian", "--", "bash", "-i"]
            # interactive bash may need script; use bash -l with stdin
            cmd = ["wsl", "-d", "Debian", "--", "bash", "-l"]
        elif self.kind == "cmd":
            cmd = ["cmd.exe", "/Q", "/K"]
        else:
            cmd = [
                "powershell.exe",
                "-NoLogo",
                "-NoExit",
                "-ExecutionPolicy",
                "Bypass",
            ]

        self.log_path.write_text(
            f"[POCKET terminal {self.id} kind={self.kind} cwd={self.cwd}]\n",
            encoding="utf-8",
        )
        self._proc = subprocess.Popen(
            cmd,
            cwd=self.cwd if self.cwd and Path(self.cwd).is_dir() else None,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            bufsize=0,
            env={**os.environ},
        )
        self.alive = True
        t = threading.Thread(target=self._reader, name=f"term-{self.id}", daemon=True)
        t.start()
        # warm prompt
        time.sleep(0.2)
        self.write("\n")

    def _reader(self) -> None:
        assert self._proc and self._proc.stdout
        while self._proc.poll() is None:
            try:
                data = self._proc.stdout.read(256)
            except Exception:
                break
            if not data:
                break
            text = data.decode("utf-8", errors="replace")
            with self._lock:
                self._buffer = (self._buffer + text)[-120000:]
            try:
                with open(self.log_path, "a", encoding="utf-8", errors="replace") as f:
                    f.write(text)
            except Exception:
                pass
        self.alive = False
        with self._lock:
            self._buffer += "\n[terminal exited]\n"

    def write(self, text: str) -> None:
        if not self._proc or not self._proc.stdin or self._proc.poll() is not None:
            raise RuntimeError("terminal not running")
        # Ensure newline so shell executes
        payload = text if text.endswith("\n") else text + "\n"
        self._proc.stdin.write(payload.encode("utf-8", errors="replace"))
        self._proc.stdin.flush()
        with self._lock:
            self._buffer = (self._buffer + f"\n$ {text.rstrip()}\n")[-120000:]
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"\n$ {text.rstrip()}\n")
        except Exception:
            pass

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            buf = self._buffer
        return {
            "id": self.id,
            "kind": self.kind,
            "cwd": self.cwd,
            "session_id": self.session_id,
            "alive": self.alive and self._proc is not None and self._proc.poll() is None,
            "pid": self._proc.pid if self._proc else None,
            "log_tail": buf[-40000:],
            "log_path": str(self.log_path),
            "created_at": self.created_at,
        }

    def stop(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._proc.wait(timeout=3)
            except Exception:
                try:
                    self._proc.kill()
                except Exception:
                    pass
        self.alive = False


def create_terminal(
    *,
    kind: str = "powershell",
    workspace: str = "workspace",
    cwd: str = "",
    session_id: str = "",
) -> Dict[str, Any]:
    kind = (kind or "powershell").lower()
    if kind not in ("powershell", "cmd", "wsl"):
        kind = "powershell"
    path = cwd or resolve_cwd({"workspace": workspace, "cwd": ""})
    tid = f"t-{uuid.uuid4().hex[:10]}"
    term = LiveTerminal(tid, kind=kind, cwd=path, session_id=session_id)
    term.start()
    with _lock:
        _TERMS[tid] = term
    burn("session_open", meta={"terminal": tid, "kind": kind})
    return term.snapshot()


def get_terminal(tid: str) -> Optional[Dict[str, Any]]:
    with _lock:
        t = _TERMS.get(tid)
    return t.snapshot() if t else None


def list_terminals() -> List[Dict[str, Any]]:
    with _lock:
        items = list(_TERMS.values())
    return [t.snapshot() for t in items]


def send_terminal(tid: str, command: str) -> Dict[str, Any]:
    with _lock:
        t = _TERMS.get(tid)
    if not t:
        return {"ok": False, "error": "terminal not found"}
    try:
        t.write(command)
        # brief wait for output
        time.sleep(0.25)
        burn("job_shell", meta={"terminal": tid, "interactive": True})
        return {"ok": True, **t.snapshot()}
    except Exception as e:
        return {"ok": False, "error": str(e), **t.snapshot()}


def stop_terminal(tid: str) -> Dict[str, Any]:
    with _lock:
        t = _TERMS.pop(tid, None)
    if not t:
        return {"ok": False, "error": "not found"}
    t.stop()
    return {"ok": True, "id": tid, "status": "stopped"}


def bind_session_terminal(session_id: str) -> Optional[str]:
    """Find terminal linked to a session."""
    with _lock:
        for t in _TERMS.values():
            if t.session_id == session_id:
                return t.id
    return None
