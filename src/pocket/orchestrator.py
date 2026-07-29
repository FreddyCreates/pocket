"""POCKET Orchestrator — the execution engine (not the chat model).

Separates **planning** (you / ARCHON / LLM) from **doing** (this process):

  Chat / API / ARCHON
        │  intent + skill list
        ▼
  Orchestrator.execute / execute_plan
        │
        ├── skill_suite catalog (100+)
        ├── workers as sub-agents (Latin workers)
        ├── screen control (UI + vision)
        └── learn + live_events + vision tape

You should NOT micro-drive every SendKeys from the outer agent forever —
post a plan once; the orchestrator runs it, workers execute, vision records frames.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit
from pocket.live_vision import ensure_vision, latest_frame
from pocket.skill_suite import all_skills, get_skill, skill_count

VISION_TAPE = Path.home() / ".pocket" / "live" / "tape"
VISION_TAPE.mkdir(parents=True, exist_ok=True)


class Orchestrator:
    """Singleton-style host executor."""

    def __init__(self) -> None:
        self.runs = 0

    def catalog(self) -> Dict[str, Any]:
        skills = all_skills()
        return {
            "ok": True,
            "skill_count": len(skills),
            "skills": skills,
            "architecture": {
                "planning": "Human chat, ARCHON, or LLM proposes skill ids",
                "execution": "Orchestrator runs skills via workers (sub-agents)",
                "screen": "PORTARIUS/NAVIGATOR/UI + OCULUS vision",
                "persistence": "Daemon queue + learned_skills + vision tape",
            },
        }

    def execute(self, skill_id: str, *, prompt: str = "", params: Optional[Dict] = None) -> Dict[str, Any]:
        """Run one skill. Always attaches fusion perception context (platform-wide)."""
        from pocket.orchestrator_exec import dispatch_skill

        ensure_vision(interval=1.0)
        sid = (skill_id or "").strip().lower().replace("-", "_").replace(" ", "_")
        emit("orch", f"Execute skill {sid}", agent="ORCHESTRATOR", role="host")
        t0 = time.time()
        # fusion context before skill (makes every skill multimodal-aware)
        fusion_ctx = None
        try:
            from pocket.perception import agent_context

            fusion_ctx = agent_context(max_ui=280)
        except Exception:
            pass
        try:
            result = dispatch_skill(sid, prompt=prompt, params=params or {})
            ok = bool(result.get("ok", True))
        except Exception as e:
            result, ok = {"ok": False, "error": str(e)}, False
        if fusion_ctx:
            result["fusion_brief"] = fusion_ctx.get("brief")
            result["fusion_counts"] = fusion_ctx.get("counts")
            result["page_hint"] = fusion_ctx.get("page_hint")
        # vision tape sample
        try:
            fr = latest_frame(include_image=False)
            if fr.get("path"):
                tape = VISION_TAPE / f"{int(time.time())}_{sid}.jpg"
                src = Path(fr["path"])
                if src.exists():
                    tape.write_bytes(src.read_bytes())
                    result["vision_frame"] = str(tape)
        except Exception:
            pass
        self.runs += 1
        result["skill"] = sid
        result["ms"] = int((time.time() - t0) * 1000)
        result["ok"] = ok
        emit("orch", f"Skill {sid} → {ok}", agent="ORCHESTRATOR", role="host")
        return result

    def execute_plan(self, steps: List[Dict[str, Any]], *, record: bool = False) -> Dict[str, Any]:
        """Run ordered skills. Optional SPECULUM full-desktop record for whole plan."""
        from pocket.screen_record import record_start, record_stop
        from pocket.learn import record_run

        ensure_vision(interval=0.9)
        log: List[Dict[str, Any]] = []
        rec_path = None
        if record:
            rs = record_start(label="orch-plan")
            rec_path = rs.get("path")
            time.sleep(0.8)
        t0 = time.time()
        for i, step in enumerate(steps):
            sid = step.get("skill") or step.get("id") or step.get("action") or ""
            prompt = step.get("prompt") or step.get("text") or step.get("url") or ""
            params = step.get("params") or {}
            if step.get("url") and not params.get("url"):
                params = {**params, "url": step["url"]}
            r = self.execute(sid, prompt=prompt, params=params)
            log.append({"i": i, "skill": sid, "ok": r.get("ok"), "message": r.get("message"), "error": r.get("error")})
            # pacing for real UI
            time.sleep(float(step.get("wait", 0.45)))
        if record:
            stop = record_stop()
            rec_path = stop.get("path") or rec_path
        learned = record_run(
            name=f"plan_{int(time.time())}",
            steps=log,
            notes="orchestrator execute_plan",
            worker="ORCHESTRATOR",
        )
        ok_n = sum(1 for x in log if x.get("ok"))
        return {
            "ok": ok_n == len(log),
            "ok_steps": ok_n,
            "total": len(log),
            "duration_sec": round(time.time() - t0, 1),
            "recording_path": rec_path,
            "learned_skill": learned.get("id"),
            "log": log,
            "skill_catalog_size": skill_count(),
            "message": f"Orchestrator plan {ok_n}/{len(log)} · record={rec_path}",
        }

    def chat_to_plan(self, text: str) -> List[Dict[str, Any]]:
        """Tiny NL → skill plan (deterministic keywords). Expandable later with LLM."""
        t = (text or "").strip()
        low = t.lower()
        steps: List[Dict[str, Any]] = []
        if any(w in low for w in ("record", "demo", "showcase", "wow", "fundable")):
            steps.append({"skill": "record_start"})
        if "github" in low and "desktop" in low:
            steps.append({"skill": "github_desktop_peek"})
        elif "github" in low or "repo" in low:
            steps.append({"skill": "github_one_page"})
            steps.append({"skill": "research_interest"})
        if "antigravity" in low:
            steps.append({"skill": "antigravity_explore"})
        if "cursor" in low:
            steps.append({"skill": "open_cursor"})
            steps.append({"skill": "scroll_read"})
            steps.append({"skill": "close_window"})
        if "email" in low or "outlook" in low or "hi world" in low:
            steps.append({"skill": "email_hi_world"})
        if "tweet" in low or "twitter" in low or " x " in f" {low} ":
            steps.append({"skill": "tweet_hi_world"})
        if "trading" in low or "tradingview" in low:
            steps.append({"skill": "edge_tradingview"})
        if "metatrader" in low or "mt5" in low:
            steps.append({"skill": "open_metatrader"})
        if "screenshot" in low:
            steps.append({"skill": "screenshot"})
        if "notepad" in low:
            steps.append({"skill": "notepad_write", "prompt": "hello world from Grokbuild and Pocket Agents"})
        if "calc" in low:
            steps.append({"skill": "calc_sum"})
        if "spacex" in low:
            steps.append({"skill": "edge_spacex"})
        if "copilot" in low:
            steps.append({"skill": "copilot_chat_send", "prompt": "Hello from POCKET orchestrator"})
        if "wow" in low or "fundable" in low or "showcase" in low or "crazy" in low:
            return self.wow_plan()
        if not steps:
            # default useful micro plan
            steps = [
                {"skill": "vision_start"},
                {"skill": "screenshot"},
                {"skill": "github_one_page"},
                {"skill": "scroll_read"},
            ]
        if any(w in low for w in ("record", "demo", "showcase", "wow", "fundable")):
            steps.append({"skill": "record_stop"})
        return steps

    def wow_plan(self) -> List[Dict[str, Any]]:
        """Impressive multi-surface plan — different from prior demos."""
        return [
            {"skill": "record_start", "params": {"label": "wow-demo"}},
            {"skill": "vision_start"},
            {"skill": "screenshot"},
            # Product story surfaces
            {"skill": "edge_producthunt", "wait": 1.2},
            {"skill": "scroll_read"},
            {"skill": "edge_hn", "wait": 1.0},
            {"skill": "scroll_read"},
            # One real GitHub deep work
            {"skill": "github_one_page", "wait": 1.0},
            {"skill": "research_interest"},
            {"skill": "screenshot"},
            # Builder tools
            {"skill": "open_cursor", "wait": 1.5},
            {"skill": "scroll_read"},
            {"skill": "close_window"},
            {"skill": "open_antigravity", "wait": 1.5},
            {"skill": "scroll_read"},
            {"skill": "close_window"},
            # Comms
            {"skill": "tweet_hi_world", "wait": 1.0},
            {"skill": "email_hi_world", "wait": 1.2},
            # Markets glance
            {"skill": "edge_tradingview", "wait": 1.2},
            {"skill": "scroll_read"},
            # Local proof of host control
            {"skill": "notepad_write", "prompt": "POCKET ORCHESTRATOR — live host co-pilot. Skills: 100+. Workers: Latin alphas."},
            {"skill": "explorer_new_file", "params": {"name": "pocket-orchestrator.txt", "content": "Fundable host co-pilot demo\n"}},
            {"skill": "calc_sum"},
            {"skill": "screenshot_series", "params": {"n": 3}},
            {"skill": "record_stop"},
        ]

    def chat(self, text: str, *, record: bool = False) -> Dict[str, Any]:
        """Simple chat → create plan → execute (optionally record)."""
        plan = self.chat_to_plan(text)
        # auto-record for demo-like intents
        if any(k in (text or "").lower() for k in ("demo", "wow", "showcase", "fundable", "record")):
            record = True
        emit("orch", f"Chat plan ({len(plan)} steps): {(text or '')[:80]}", agent="ORCHESTRATOR", role="host")
        return {
            **self.execute_plan(plan, record=record),
            "plan": plan,
            "input": text,
            "mode": "chat_workflow",
        }

    def create_worker(self, name: str, skills: List[str], *, role: str = "custom") -> Dict[str, Any]:
        """Creation engine — mint a worker definition and optionally run its first skill."""
        from pocket.learn import record_run

        wid = re.sub(r"[^\w]+", "_", (name or "WORKER").upper())[:24]
        path = Path.home() / ".pocket" / "created_workers" / f"{wid}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        rec = {
            "id": wid,
            "role": role,
            "skills": skills,
            "created_at": time.time(),
            "class": "created",
        }
        path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        record_run(name=f"create_{wid}", steps=[{"skill": s} for s in skills], notes="created worker", worker=wid)
        emit("orch", f"Created worker {wid} with {len(skills)} skills", agent="ORCHESTRATOR", role="host")
        return {"ok": True, "worker": rec, "path": str(path), "message": f"Worker {wid} created"}


_ORCH: Optional[Orchestrator] = None


def get_orchestrator() -> Orchestrator:
    global _ORCH
    if _ORCH is None:
        _ORCH = Orchestrator()
    return _ORCH
