"""Custom agent builder — Emergent-style specialized agents with tools + sub-agents.

Agents persist under ~/.pocket/custom_agents/ and register on the mesh.
They can be invoked from desk @mentions, build loops, and the phone app.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket" / "custom_agents"
ROOT.mkdir(parents=True, exist_ok=True)
_lock = Lock()

TOOL_CATALOG = {
    "files": "Read/write workspace files",
    "web": "Search and fetch URLs",
    "git": "Sovereign git / repo notes",
    "test": "Run pytest / npm test heuristics",
    "shell": "Host shell (founder only)",
    "wsl": "Native WSL Linux (founder only)",
    "desktop": "Open apps / capture (founder only)",
    "mesh": "Send mesh messages / leave artifacts",
    "deploy": "Static deploy helper",
    "plan": "Structured planning only",
}


def _slug(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]+", "_", (name or "agent").strip()).strip("_").upper()
    return (s or "AGENT")[:32]


def _path(aid: str) -> Path:
    return ROOT / f"{aid.lower()}.json"


def list_agents() -> List[Dict[str, Any]]:
    out = []
    with _lock:
        for fp in sorted(ROOT.glob("*.json")):
            try:
                out.append(json.loads(fp.read_text(encoding="utf-8")))
            except Exception:
                continue
    return out


def get_agent(aid: str) -> Optional[Dict[str, Any]]:
    aid = _slug(aid)
    fp = _path(aid)
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return None


def create_agent(
    *,
    name: str,
    role: str = "",
    personality: str = "",
    tools: Optional[List[str]] = None,
    sub_agents: Optional[List[str]] = None,
    system: str = "",
    owner: str = "pocket",
) -> Dict[str, Any]:
    aid = _slug(name)
    tools = [t for t in (tools or ["files", "plan", "mesh"]) if t in TOOL_CATALOG]
    if not tools:
        tools = ["files", "plan"]
    sub_agents = [ _slug(s) for s in (sub_agents or []) ][:8]
    rec = {
        "id": aid,
        "name": name or aid,
        "role": (role or "specialist")[:200],
        "personality": (personality or "precise, helpful, ships real artifacts")[:500],
        "system": (system or "")[:4000],
        "tools": tools,
        "sub_agents": sub_agents,
        "owner": owner,
        "created_at": time.time(),
        "runs": 0,
        "last_at": 0,
        "status": "ready",
    }
    with _lock:
        _path(aid).write_text(json.dumps(rec, indent=2), encoding="utf-8")
    try:
        from pocket.mesh_disk import ensure_agent

        ensure_agent(aid, role="custom")
    except Exception:
        pass
    return {"ok": True, **rec}


def delete_agent(aid: str) -> Dict[str, Any]:
    aid = _slug(aid)
    fp = _path(aid)
    if fp.exists():
        fp.unlink()
        return {"ok": True, "deleted": aid}
    return {"ok": False, "error": "not found"}


def run_custom_agent(aid: str, prompt: str, *, cwd: str = "", job: Optional[Dict] = None) -> Dict[str, Any]:
    """Execute one turn: plan → tool actions → optional sub-agent fan-out → artifact."""
    agent = get_agent(aid)
    if not agent:
        return {"ok": False, "error": f"custom agent {aid} not found"}
    job = job or {}
    text = (prompt or "").strip()
    work = Path(cwd or job.get("cwd") or (Path.home() / ".pocket" / "workspaces" / "custom" / aid.lower()))
    work.mkdir(parents=True, exist_ok=True)
    steps: List[Dict[str, Any]] = []
    tools = set(agent.get("tools") or [])

    # 1) write brief
    if "files" in tools or "plan" in tools:
        brief = work / f"brief_{int(time.time())}.md"
        body = (
            f"# {agent.get('name')} run\n\n"
            f"**Role:** {agent.get('role')}\n"
            f"**Personality:** {agent.get('personality')}\n\n"
            f"## Task\n{text}\n\n"
            f"## System\n{agent.get('system') or '(default)'}\n"
        )
        brief.write_text(body, encoding="utf-8")
        steps.append({"tool": "files", "ok": True, "path": str(brief)})

    # 2) plan skeleton
    plan_path = work / "PLAN.md"
    plan_path.write_text(
        f"# Plan — {agent.get('id')}\n\n"
        f"1. Understand: {text[:400]}\n"
        f"2. Tools: {', '.join(tools)}\n"
        f"3. Sub-agents: {', '.join(agent.get('sub_agents') or []) or 'none'}\n"
        f"4. Deliver artifact under `{work}`\n"
        f"5. Report status\n",
        encoding="utf-8",
    )
    steps.append({"tool": "plan", "ok": True, "path": str(plan_path)})

    # 3) optional web research note
    if "web" in tools and any(k in text.lower() for k in ("research", "lookup", "search", "find")):
        try:
            from pocket.web_research import search_web

            sr = search_web(text[:200])
            (work / "research.json").write_text(json.dumps(sr, indent=2)[:12000], encoding="utf-8")
            steps.append({"tool": "web", "ok": True})
        except Exception as e:
            steps.append({"tool": "web", "ok": False, "error": str(e)[:200]})

    # 4) mesh artifact
    if "mesh" in tools:
        try:
            from pocket.mesh_disk import leave_artifact

            leave_artifact(
                agent["id"],
                f"custom_{int(time.time())}.md",
                f"# {agent['id']}\n\n{text[:2000]}\n",
                notify=["ARCHON"],
            )
            steps.append({"tool": "mesh", "ok": True})
        except Exception as e:
            steps.append({"tool": "mesh", "ok": False, "error": str(e)[:120]})

    # 5) fan-out sub-agents (non-blocking style sequential with cap)
    sub_results = []
    for sub in (agent.get("sub_agents") or [])[:4]:
        try:
            from pocket.subagent_dispatch import dispatch

            r = dispatch(f"@{sub} assist for: {text[:300]}", from_agent=agent["id"], agents=[sub])
            sub_results.append({"agent": sub, "ok": r.get("ok")})
        except Exception as e:
            sub_results.append({"agent": sub, "ok": False, "error": str(e)[:120]})

    # 6) deliverable stub code if backend-ish role
    role = (agent.get("role") or "").lower()
    if any(x in role for x in ("code", "backend", "frontend", "build", "engineer")):
        src = work / "main.py"
        if not src.exists():
            src.write_text(
                f'"""Generated by custom agent {agent["id"]}"""\n'
                f"def main():\n"
                f"    print({text[:80]!r})\n"
                f"\n"
                f"if __name__ == '__main__':\n"
                f"    main()\n",
                encoding="utf-8",
            )
            steps.append({"tool": "files", "ok": True, "path": str(src)})

    agent["runs"] = int(agent.get("runs") or 0) + 1
    agent["last_at"] = time.time()
    with _lock:
        _path(agent["id"]).write_text(json.dumps(agent, indent=2), encoding="utf-8")

    summary = (
        f"## {agent.get('name')} complete\n\n"
        f"- Steps: {len(steps)}\n"
        f"- Workspace: `{work}`\n"
        f"- Sub-agents: {sub_results}\n"
        f"- Tools used: {[s.get('tool') for s in steps]}\n"
    )
    return {
        "ok": True,
        "agent": agent["id"],
        "workspace": str(work),
        "steps": steps,
        "sub_agents": sub_results,
        "summary": summary,
        "engine": f"custom:{agent['id']}",
    }


def tools_catalog() -> Dict[str, Any]:
    return {"ok": True, "tools": TOOL_CATALOG}
