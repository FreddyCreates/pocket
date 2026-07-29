"""Live job streaming — partial logs + token estimates while agents run."""

from __future__ import annotations

import re
import time
from typing import Any, Dict, Optional

from pocket.jobs import get, save


def _parse_tokens(text: str) -> int:
    if not text:
        return 0
    total = 0
    for m in re.finditer(r"tokens used[:\s]*([0-9,]+)", text, re.I):
        try:
            total += int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    for m in re.finditer(r'"total_tokens"\s*:\s*(\d+)', text):
        try:
            total += int(m.group(1))
        except ValueError:
            pass
    return total


def estimate_tokens(text: str) -> int:
    """Prefer parsed counts; else ~4 chars/token on stream buffer."""
    parsed = _parse_tokens(text)
    if parsed:
        return parsed
    return max(0, len(text or "") // 4)


def update_progress(
    job_id: str,
    log_text: str,
    *,
    engine: str = "",
    force_tokens: Optional[int] = None,
) -> None:
    """Write streaming tail onto job + linked session message (running)."""
    job = get(job_id)
    if not job:
        return
    tail = (log_text or "")[-50000:]
    tokens = force_tokens if force_tokens is not None else estimate_tokens(tail)
    job["log_tail"] = tail
    job["stream_tokens"] = tokens
    job["stream_updated_at"] = time.time()
    if engine:
        job["engine"] = engine
    if job.get("status") == "queued":
        job["status"] = "running"
    save(job)

    sid = job.get("session_id") or ""
    mid = job.get("message_id") or ""
    if sid and mid:
        try:
            from pocket.sessions import patch_message_stream

            patch_message_stream(
                sid,
                mid,
                result=tail,
                engine=engine or job.get("engine") or "",
                stream_tokens=tokens,
            )
        except Exception:
            pass


def run_streaming(
    cmd,
    *,
    job_id: str = "",
    cwd: str = "",
    env: Optional[Dict[str, str]] = None,
    timeout: float = 900,
    engine: str = "",
    shell: bool = False,
    stdin_text: Optional[str] = None,
) -> tuple[str, int, str]:
    """
    Run process with streaming into job progress.
    Returns (combined_output, returncode, error_or_empty).
    If stdin_text is set, write it to the process stdin (Codex/Grok reliable prompts).
    """
    import os
    import subprocess
    import threading

    env_full = {**os.environ, **(env or {})}
    try:
        p = subprocess.Popen(
            cmd,
            cwd=cwd or None,
            env=env_full,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE if stdin_text is not None else subprocess.DEVNULL,
            bufsize=0,
            shell=shell,
        )
    except Exception as e:
        return "", 1, str(e)

    if job_id and p.pid:
        try:
            from pocket.jobs import set_pid

            set_pid(job_id, int(p.pid))
        except Exception:
            pass

    if stdin_text is not None and p.stdin is not None:
        try:
            data = stdin_text.encode("utf-8", errors="replace")
            # Write in chunks — large prompts + Windows pipes
            view = memoryview(data)
            step = 65536
            for i in range(0, len(view), step):
                p.stdin.write(view[i : i + step])
            try:
                p.stdin.flush()
            except Exception:
                pass
            p.stdin.close()
        except Exception:
            try:
                p.stdin.close()
            except Exception:
                pass

    chunks: list[bytes] = []
    lock = threading.Lock()
    done = threading.Event()
    cancelled = threading.Event()

    def reader():
        assert p.stdout is not None
        last_push = 0.0
        while True:
            try:
                data = p.stdout.read(256)
            except Exception:
                break
            if not data:
                break
            with lock:
                chunks.append(data)
            now = time.time()
            if job_id and (now - last_push > 0.35 or b"\n" in data):
                last_push = now
                try:
                    text = b"".join(chunks).decode("utf-8", errors="replace")
                    update_progress(job_id, text, engine=engine)
                except Exception:
                    pass
        done.set()

    def cancel_watch():
        """Poll job cancel flag; kill process tree so new prompts can take over."""
        if not job_id:
            return
        from pocket.jobs import is_cancelled, _kill_pid

        while not done.is_set() and not cancelled.is_set():
            try:
                if is_cancelled(job_id):
                    cancelled.set()
                    try:
                        _kill_pid(int(p.pid or 0))
                    except Exception:
                        pass
                    try:
                        p.kill()
                    except Exception:
                        pass
                    return
            except Exception:
                pass
            done.wait(0.35)

    t = threading.Thread(target=reader, name=f"stream-{job_id or 'x'}", daemon=True)
    t.start()
    cw = threading.Thread(target=cancel_watch, name=f"cancel-{job_id or 'x'}", daemon=True)
    cw.start()
    try:
        p.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill()
        try:
            p.wait(timeout=5)
        except Exception:
            pass
        text = b"".join(chunks).decode("utf-8", errors="replace")
        if job_id:
            update_progress(job_id, text + "\n[timeout]", engine=engine)
        return text, -1, f"timeout {timeout}s"

    t.join(timeout=5)
    text = b"".join(chunks).decode("utf-8", errors="replace")
    if job_id:
        try:
            from pocket.jobs import is_cancelled

            if is_cancelled(job_id) or cancelled.is_set():
                update_progress(job_id, (text or "") + "\n[cancelled]", engine=engine)
                return text, -2, "cancelled"
        except Exception:
            pass
        update_progress(job_id, text, engine=engine)
    return text, int(p.returncode or 0), ""
