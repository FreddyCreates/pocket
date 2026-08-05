"""Work types & work loops — easy generation for platform agents.

A WorkType is a reusable unit of agent labor (what kind of work).
A WorkLoop is an ordered graph of work types (how they chain) with
retry, stop, and cortex/subcortex binding.

Design goals: one-click templates, JSON that humans can edit, live in UI.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket" / "work_studio"
TYPES = ROOT / "types"
LOOPS = ROOT / "loops"
ROOT.mkdir(parents=True, exist_ok=True)
TYPES.mkdir(exist_ok=True)
LOOPS.mkdir(exist_ok=True)
_lock = Lock()

# Built-in catalog — well-named, product-facing
BUILTIN_TYPES: List[Dict[str, Any]] = [
    {
        "id": "wt_plan",
        "name": "Plan",
        "icon": "◇",
        "color": "#60a5fa",
        "layer": "cortex",
        "description": "Clarify goal, constraints, success metrics",
        "engine": "plan",
        "inputs": ["goal"],
        "outputs": ["plan.md"],
        "subcortex": ["world_search"],
    },
    {
        "id": "wt_design",
        "name": "Design",
        "icon": "✦",
        "color": "#a78bfa",
        "layer": "cortex",
        "description": "Structure UX / architecture before code",
        "engine": "design",
        "inputs": ["plan"],
        "outputs": ["design.md"],
        "subcortex": ["archetype_match"],
    },
    {
        "id": "wt_code",
        "name": "Code",
        "icon": "⌘",
        "color": "#34d399",
        "layer": "cortex",
        "description": "Write real files in workspace",
        "engine": "implement",
        "inputs": ["design"],
        "outputs": ["project/"],
        "subcortex": ["syntax_lookup"],
    },
    {
        "id": "wt_test",
        "name": "Test",
        "icon": "◎",
        "color": "#fbbf24",
        "layer": "subcortex",
        "description": "Silent pytest / real checks while user reads",
        "engine": "test",
        "inputs": ["project"],
        "outputs": ["TEST_REPORT.md"],
        "subcortex": ["fact_check"],
    },
    {
        "id": "wt_fix",
        "name": "Fix",
        "icon": "↺",
        "color": "#f87171",
        "layer": "subcortex",
        "description": "Retry failed tests with dep install",
        "engine": "fix",
        "inputs": ["TEST_REPORT"],
        "outputs": ["FIX_LOG.md"],
        "subcortex": [],
    },
    {
        "id": "wt_ship",
        "name": "Ship",
        "icon": "▲",
        "color": "#10a37f",
        "layer": "cortex",
        "description": "Package, deploy static, write SHIP.md",
        "engine": "ship",
        "inputs": ["project"],
        "outputs": ["SHIP.md"],
        "subcortex": [],
    },
    {
        "id": "wt_research",
        "name": "Research",
        "icon": "◈",
        "color": "#22d3ee",
        "layer": "subcortex",
        "description": "Background web + world-model retrieval",
        "engine": "research",
        "inputs": ["goal"],
        "outputs": ["research.md"],
        "subcortex": ["world_search", "fact_check"],
    },
    {
        "id": "wt_narrative",
        "name": "Narrative",
        "icon": "❧",
        "color": "#e879f9",
        "layer": "cortex",
        "description": "Story/prose generation with archetype awareness",
        "engine": "narrative",
        "inputs": ["goal"],
        "outputs": ["story.md"],
        "subcortex": ["archetype_match", "prose_style", "timeline_update"],
    },
    {
        "id": "wt_wsl",
        "name": "WSL",
        "icon": "⬡",
        "color": "#8b5cf6",
        "layer": "subcortex",
        "description": "Native Linux hands on host",
        "engine": "wsl",
        "inputs": ["goal"],
        "outputs": ["wsl_log.md"],
        "subcortex": [],
    },
    {
        "id": "wt_host",
        "name": "Host ops",
        "icon": "▣",
        "color": "#fb923c",
        "layer": "subcortex",
        "description": "Desktop / capture / real-world queue",
        "engine": "host",
        "inputs": ["goal"],
        "outputs": ["ops.md"],
        "subcortex": [],
    },
]

BUILTIN_LOOPS: List[Dict[str, Any]] = [
    {
        "id": "wl_ship_standard",
        "name": "Standard ship",
        "description": "Plan → design → code → test → fix → ship",
        "color": "#10a37f",
        "steps": ["wt_plan", "wt_design", "wt_code", "wt_test", "wt_fix", "wt_ship"],
        "max_retries": 3,
        "always_on_eligible": True,
        "cortex_voice": True,
        "subcortex_silent": True,
    },
    {
        "id": "wl_story_engine",
        "name": "Story engine",
        "description": "Narrative with silent world-model fact/timeline work",
        "color": "#e879f9",
        "steps": ["wt_plan", "wt_research", "wt_narrative", "wt_test"],
        "max_retries": 2,
        "always_on_eligible": True,
        "cortex_voice": True,
        "subcortex_silent": True,
    },
    {
        "id": "wl_code_sprint",
        "name": "Code sprint",
        "description": "Fast code + test loop for APIs and CLIs",
        "color": "#34d399",
        "steps": ["wt_plan", "wt_code", "wt_test", "wt_fix", "wt_ship"],
        "max_retries": 4,
        "always_on_eligible": True,
        "cortex_voice": True,
        "subcortex_silent": True,
    },
    {
        "id": "wl_swarm_pulse",
        "name": "Swarm pulse",
        "description": "Always-on heartbeat work unit for the swarm",
        "color": "#f472b6",
        "steps": ["wt_research", "wt_plan", "wt_code", "wt_test"],
        "max_retries": 2,
        "always_on_eligible": True,
        "cortex_voice": False,
        "subcortex_silent": True,
    },
]


def _slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9_]+", "_", (s or "work").lower()).strip("_")
    return (s or "work")[:40]


def _ensure_builtins() -> None:
    with _lock:
        for t in BUILTIN_TYPES:
            fp = TYPES / f"{t['id']}.json"
            if not fp.exists():
                fp.write_text(json.dumps(t, indent=2), encoding="utf-8")
        for L in BUILTIN_LOOPS:
            fp = LOOPS / f"{L['id']}.json"
            if not fp.exists():
                fp.write_text(json.dumps(L, indent=2), encoding="utf-8")


def list_types() -> List[Dict[str, Any]]:
    _ensure_builtins()
    out = []
    for fp in sorted(TYPES.glob("*.json")):
        try:
            out.append(json.loads(fp.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def list_loops() -> List[Dict[str, Any]]:
    _ensure_builtins()
    out = []
    for fp in sorted(LOOPS.glob("*.json")):
        try:
            out.append(json.loads(fp.read_text(encoding="utf-8")))
        except Exception:
            pass
    return out


def get_type(tid: str) -> Optional[Dict[str, Any]]:
    for t in list_types():
        if t.get("id") == tid:
            return t
    return None


def get_loop(lid: str) -> Optional[Dict[str, Any]]:
    for L in list_loops():
        if L.get("id") == lid:
            return L
    return None


def create_type(
    *,
    name: str,
    description: str = "",
    engine: str = "plan",
    layer: str = "cortex",
    color: str = "#10a37f",
    icon: str = "●",
    subcortex: Optional[List[str]] = None,
    inputs: Optional[List[str]] = None,
    outputs: Optional[List[str]] = None,
) -> Dict[str, Any]:
    tid = "wt_" + _slug(name)
    rec = {
        "id": tid,
        "name": name,
        "icon": icon,
        "color": color,
        "layer": layer if layer in ("cortex", "subcortex") else "cortex",
        "description": description or f"Custom work type: {name}",
        "engine": engine,
        "inputs": inputs or ["goal"],
        "outputs": outputs or [f"{_slug(name)}.md"],
        "subcortex": subcortex or [],
        "custom": True,
        "created_at": time.time(),
    }
    with _lock:
        (TYPES / f"{tid}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return {"ok": True, **rec}


def create_loop(
    *,
    name: str,
    steps: Optional[List[str]] = None,
    description: str = "",
    color: str = "#10a37f",
    max_retries: int = 3,
    always_on_eligible: bool = True,
    cortex_voice: bool = True,
    subcortex_silent: bool = True,
    from_prompt: str = "",
) -> Dict[str, Any]:
    """Easy generation: pass steps or a natural language prompt."""
    lid = "wl_" + _slug(name) + "_" + uuid.uuid4().hex[:4]
    if not steps and from_prompt:
        steps = _infer_steps(from_prompt)
    steps = steps or ["wt_plan", "wt_code", "wt_test", "wt_ship"]
    # validate known types (unknown kept as custom engines later)
    known = {t["id"] for t in list_types()}
    steps = [s for s in steps if s in known] or ["wt_plan", "wt_code", "wt_ship"]
    rec = {
        "id": lid,
        "name": name,
        "description": description or from_prompt or f"Loop: {name}",
        "color": color,
        "steps": steps,
        "max_retries": max_retries,
        "always_on_eligible": always_on_eligible,
        "cortex_voice": cortex_voice,
        "subcortex_silent": subcortex_silent,
        "custom": True,
        "created_at": time.time(),
    }
    with _lock:
        (LOOPS / f"{lid}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return {"ok": True, **rec}


def _infer_steps(prompt: str) -> List[str]:
    p = (prompt or "").lower()
    steps = ["wt_plan"]
    if any(k in p for k in ("story", "novel", "narrative", "character", "plot")):
        steps += ["wt_research", "wt_narrative"]
    if any(k in p for k in ("design", "ui", "ux", "layout")):
        steps.append("wt_design")
    if any(k in p for k in ("code", "api", "app", "build", "implement", "ship", "full")):
        steps.append("wt_code")
    if any(k in p for k in ("test", "qa", "fix", "bug")):
        steps += ["wt_test", "wt_fix"]
    if any(k in p for k in ("wsl", "linux")):
        steps.append("wt_wsl")
    if any(k in p for k in ("desktop", "host", "real world", "embody")):
        steps.append("wt_host")
    if "ship" in p or "deploy" in p or "release" in p:
        steps.append("wt_ship")
    # de-dupe preserve order
    seen = set()
    out = []
    for s in steps:
        if s not in seen:
            seen.add(s)
            out.append(s)
    if "wt_ship" not in out and ("app" in p or "product" in p):
        out.append("wt_ship")
    return out or ["wt_plan", "wt_code", "wt_test", "wt_ship"]


def generate_from_goal(goal: str) -> Dict[str, Any]:
    """One-shot: invent a named loop from a goal string."""
    goal = (goal or "").strip()
    name = " ".join(goal.split()[:5]) or "Generated loop"
    loop = create_loop(name=name, from_prompt=goal, description=f"Auto-generated for: {goal[:200]}")
    return {
        "ok": True,
        "loop": loop,
        "hint": "Attach to always-on swarm or run via POST /v1/build-loops with work_loop id",
    }


def catalog() -> Dict[str, Any]:
    _ensure_builtins()
    return {
        "ok": True,
        "schema": "pocket.work_studio.v1",
        "types": list_types(),
        "loops": list_loops(),
        "layers": {
            "cortex": "User-facing dialogue / explanations (System 1 stream)",
            "subcortex": "Silent background world + tests + retrieval (System 2)",
        },
    }
