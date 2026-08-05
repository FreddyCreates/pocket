"""Always-on swarm — continuous multi-agent labor on the host.

Pulses eligible work loops on an interval. Each pulse can:
  - run a build_loop use-case
  - fire dual cortex/subcortex warm-ups
  - tick world-model maintenance

Designed to start with the POCKET host and survive desk reloads.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "swarm"
STATE = ROOT / "always_on.json"
ROOT.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()
_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_started = False


def _default_state() -> Dict[str, Any]:
    return {
        "enabled": False,
        "interval_sec": 90,
        "max_parallel": 2,
        "work_loops": ["wl_swarm_pulse", "wl_code_sprint"],
        "use_cases": ["fullstack_web_app", "api_microservice"],
        "rotate_i": 0,
        "pulses": 0,
        "last_pulse_at": 0,
        "last_result": {},
        "history": [],
        "warm_dual": True,
        "world_model_tick": True,
    }


def _load() -> Dict[str, Any]:
    if STATE.exists():
        try:
            data = json.loads(STATE.read_text(encoding="utf-8"))
            base = _default_state()
            base.update(data)
            return base
        except Exception:
            pass
    return _default_state()


def _save(data: Dict[str, Any]) -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")


def status() -> Dict[str, Any]:
    data = _load()
    alive = _started and _thread is not None and _thread.is_alive()
    return {
        "ok": True,
        "schema": "pocket.always_on_swarm.v1",
        "running": alive and bool(data.get("enabled")),
        "thread_alive": alive,
        "enabled": bool(data.get("enabled")),
        "interval_sec": data.get("interval_sec"),
        "work_loops": data.get("work_loops"),
        "use_cases": data.get("use_cases"),
        "pulses": data.get("pulses"),
        "last_pulse_at": data.get("last_pulse_at"),
        "last_result": data.get("last_result"),
        "history": (data.get("history") or [])[-12:],
        "max_parallel": data.get("max_parallel"),
    }


def configure(**kwargs) -> Dict[str, Any]:
    with _lock:
        data = _load()
        for k in (
            "interval_sec",
            "max_parallel",
            "work_loops",
            "use_cases",
            "warm_dual",
            "world_model_tick",
        ):
            if k in kwargs and kwargs[k] is not None:
                data[k] = kwargs[k]
        if "interval_sec" in data:
            data["interval_sec"] = max(15, int(data["interval_sec"]))
        _save(data)
    return status()


def start(*, interval_sec: Optional[int] = None) -> Dict[str, Any]:
    global _started, _thread
    with _lock:
        data = _load()
        data["enabled"] = True
        if interval_sec:
            data["interval_sec"] = max(15, int(interval_sec))
        _save(data)
        _stop.clear()
        if _thread and _thread.is_alive():
            return status()
        _thread = threading.Thread(target=_loop, name="pocket-always-on-swarm", daemon=True)
        _thread.start()
        _started = True
    emit("swarm", "always-on swarm started", agent="SWARM", role="daemon")
    # immediate first pulse in background
    threading.Thread(target=_pulse_once, name="swarm-pulse0", daemon=True).start()
    return status()


def stop() -> Dict[str, Any]:
    with _lock:
        data = _load()
        data["enabled"] = False
        _save(data)
        _stop.set()
    emit("swarm", "always-on swarm stopped", agent="SWARM", role="daemon")
    return status()


def ensure_running() -> Dict[str, Any]:
    """Idempotent — used by host boot."""
    data = _load()
    if data.get("enabled"):
        return start()
    # default: enable always-on for product machines unless explicitly disabled
    if data.get("enabled") is False and data.get("pulses", 0) == 0 and not STATE.exists():
        return start()
    # if never configured, auto-enable
    if not STATE.exists() or data.get("auto_boot", True):
        return start(interval_sec=int(data.get("interval_sec") or 90))
    return status()


def _loop() -> None:
    while not _stop.is_set():
        data = _load()
        if not data.get("enabled"):
            time.sleep(2)
            continue
        try:
            _pulse_once()
        except Exception as e:
            emit("swarm", f"pulse error {e}", agent="SWARM", role="daemon")
        iv = max(15, int(data.get("interval_sec") or 90))
        # sleep in slices so stop is responsive
        for _ in range(iv):
            if _stop.is_set() or not _load().get("enabled"):
                break
            time.sleep(1)


def _pulse_once() -> Dict[str, Any]:
    from pocket.build_loop import run_use_case, start_loop
    from pocket.work_types import get_loop, list_loops

    data = _load()
    result: Dict[str, Any] = {"at": time.time(), "id": f"pulse-{uuid.uuid4().hex[:8]}"}

    # 1) world model tick (silent)
    if data.get("world_model_tick", True):
        try:
            from pocket import world_model as wm

            st = wm.status()
            result["world_model"] = st.get("counts")
            wm.log_subcortex("swarm_tick", "always-on pulse")
        except Exception as e:
            result["world_model_error"] = str(e)[:120]

    # 2) dual-loop warm (subcortex) without user chat noise
    if data.get("warm_dual", True):
        try:
            from pocket.cortex_subcortex import start_dual

            dual = start_dual(
                "Swarm pulse: maintain world model and ready next ship unit",
                mode="swarm",
                wait_subcortex_ms=80,
            )
            result["dual"] = {"id": dual.get("id"), "subcortex_done": dual.get("subcortex_done")}
        except Exception as e:
            result["dual_error"] = str(e)[:120]

    # 3) rotate use cases / work loops
    use_cases = list(data.get("use_cases") or ["fullstack_web_app"])
    loops = list(data.get("work_loops") or [])
    i = int(data.get("rotate_i") or 0)
    pick_uc = use_cases[i % len(use_cases)] if use_cases else "fullstack_web_app"
    pick_loop = None
    if loops:
        pick_loop = loops[i % len(loops)]
    data["rotate_i"] = i + 1

    try:
        if pick_loop:
            wl = get_loop(pick_loop) or {}
            # map work loop → build_loop kind heuristically
            goal = f"Always-on swarm pulse via {wl.get('name') or pick_loop}"
            started = start_loop(
                goal,
                template="web_static" if "story" not in (pick_loop or "") else "web_static",
                loop_kind="ship",
                owner="swarm",
                name=f"swarm-{pick_loop}",
            )
            result["build"] = {"id": started.get("id"), "via": "work_loop", "loop": pick_loop}
        else:
            started = run_use_case(pick_uc, goal=f"Always-on swarm: {pick_uc}", owner="swarm")
            result["build"] = {"id": started.get("id"), "via": "use_case", "use_case": pick_uc}
    except Exception as e:
        result["build_error"] = str(e)[:200]

    data["pulses"] = int(data.get("pulses") or 0) + 1
    data["last_pulse_at"] = time.time()
    data["last_result"] = result
    hist = list(data.get("history") or [])
    hist.append({"at": result["at"], "id": result["id"], "build": result.get("build")})
    data["history"] = hist[-40:]
    with _lock:
        _save(data)
    emit("swarm", f"pulse {result['id']}", agent="SWARM", role="daemon")
    return result


def pulse_now() -> Dict[str, Any]:
    return {"ok": True, "result": _pulse_once(), "status": status()}
