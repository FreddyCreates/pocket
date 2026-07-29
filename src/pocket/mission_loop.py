"""Long-running mission loop — multi-hour agent work with chain prompts.

Pattern (what you asked for):
  1. Start a mission with a goal + queue of prompts/steps
  2. Each step: fusion sense → decide/act → log
  3. When a step ends, automatically start the next prompt
  4. Mission can run for hours; poll status; inject more work

This is the production backbone so Grok/Codex/Claude can leave work running.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "missions"
ROOT.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()
_missions: Dict[str, Dict[str, Any]] = {}
_threads: Dict[str, threading.Thread] = {}
_stops: Dict[str, threading.Event] = {}


def list_missions() -> List[Dict[str, Any]]:
    with _lock:
        return [
            {
                "id": m["id"],
                "status": m["status"],
                "goal": m.get("goal"),
                "step_i": m.get("step_i"),
                "total": len(m.get("queue") or []),
                "results_n": len(m.get("results") or []),
                "updated_at": m.get("updated_at"),
            }
            for m in _missions.values()
        ]


def get_mission(mid: str) -> Optional[Dict[str, Any]]:
    with _lock:
        m = _missions.get(mid)
        return json.loads(json.dumps(m, default=str)) if m else None


def start_mission(
    goal: str,
    *,
    queue: Optional[List[Dict[str, Any]]] = None,
    max_hours: float = 3.0,
    step_pause_sec: float = 1.0,
    name: str = "MISSION",
) -> Dict[str, Any]:
    """
    queue items:
      { "prompt": "...", "action": "sense|skill|shell|click|open_app|codex|plan", ...params }
      or { "skill": "page_render", "params": {} }
      or { "plan": [ {skill, prompt}, ... ] }
    """
    mid = f"m-{uuid.uuid4().hex[:10]}"
    q = list(queue or [])
    if not q:
        # default sophisticated starter if empty
        q = [
            {"action": "sense", "prompt": "baseline fusion sense"},
            {"action": "skill", "skill": "page_render", "params": {"max_ui": 400}},
            {"action": "skill", "skill": "screenshot", "prompt": "snapshot"},
        ]
    mission = {
        "id": mid,
        "name": name,
        "goal": goal,
        "status": "running",
        "queue": q,
        "results": [],
        "step_i": 0,
        "created_at": time.time(),
        "updated_at": time.time(),
        "max_until": time.time() + max(0.1, max_hours) * 3600,
        "errors": [],
    }
    stop = threading.Event()
    with _lock:
        _missions[mid] = mission
        _stops[mid] = stop

    def loop():
        emit("mission", f"Mission {mid} start: {goal[:80]}", agent="ARCHON", role="host")
        # ensure virtual computer
        try:
            from pocket.virtual_computer import open_computer, status as vc_status

            st = vc_status()
            if (st.get("state") or {}).get("status") != "on":
                open_computer(label=f"mission-{mid}")
        except Exception as e:
            mission["errors"].append(str(e))

        while not stop.is_set():
            with _lock:
                m = _missions.get(mid)
                if not m or m["status"] != "running":
                    break
                if time.time() > m["max_until"]:
                    m["status"] = "timeout"
                    m["updated_at"] = time.time()
                    break
                i = m["step_i"]
                qloc = m["queue"]
                if i >= len(qloc):
                    m["status"] = "completed"
                    m["updated_at"] = time.time()
                    break
                step = dict(qloc[i])

            try:
                result = _run_step(step, mission_id=mid, goal=goal)
                ok = bool(result.get("ok", True))
            except Exception as e:
                result, ok = {"ok": False, "error": str(e)}, False

            with _lock:
                m = _missions[mid]
                m["results"].append(
                    {
                        "i": i,
                        "step": {k: step.get(k) for k in ("action", "skill", "prompt", "name") if k in step},
                        "ok": ok,
                        "brief": result.get("brief") or result.get("message") or result.get("error"),
                        "at": time.time(),
                    }
                )
                m["step_i"] = i + 1
                m["updated_at"] = time.time()
                # persist
                try:
                    (ROOT / f"{mid}.json").write_text(
                        json.dumps(m, indent=2, default=str)[:800000], encoding="utf-8"
                    )
                except Exception:
                    pass

            emit(
                "mission",
                f"{mid} step {i+1}/{len(qloc)} ok={ok}",
                agent="ARCHON",
                role="host",
            )
            stop.wait(max(0.2, float(step_pause_sec)))

        with _lock:
            m = _missions.get(mid)
            if m and m["status"] == "running":
                m["status"] = "stopped"
            if m:
                emit("mission", f"Mission {mid} → {m['status']}", agent="ARCHON", role="host")

    t = threading.Thread(target=loop, name=f"mission-{mid}", daemon=True)
    t.start()
    _threads[mid] = t
    return {"ok": True, "mission_id": mid, "status": "running", "queue_len": len(q), "goal": goal}


def enqueue(mid: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Add more work while mission is running (3-hour chain pattern)."""
    with _lock:
        m = _missions.get(mid)
        if not m:
            return {"ok": False, "error": "mission not found"}
        m["queue"].extend(steps)
        if m["status"] in ("completed", "stopped", "timeout"):
            # restart from current index
            m["status"] = "running"
            stop = threading.Event()
            _stops[mid] = stop
            # re-enter loop is complex if thread dead — start new runner if needed
            thr = _threads.get(mid)
            if not thr or not thr.is_alive():
                # call start_mission continuation via new thread on same mid
                return _resume(mid)
        m["updated_at"] = time.time()
        return {"ok": True, "queue_len": len(m["queue"]), "step_i": m["step_i"]}


def _resume(mid: str) -> Dict[str, Any]:
    m = _missions[mid]
    m["status"] = "running"
    stop = threading.Event()
    _stops[mid] = stop

    def loop():
        while not stop.is_set():
            with _lock:
                mm = _missions.get(mid)
                if not mm or mm["status"] != "running":
                    break
                if time.time() > mm["max_until"]:
                    mm["status"] = "timeout"
                    break
                i = mm["step_i"]
                if i >= len(mm["queue"]):
                    mm["status"] = "completed"
                    break
                step = dict(mm["queue"][i])
            try:
                result = _run_step(step, mission_id=mid, goal=mm.get("goal") or "")
                ok = bool(result.get("ok", True))
            except Exception as e:
                result, ok = {"ok": False, "error": str(e)}, False
            with _lock:
                mm = _missions[mid]
                mm["results"].append({"i": i, "ok": ok, "brief": result.get("brief") or result.get("message"), "at": time.time()})
                mm["step_i"] = i + 1
                mm["updated_at"] = time.time()
            stop.wait(1.0)

    t = threading.Thread(target=loop, name=f"mission-resume-{mid}", daemon=True)
    t.start()
    _threads[mid] = t
    return {"ok": True, "resumed": True, "mission_id": mid}


def stop_mission(mid: str) -> Dict[str, Any]:
    with _lock:
        if mid in _stops:
            _stops[mid].set()
        if mid in _missions:
            _missions[mid]["status"] = "stopped"
            _missions[mid]["updated_at"] = time.time()
    return {"ok": True, "status": "stopped", "mission_id": mid}


def _run_step(step: Dict[str, Any], *, mission_id: str, goal: str) -> Dict[str, Any]:
    from pocket.virtual_computer import act, shell, sense_computer
    from pocket.perception import sense, agent_context

    # always sense first (fusion into everything)
    ctx = agent_context(max_ui=300)
    action = (step.get("action") or "").lower()
    if step.get("plan"):
        from pocket.orchestrator import get_orchestrator

        r = get_orchestrator().execute_plan(step["plan"], record=bool(step.get("record")))
        r["context_before"] = ctx.get("brief")
        return r
    if step.get("skill") and not action:
        action = "skill"
    if action in ("sense", "observe", "page"):
        return sense_computer(max_ui=int(step.get("max_ui") or 500))
    if action in ("shell", "cmd"):
        return shell(step.get("command") or step.get("prompt") or "echo ok")
    if action == "skill":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute(
            step.get("skill") or "screenshot",
            prompt=step.get("prompt") or goal,
            params=step.get("params") or {},
        )
    if action in ("click", "click_name"):
        return act("click", name=step.get("name") or step.get("prompt") or "")
    if action in ("open_app", "app"):
        return act("open_app", app=step.get("app") or step.get("name") or "notepad")
    if action in ("open_url", "url"):
        return act("open_url", url=step.get("url") or step.get("prompt") or "https://github.com")
    if action == "type":
        return act("type", text=step.get("text") or step.get("prompt") or "")
    if action == "scroll":
        return act("scroll", direction=step.get("direction") or "down", n=int(step.get("n") or 3))
    if action in ("codex", "run_codex"):
        cmd = step.get("command") or step.get("prompt") or "codex --version"
        return shell(cmd, timeout=int(step.get("timeout") or 180))
    if action == "remake":
        return act("remake")
    if action in ("studio", "viral"):
        return act("studio", source=step.get("source") or "")
    if action == "wait":
        time.sleep(float(step.get("seconds") or 2))
        return {"ok": True, "waited": step.get("seconds") or 2}
    # freeform: treat prompt as orchestrator chat plan skill
    if step.get("prompt"):
        from pocket.orchestrator import get_orchestrator

        # try page_render then skill guess
        return get_orchestrator().execute(
            step.get("skill") or "see_screen",
            prompt=step["prompt"],
            params=step.get("params") or {},
        )
    return {"ok": False, "error": "empty step", "context": ctx}
