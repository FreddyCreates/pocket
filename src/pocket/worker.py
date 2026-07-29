"""Concurrent worker pool — many agents/terminals at once."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Optional

from pocket.executor import run_job
from pocket.jobs import claim, finish, next_queued

_pool: Optional[ThreadPoolExecutor] = None
_inflight = 0
_inflight_lock = Lock()
_MAX = 4  # parallel Codex/shell/WSL jobs


def _run_claimed(job: dict) -> None:
    global _inflight
    jid = job["id"]
    print(f"[POCKET worker] running {jid} mode={job.get('mode')} session={job.get('session_id')}", flush=True)
    try:
        result, error, engine = run_job(job)
        try:
            from pocket.reply_format import polish_agent_output

            # Final pass so stored session transcripts stay chat-readable
            result = polish_agent_output(result or "", engine=str(engine or job.get("mode") or ""))
        except Exception:
            pass
        finish(jid, result=result, error=error, engine=engine)
        print(f"[POCKET worker] {jid} -> done engine={engine} err={bool(error)}", flush=True)
    except Exception as e:
        finish(jid, result="", error=str(e), engine=job.get("mode") or "unknown")
        print(f"[POCKET worker] {jid} exception {e}", flush=True)
    finally:
        with _inflight_lock:
            _inflight -= 1


def ensure_pool() -> ThreadPoolExecutor:
    global _pool
    if _pool is None:
        _pool = ThreadPoolExecutor(max_workers=_MAX, thread_name_prefix="pocket-job")
    return _pool


def process_one() -> bool:
    """Claim one job if capacity; return True if work scheduled or was available."""
    global _inflight
    with _inflight_lock:
        if _inflight >= _MAX:
            return True  # busy, keep loop warm
        capacity = True
    job = next_queued()
    if not job:
        return False
    claimed = claim(job["id"])
    if not claimed:
        return False
    with _inflight_lock:
        _inflight += 1
    ensure_pool().submit(_run_claimed, claimed)
    return True


def run_loop(poll: float = 0.6) -> None:
    print("POCKET worker pool — multi-agent concurrent executor", flush=True)
    ensure_pool()
    while True:
        try:
            # drain up to capacity each tick
            progressed = False
            for _ in range(_MAX):
                if process_one():
                    progressed = True
                else:
                    break
            if not progressed:
                time.sleep(poll)
            else:
                time.sleep(0.15)
        except KeyboardInterrupt:
            print("worker stop", flush=True)
            break
        except Exception as e:
            print(f"[worker error] {e}", flush=True)
            time.sleep(2)


if __name__ == "__main__":
    run_loop()
