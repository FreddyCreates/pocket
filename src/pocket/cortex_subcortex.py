"""Dual-loop: Cortex (System 1) + Subcortex (System 2).

While Cortex streams conversational prose / coding explanations,
Subcortex silently:
  - world-model search & fact-check
  - narrative timeline / character updates
  - syntax lookups
  - optional test ticks
  - writes SQLite state before the user finishes reading

No step-logs dumped into the chat unless asked — only a soft "working" pulse.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "dual_loop"
ROOT.mkdir(parents=True, exist_ok=True)
_lock = threading.Lock()
_jobs: Dict[str, Dict[str, Any]] = {}


def _save(job: Dict[str, Any]) -> None:
    fp = ROOT / f"{job['id']}.json"
    fp.write_text(json.dumps(job, indent=2, default=str), encoding="utf-8")


def get_job(jid: str) -> Optional[Dict[str, Any]]:
    with _lock:
        if jid in _jobs:
            return json.loads(json.dumps(_jobs[jid], default=str))
    fp = ROOT / f"{jid}.json"
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def list_jobs(limit: int = 30) -> List[Dict[str, Any]]:
    with _lock:
        items = sorted(_jobs.values(), key=lambda x: x.get("updated_at") or 0, reverse=True)
        return [
            {
                "id": j["id"],
                "status": j.get("status"),
                "goal": j.get("goal"),
                "cortex_ready": j.get("cortex_ready"),
                "subcortex_done": j.get("subcortex_done"),
                "updated_at": j.get("updated_at"),
            }
            for j in items[:limit]
        ]


def _subcortex_work(job: Dict[str, Any]) -> None:
    """Silent background — never blocks cortex text assembly for long."""
    from pocket import world_model as wm

    goal = job.get("goal") or ""
    sid = job.get("session_id") or job["id"]
    tasks = job.get("subcortex_tasks") or [
        "world_search",
        "fact_check",
        "syntax_lookup",
        "timeline_update",
    ]
    results: List[Dict[str, Any]] = []
    try:
        wm.ensure_db()
        if "world_search" in tasks:
            hits = wm.search(goal, kind="all", limit=6)
            results.append({"task": "world_search", "ok": True, "n": len(hits.get("results") or [])})
            job["world_brief"] = wm.cortex_context(goal, limit=6)
            wm.log_subcortex("world_search", goal[:200])
        if "fact_check" in tasks:
            fc = wm.fact_check(goal)
            results.append({"task": "fact_check", "ok": True, "supported": fc.get("supported")})
            job["fact_check"] = fc
            wm.log_subcortex("fact_check", json.dumps(fc.get("matches") or [])[:300])
        if "syntax_lookup" in tasks:
            syn = wm.search(goal, kind="syntax", limit=4)
            results.append({"task": "syntax_lookup", "ok": True, "n": len(syn.get("results") or [])})
            job["syntax"] = syn.get("results") or []
        if "archetype_match" in tasks or "narrative" in (job.get("mode") or ""):
            arch = wm.search(goal, kind="archetype", limit=3)
            results.append({"task": "archetype_match", "ok": True, "n": len(arch.get("results") or [])})
            job["archetypes"] = arch.get("results") or []
        if "prose_style" in tasks:
            prose = wm.search(goal, kind="prose", limit=2)
            results.append({"task": "prose_style", "ok": True})
            job["prose"] = prose.get("results") or []
        if "timeline_update" in tasks:
            wm.update_narrative_state(
                sid,
                character=job.get("character") or "protagonist",
                notes=f"Subcortex pulse: {goal[:300]}",
                timeline=[{"at": time.time(), "event": "subcortex_review", "goal": goal[:120]}],
            )
            results.append({"task": "timeline_update", "ok": True})
        job["subcortex_results"] = results
        job["subcortex_done"] = True
        job["status"] = "ready" if job.get("cortex_ready") else "subcortex_done"
    except Exception as e:
        job["subcortex_error"] = str(e)[:300]
        job["subcortex_done"] = True
    job["updated_at"] = time.time()
    with _lock:
        _jobs[job["id"]] = job
        _save(job)
    emit("subcortex", f"{job['id']} silent work done", agent="SUBCORTEX", role="daemon")


def _cortex_compose(job: Dict[str, Any]) -> str:
    """Beautiful conversational reply — System 1 — informed by Subcortex when ready."""
    goal = (job.get("goal") or "").strip()
    brief = job.get("world_brief") or ""
    facts = job.get("fact_check") or {}
    syntax = job.get("syntax") or []
    arch = job.get("archetypes") or []
    prose = job.get("prose") or []

    lines = [
        f"## Working with you on this\n",
        f"{goal}\n",
    ]
    if brief:
        lines.append("\nI kept a quiet world-model pass running while drafting this — here's the useful residue:\n")
        lines.append(brief)
        lines.append("")
    if arch:
        lines.append("\n### Narrative structure\n")
        for a in arch[:2]:
            lines.append(f"- **{a.get('name')}** ({a.get('kind')}): {a.get('description')}")
    if prose:
        lines.append("\n### Prose register\n")
        for p in prose[:1]:
            lines.append(f"- Aim for: {p.get('style_notes')} (ref: {p.get('title')})")
    if facts:
        if facts.get("supported"):
            lines.append(
                f"\n### Fact pulse\n- Graph lean-support ~{facts.get('confidence')} — matches: "
                + ", ".join(m.get("triple", "") for m in (facts.get("matches") or [])[:2])
            )
        else:
            lines.append("\n### Fact pulse\n- No strong common-sense hit yet; treat claims as open.")
    if syntax:
        lines.append("\n### API fidelity\n")
        for s in syntax[:3]:
            lines.append(f"- `{s.get('language')}` `{s.get('symbol')}` — {s.get('signature')}: {s.get('doc')}")
    lines.append(
        "\n### Next moves\n"
        "1. Keep talking — Subcortex stays warm in the background.\n"
        "2. Or kick a **Build** loop / always-on swarm pulse to materialize files.\n"
        "3. Open **Work Studio** to design work types & loops without friction.\n"
    )
    lines.append("\n— *Cortex stream · Subcortex silent*\n")
    return "\n".join(lines)


def start_dual(
    goal: str,
    *,
    session_id: str = "",
    mode: str = "dialogue",
    subcortex_tasks: Optional[List[str]] = None,
    wait_subcortex_ms: int = 120,
) -> Dict[str, Any]:
    """
    Fire Subcortex thread immediately; Cortex returns after a brief wait so
    background work often finishes before the user finishes reading.
    """
    jid = f"dl-{uuid.uuid4().hex[:10]}"
    job = {
        "id": jid,
        "goal": (goal or "").strip(),
        "session_id": session_id or jid,
        "mode": mode,
        "status": "running",
        "cortex_ready": False,
        "subcortex_done": False,
        "subcortex_tasks": subcortex_tasks
        or ["world_search", "fact_check", "syntax_lookup", "timeline_update", "archetype_match", "prose_style"],
        "created_at": time.time(),
        "updated_at": time.time(),
    }
    with _lock:
        _jobs[jid] = job
        _save(job)

    t = threading.Thread(target=_subcortex_work, args=(job,), name=f"subcortex-{jid}", daemon=True)
    t.start()

    # brief yield so silent work can land
    t.join(timeout=max(0.05, wait_subcortex_ms / 1000.0))

    # Cortex composes (uses whatever Subcortex finished)
    with _lock:
        job = _jobs.get(jid) or job
    text = _cortex_compose(job)
    job["cortex_text"] = text
    job["cortex_ready"] = True
    job["status"] = "done" if job.get("subcortex_done") else "cortex_done"
    job["updated_at"] = time.time()
    with _lock:
        _jobs[jid] = job
        _save(job)

    # if subcortex still running, it will flip status when finished
    return {
        "ok": True,
        "id": jid,
        "text": text,
        "subcortex_done": bool(job.get("subcortex_done")),
        "world_brief": job.get("world_brief") or "",
        "poll": f"/v1/dual/{jid}",
        "architecture": {
            "cortex": "System 1 — conversational stream",
            "subcortex": "System 2 — silent world-model + state writes",
        },
    }


def run_dual_job(prompt: str, *, cwd: str = "", job: Optional[Dict] = None) -> tuple:
    """Executor adapter → (text, error, engine)."""
    r = start_dual(prompt, session_id=(job or {}).get("session_id") or "", mode="dialogue")
    return r.get("text") or "", "" if r.get("ok") else "dual failed", "cortex"
