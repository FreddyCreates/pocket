"""Dynamic AI-style workers — not fixed scripts.

A worker has: goal, memory, observe→decide→act loop, short or long lifetime.
Scripts bootstrap; workers *live* and react to the real screen via vision_core.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit
from pocket.vision_core import observe, click_by_name, find_in_map, build_ui_map
# Fusion page symbols (200+) are first-class — not a side demo

BRAIN = Path.home() / ".pocket" / "worker_brains"
BRAIN.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()
_ACTIVE: Dict[str, "DynamicWorker"] = {}


class DynamicWorker:
    """Stateful worker that loops on a goal using vision + policy."""

    def __init__(
        self,
        name: str,
        goal: str,
        *,
        max_steps: int = 12,
        lifetime: str = "short",  # short | long | always
        policy: str = "explore",
    ):
        self.id = f"dw-{uuid.uuid4().hex[:10]}"
        self.name = (name or "WORKER").upper()
        self.goal = goal
        self.max_steps = max_steps
        self.lifetime = lifetime
        self.policy = policy
        self.memory: List[Dict[str, Any]] = []
        self.status = "created"
        self.created_at = time.time()
        self.thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    def brain_path(self) -> Path:
        return BRAIN / f"{self.name}_{self.id}.json"

    def save_brain(self) -> None:
        self.brain_path().write_text(
            json.dumps(
                {
                    "id": self.id,
                    "name": self.name,
                    "goal": self.goal,
                    "lifetime": self.lifetime,
                    "status": self.status,
                    "memory": self.memory[-50:],
                    "updated_at": time.time(),
                },
                indent=2,
                default=str,
            )[:200000],
            encoding="utf-8",
        )

    def decide(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        """Policy: goal-conditioned, fusion-aware (page symbols + UIA names)."""
        goal = self.goal.lower()
        names = [n.lower() for n in (obs.get("ui_names") or [])]
        # merge fusion symbol texts (the 200+ page renderer graph)
        for s in obs.get("fusion_symbols") or []:
            t = (s.get("text") or "").strip().lower()
            if t and t not in names:
                names.append(t)
        titles = " ".join(obs.get("window_titles") or []).lower()
        step_i = len(self.memory)
        # prefer action_hints from fusion when available
        hints = obs.get("action_hints") or []
        if step_i >= 1 and hints and step_i % 3 == 0:
            h = hints[0]
            if h.get("action") == "click_name" and h.get("name"):
                return {"action": "click_name", "name": h["name"], "why": f"fusion hint: {h.get('reason')}"}
            if h.get("action") == "click_xy" and h.get("x") is not None:
                return {"action": "click_xy", "x": h["x"], "y": h["y"], "why": "fusion hotspot"}

        # Goal: explore current page / read
        if any(k in goal for k in ("scroll", "read", "explore", "look", "interest", "github", "page")):
            if step_i < 3:
                return {"action": "scroll", "direction": "down", "n": 3, "why": "read content"}
            if step_i == 3:
                return {"action": "scroll", "direction": "up", "n": 1, "why": "re-center"}
            if step_i == 4:
                return {"action": "observe", "why": "rebuild vision UI map mid-explore"}
            # try click something related to goal keywords from live map
            for kw in goal.replace(",", " ").split():
                if len(kw) < 4:
                    continue
                for n in names:
                    if kw in n:
                        return {"action": "click_name", "name": n, "why": f"goal keyword {kw} on UI"}
            # common github page controls if present
            for label in ("code", "readme", "files", "go to file", "star", "fork"):
                for n in names:
                    if label in n:
                        return {"action": "click_name", "name": n, "why": f"page control: {label}"}
            if step_i < self.max_steps - 2:
                return {"action": "scroll", "direction": "down", "n": 2, "why": "continue explore"}
            if "screenshot" in goal:
                return {"action": "screenshot", "why": "goal asked for screenshot"}
            return {"action": "done", "why": "explore budget exhausted"}

        # Goal: open github and work
        if "github" in goal:
            if "github" not in titles and step_i == 0:
                return {"action": "open_url", "url": "https://github.com/", "why": "goal needs GitHub"}
            if step_i < 4:
                return {"action": "scroll", "direction": "down", "n": 3, "why": "use GitHub page"}
            for label in ("repositories", "code", "pull requests", "issues", "explore"):
                for n in names:
                    if label in n:
                        return {"action": "click_name", "name": n, "why": f"github UI: {label}"}
            return {"action": "done", "why": "github interaction cycle complete"}

        # Goal: antigravity / cursor / app
        for app, title in (("antigravity", "antigravity"), ("cursor", "cursor"), ("notepad", "notepad")):
            if app in goal:
                if title not in titles and step_i == 0:
                    return {"action": "open_app", "app": app, "why": f"open {app} for goal"}
                if step_i < 3:
                    return {"action": "scroll", "direction": "down", "n": 2, "why": f"use {app} UI"}
                if "exit" in goal or "close" in goal or step_i >= 4:
                    return {"action": "close", "why": "done with app"}
                return {"action": "done", "why": f"{app} cycle done"}

        # Goal: email / hi world
        if "email" in goal or "outlook" in goal or "hi world" in goal:
            if step_i == 0:
                return {"action": "email_hi", "why": "draft hi world email"}
            return {"action": "done", "why": "email drafted"}

        # Goal: screenshot / vision
        if "screenshot" in goal or "vision" in goal:
            if step_i == 0:
                return {"action": "screenshot", "why": "capture glass"}
            if step_i == 1:
                return {"action": "observe", "why": "rebuild UI map"}
            return {"action": "done", "why": "vision sample done"}

        # Default dynamic: observe, scroll, try interesting button, screenshot
        if step_i == 0:
            return {"action": "observe", "why": "sense environment"}
        if step_i == 1:
            return {"action": "scroll", "direction": "down", "n": 3, "why": "move like a user"}
        if step_i == 2 and names:
            # pick a mid-list named control that looks like navigation
            pick = names[min(5, len(names) - 1)]
            return {"action": "click_name", "name": pick, "why": "probe UI element from vision map"}
        if step_i == 3:
            return {"action": "screenshot", "why": "document state"}
        return {"action": "done", "why": "default policy complete"}

    def act(self, decision: Dict[str, Any]) -> Dict[str, Any]:
        action = decision.get("action")
        emit("worker", f"{self.name} act={action} ({decision.get('why')})", agent=self.name, role="python")
        try:
            if action == "observe":
                return {"ok": True, "obs": observe(with_ui_map=True)}
            if action == "scroll":
                from pocket.ui_click import scroll_page

                return scroll_page(int(decision.get("n") or 3), direction=decision.get("direction") or "down")
            if action == "click_name":
                # fusion symbol click first, then UIA map
                try:
                    from pocket.perception import act_on_symbol

                    r = act_on_symbol(decision.get("name") or "")
                    if r.get("ok"):
                        return r
                except Exception:
                    pass
                return click_by_name(decision.get("name") or "")
            if action == "click_xy":
                from pocket.vision_core import click_xy

                return click_xy(int(decision.get("x") or 0), int(decision.get("y") or 0))
            if action == "open_url":
                from pocket.browser_mode import open_edge_url

                return open_edge_url(decision.get("url") or "https://example.com", new_window=True)
            if action == "open_app":
                from pocket.desktop import open_app

                return open_app(decision.get("app") or "notepad")
            if action == "close":
                from pocket.ui_click import close_foreground_window

                return close_foreground_window()
            if action == "email_hi":
                from pocket.skills_real import skill_email_hi_world

                return skill_email_hi_world()
            if action == "screenshot":
                from pocket.capture import capture_screen

                return capture_screen()
            if action == "done":
                return {"ok": True, "done": True}
            return {"ok": False, "error": f"unknown action {action}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def run_loop(self) -> Dict[str, Any]:
        self.status = "running"
        self.save_brain()
        for i in range(self.max_steps):
            if self._stop.is_set():
                self.status = "stopped"
                break
            # Unified perception: classic observe + fusion page symbols
            obs = observe(with_ui_map=True)
            try:
                from pocket.perception import agent_context

                ctx = agent_context(max_ui=350)
                obs["fusion_brief"] = ctx.get("brief")
                obs["fusion_symbols"] = ctx.get("symbol_sample") or []
                obs["action_hints"] = ctx.get("action_hints") or []
                obs["ui_names"] = list(obs.get("ui_names") or []) + [
                    s.get("text") for s in (ctx.get("symbol_sample") or []) if s.get("text")
                ]
                obs["page_hint"] = ctx.get("page_hint")
            except Exception:
                pass
            # strip huge b64 from memory
            obs_small = {k: v for k, v in obs.items() if k not in ("_frame_b64", "fusion_symbols")}
            decision = self.decide(obs)
            result = self.act(decision)
            self.memory.append(
                {
                    "step": i,
                    "decision": decision,
                    "result_ok": result.get("ok"),
                    "result": {k: result.get(k) for k in ("message", "error", "method", "matched", "why") if k in result or k == "why"},
                    "ui_count": obs_small.get("ui_map_count"),
                    "titles": (obs_small.get("window_titles") or [])[:5],
                    "at": time.time(),
                }
            )
            self.save_brain()
            if decision.get("action") == "done" or result.get("done"):
                self.status = "completed"
                break
            time.sleep(0.55)
        else:
            self.status = "completed"
        self.save_brain()
        return {
            "ok": True,
            "worker_id": self.id,
            "name": self.name,
            "goal": self.goal,
            "status": self.status,
            "steps": len(self.memory),
            "memory": self.memory,
            "brain": str(self.brain_path()),
            "message": f"Dynamic worker {self.name} finished ({self.status}) steps={len(self.memory)}",
        }

    def start_async(self) -> None:
        self.thread = threading.Thread(target=self.run_loop, name=f"dw-{self.name}", daemon=True)
        self.thread.start()
        with _lock:
            _ACTIVE[self.id] = self

    def stop(self) -> None:
        self._stop.set()


def spawn_worker(goal: str, *, name: str = "AUTON", max_steps: int = 10, async_: bool = False) -> Dict[str, Any]:
    w = DynamicWorker(name, goal, max_steps=max_steps)
    emit("worker", f"Spawn {w.name} goal={goal[:80]}", agent="ORCHESTRATOR", role="host")
    if async_:
        w.start_async()
        return {"ok": True, "worker_id": w.id, "name": w.name, "status": "running_async", "goal": goal}
    return w.run_loop()


def list_active() -> List[Dict[str, Any]]:
    with _lock:
        return [
            {"id": w.id, "name": w.name, "goal": w.goal, "status": w.status, "steps": len(w.memory)}
            for w in _ACTIVE.values()
        ]
