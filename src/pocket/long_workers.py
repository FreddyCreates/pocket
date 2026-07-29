"""Long-running workers: always-on, folder watch, daily research.

These are real processes/threads — not one-shot scripts.
"""

from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "long_workers"
ROOT.mkdir(parents=True, exist_ok=True)
WATCH = Path.home() / ".pocket" / "watch_inbox"
WATCH.mkdir(parents=True, exist_ok=True)

_threads: Dict[str, threading.Thread] = {}
_stop: Dict[str, threading.Event] = {}
_state: Dict[str, Any] = {}


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "workers": {
            k: {
                "alive": t.is_alive() if t else False,
                "state": _state.get(k),
            }
            for k, t in _threads.items()
        },
        "watch_dir": str(WATCH),
    }


def start_folder_watch() -> Dict[str, Any]:
    """When files appear in watch_inbox, observe+screenshot+log (real reaction)."""
    key = "folder_watch"
    if key in _threads and _threads[key].is_alive():
        return {"ok": True, "already": True, "worker": key}

    stop = threading.Event()
    _stop[key] = stop

    def loop():
        seen = set()
        emit("long", "Folder watch worker started", agent="WATCHER", role="python")
        while not stop.is_set():
            try:
                for p in WATCH.glob("*"):
                    if p.name in seen or p.name.startswith("."):
                        continue
                    seen.add(p.name)
                    emit("long", f"New file in watch: {p.name}", agent="WATCHER", role="python")
                    from pocket.vision_core import observe
                    from pocket.capture import capture_screen

                    obs = observe(with_ui_map=False)
                    shot = capture_screen(max_width=900)
                    rec = {
                        "file": str(p),
                        "at": time.time(),
                        "titles": obs.get("window_titles"),
                        "shot_ok": shot.get("ok"),
                    }
                    (ROOT / f"watch_{int(time.time())}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
                    _state[key] = {"last_file": p.name, "at": time.time()}
            except Exception as e:
                _state[key] = {"error": str(e)}
            stop.wait(2.0)

    t = threading.Thread(target=loop, name="pocket-folder-watch", daemon=True)
    t.start()
    _threads[key] = t
    return {"ok": True, "worker": key, "watch_dir": str(WATCH), "message": "Folder watch long-worker online"}


def start_always_on_pulse(*, interval_sec: int = 120) -> Dict[str, Any]:
    """Always-on: periodic vision sample + UI map count (host heartbeat)."""
    key = "always_on"
    if key in _threads and _threads[key].is_alive():
        return {"ok": True, "already": True}

    stop = threading.Event()
    _stop[key] = stop

    def loop():
        emit("long", "Always-on pulse worker started", agent="PULSE", role="python")
        while not stop.is_set():
            try:
                from pocket.vision_core import observe

                obs = observe(with_ui_map=True)
                _state[key] = {
                    "at": time.time(),
                    "ui_map_count": obs.get("ui_map_count"),
                    "titles": (obs.get("window_titles") or [])[:6],
                }
                (ROOT / "pulse_latest.json").write_text(json.dumps(_state[key], indent=2), encoding="utf-8")
            except Exception as e:
                _state[key] = {"error": str(e), "at": time.time()}
            stop.wait(max(30, interval_sec))

    t = threading.Thread(target=loop, name="pocket-always-on", daemon=True)
    t.start()
    _threads[key] = t
    return {"ok": True, "worker": key, "interval_sec": interval_sec}


def start_daily_research(topic: str = "AI agent desktop") -> Dict[str, Any]:
    """Schedules research via autonomy + marks long worker."""
    from pocket.autonomy import create_schedule, ensure_runner

    ensure_runner()
    rec = create_schedule(prompt=f"lookup {topic}", interval="daily", title=f"research:{topic[:40]}")
    _state["daily_research"] = rec
    return {"ok": True, "schedule": rec, "message": "Daily research long-worker scheduled"}


def stop_worker(name: str) -> Dict[str, Any]:
    ev = _stop.get(name)
    if ev:
        ev.set()
        return {"ok": True, "stopped": name}
    return {"ok": False, "error": "not found"}
