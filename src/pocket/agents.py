"""Headless agent fleet — specialized agents that run without the desk UI.

Each agent is a sellable product unit: fixed role, system prompt, engine routing,
and POCK/API pricing. Jobs still execute on the POCKET host.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Catalog (product SKUs)
# ---------------------------------------------------------------------------

AGENTS: Dict[str, Dict[str, Any]] = {
    "researcher": {
        "id": "researcher",
        "name": "Researcher",
        "role": "Web + synthesis research",
        "engine": "web",
        "tier": "starter",
        "pock": 12,
        "usd_hint": 0.04,
        "sell": True,
        "headless": True,
        "description": "Search, fetch, and synthesize sources into a brief.",
        "system": (
            "You are a rigorous research agent. Prefer primary sources. "
            "Return: summary, key facts, sources, open questions."
        ),
        "examples": ["research Cloudflare named tunnels vs quick tunnels"],
    },
    "planner": {
        "id": "planner",
        "name": "Planner",
        "role": "Product / engineering plans only",
        "engine": "plan",
        "tier": "starter",
        "pock": 10,
        "usd_hint": 0.03,
        "sell": True,
        "headless": True,
        "description": "Step plans, risks, milestones — no code writes.",
        "system": "PLAN ONLY. No code. Ordered steps, risks, acceptance criteria.",
        "examples": ["Plan a multi-user seat billing system"],
    },
    "coder": {
        "id": "coder",
        "name": "Coder",
        "role": "Implementation agent (Codex)",
        "engine": "codex",
        "tier": "pro",
        "pock": 50,
        "usd_hint": 0.15,
        "sell": True,
        "headless": True,
        "description": "Writes and edits real code via Codex CLI.",
        "system": "Implement the smallest correct change. Summarize files touched.",
        "examples": ["Add health endpoint version field"],
    },
    "grok_coder": {
        "id": "grok_coder",
        "name": "Grok Coder",
        "role": "Implementation agent (Grok)",
        "engine": "grok",
        "tier": "pro",
        "pock": 40,
        "usd_hint": 0.10,
        "sell": True,
        "headless": True,
        "description": "Writes code via Grok CLI (--single).",
        "system": "Ship a useful code change. Report paths and verification.",
        "examples": ["Fix auth header handling in client"],
    },
    "reviewer": {
        "id": "reviewer",
        "name": "Reviewer",
        "role": "Code / design review",
        "engine": "plan",
        "tier": "pro",
        "pock": 18,
        "usd_hint": 0.05,
        "sell": True,
        "headless": True,
        "description": "Bug/risk review, severity ranked findings.",
        "system": (
            "You are a senior code reviewer. Output: severity (P0-P3), finding, "
            "evidence, fix. No fluff."
        ),
        "examples": ["Review this auth flow for privilege escalation"],
    },
    "security": {
        "id": "security",
        "name": "Security",
        "role": "Threat model + security audit",
        "engine": "plan",
        "tier": "pro",
        "pock": 25,
        "usd_hint": 0.08,
        "sell": True,
        "headless": True,
        "description": "Threat model, abuse cases, hardening checklist.",
        "system": (
            "Security engineer. Cover: authn/z, injection, secrets, supply chain, "
            "network exposure. Output STRIDE-style threats + mitigations."
        ),
        "examples": ["Threat model a public agent API with API keys"],
    },
    "writer": {
        "id": "writer",
        "name": "Writer",
        "role": "Docs / product copy",
        "engine": "plan",
        "tier": "starter",
        "pock": 12,
        "usd_hint": 0.04,
        "sell": True,
        "headless": True,
        "description": "README, API docs, launch copy — clear and shippable.",
        "system": "Technical writer. Clear, scannable markdown. No filler.",
        "examples": ["Write API quickstart for POCKET AI API"],
    },
    "ops": {
        "id": "ops",
        "name": "Ops",
        "role": "Shell / diagnostics on host",
        "engine": "shell",
        "tier": "pro",
        "pock": 8,
        "usd_hint": 0.02,
        "sell": True,
        "headless": True,
        "description": "Safe shell diagnostics on the POCKET host.",
        "system": "Run only the diagnostic requested. Paste command output.",
        "examples": ["python --version && git status"],
    },
    "data": {
        "id": "data",
        "name": "Data",
        "role": "Tables, metrics, analysis",
        "engine": "plan",
        "tier": "starter",
        "pock": 14,
        "usd_hint": 0.04,
        "sell": True,
        "headless": True,
        "description": "Structure numbers into tables and recommendations.",
        "system": "Data analyst. Tables first, then insights and caveats.",
        "examples": ["Estimate monthly cost for 20 API seats at 100 jobs/day"],
    },
    "architect": {
        "id": "architect",
        "name": "Architect",
        "role": "System design",
        "engine": "plan",
        "tier": "pro",
        "pock": 22,
        "usd_hint": 0.07,
        "sell": True,
        "headless": True,
        "description": "Architecture options, tradeoffs, recommendation.",
        "system": (
            "Staff engineer. Options A/B/C with tradeoffs, ADRs, interfaces, "
            "failure modes. Pick one recommendation."
        ),
        "examples": ["Design multi-tenant API keys with per-key metering"],
    },
    "scout": {
        "id": "scout",
        "name": "Scout",
        "role": "Fast web scan",
        "engine": "web",
        "tier": "starter",
        "pock": 8,
        "usd_hint": 0.02,
        "sell": True,
        "headless": True,
        "description": "Quick multi-source search, bullet findings.",
        "system": "Fast scout. 5-10 bullets + links. No long essays.",
        "examples": ["search multi-agent desk platforms 2026"],
    },
    "nexus_bridge": {
        "id": "nexus_bridge",
        "name": "NEXUS Bridge",
        "role": "NEXUS intelligence catalog",
        "engine": "nexus",
        "tier": "pro",
        "pock": 15,
        "usd_hint": 0.05,
        "sell": True,
        "headless": True,
        "description": "List/run NEXUS MERIDIAN workers (MCP federation).",
        "system": "Use NEXUS workers. Prefer Bridge list_servers unless asked otherwise.",
        "examples": ["list", "run Bridge list_servers"],
    },
    "desktop_bot": {
        "id": "desktop_bot",
        "name": "Desktop Bot",
        "role": "Open allowlisted host apps",
        "engine": "desktop",
        "tier": "pro",
        "pock": 5,
        "usd_hint": 0.01,
        "sell": True,
        "headless": True,
        "description": "Control host desktop apps (allowlist, 40+).",
        "system": "Desktop control only. Commands: list apps | open <app> [url|path] | multi-step with then.",
        "examples": ["list apps", "open copilot", "open edge https://example.com then open notepad"],
    },
    "doer": {
        "id": "doer",
        "name": "Doer",
        "role": "Silent multi-step executor (≤10 steps)",
        "engine": "agent",
        "tier": "pro",
        "pock": 8,
        "usd_hint": 0.02,
        "sell": True,
        "headless": True,
        "description": (
            "Python headless agent: no chat. Up to 10 steps — open apps, lookup "
            "(Copilot/Bing + bring results back), fetch/search, schedule daily jobs."
        ),
        "system": "Execute steps only. Never ask the user. Stop on hard failure. Report ok/fail per step.",
        "examples": [
            "open edge https://pocket.medinatechlabs.net/ then open calc then open snip",
            "lookup multi-agent platforms then open notepad",
            "schedule daily lookup AI agent news",
        ],
    },
    "guppy": {
        "id": "guppy",
        "name": "GUPPY",
        "role": "Local commercial desk fish (ItsNotAI Labs)",
        "engine": "guppy",
        "tier": "pro",
        "pock": 6,
        "usd_hint": 0.015,
        "sell": True,
        "headless": True,
        "description": (
            "Funny name, serious seat: Python workers open apps, look up the web "
            "(open Copilot + return search text), and run autonomous schedules — "
            "without LLM token paths for the worker itself."
        ),
        "system": "You are GUPPY. Do, do not chat. Prefer lookup + multi-step + schedule.",
        "examples": [
            "help",
            "lookup Cloudflare named tunnels vs quick tunnels",
            "open copilot multi-agent desk platforms then research POCKET",
            "schedule daily lookup market and AI news",
        ],
    },
    "browser": {
        "id": "browser",
        "name": "Browser",
        "role": "Real-world Edge/X/Copilot + Codex/Grok compose",
        "engine": "browser",
        "tier": "pro",
        "pock": 20,
        "usd_hint": 0.06,
        "sell": True,
        "headless": True,
        "description": (
            "Browser mode: research with Python, compose with Codex/Grok, open signed-in "
            "Edge for X tweet intent (you click Post). Windows Copilot app + web Copilot."
        ),
        "system": "Browser mode. Emit [[POCKET …]] tags. Never claim auto-post to X.",
        "examples": [
            "help",
            "lookup multi-agent platforms then write a tweet for https://x.com/ItsnotAILabs",
            "open copilot",
            "open copilot web AI agents",
            "tweet Shipping POCKET Browser mode from the lab",
        ],
    },
    "capture": {
        "id": "capture",
        "name": "Capture",
        "role": "Screenshot / snip paste-back",
        "engine": "capture",
        "tier": "starter",
        "pock": 3,
        "usd_hint": 0.01,
        "sell": True,
        "headless": True,
        "description": "Screen capture returned to desk as image (no folder save). Open Snipping Tool.",
        "system": "Capture only. Prefer paste-back base64 + clipboard.",
        "examples": ["screenshot", "snip"],
    },
    "repos": {
        "id": "repos",
        "name": "Repos",
        "role": "Folders, zip, git, GitHub via gh",
        "engine": "repos",
        "tier": "pro",
        "pock": 10,
        "usd_hint": 0.03,
        "sell": True,
        "headless": True,
        "description": "Local workspaces, zip, git init, list/open GitHub repos (signed-in gh).",
        "system": "Repos/GitHub agent. Prefer gh; never ask for passwords.",
        "examples": ["open my 5 repos", "list repos", "new repo demo-pocket", "gh status"],
    },
    "copilot_intro": {
        "id": "copilot_intro",
        "name": "Copilot Intro",
        "role": "Introduce persona to Windows Copilot",
        "engine": "copilot",
        "tier": "starter",
        "pock": 4,
        "usd_hint": 0.01,
        "sell": True,
        "headless": True,
        "description": "Open Windows Copilot + clipboard intro as POCKET/persona (Ctrl+V if needed).",
        "system": "Introduce only. Open app + clipboard.",
        "examples": ["introduce", "introduce as Grok: we ship multi-agent desks"],
    },
    "squad": {
        "id": "squad",
        "name": "Squad",
        "role": "Multi-agent chain: scout → plan → code brief",
        "engine": "squad",
        "tier": "enterprise",
        "pock": 80,
        "usd_hint": 0.25,
        "sell": True,
        "headless": True,
        "description": "Runs researcher + planner (+ optional coder brief) headlessly.",
        "system": "Coordinate specialist agents. Merge into one ship brief.",
        "examples": ["Ship a public AI API with keys and metering"],
    },
    "router": {
        "id": "router",
        "name": "Router",
        "role": "Pick the best agent for a task",
        "engine": "router",
        "tier": "starter",
        "pock": 3,
        "usd_hint": 0.01,
        "sell": True,
        "headless": True,
        "description": "Classifies task → agent id (no heavy run).",
        "system": "Route only. Return agent_id + reason.",
        "examples": ["I need a threat model for our login"],
    },
}


def list_agents(*, sellable_only: bool = False) -> List[Dict[str, Any]]:
    out = []
    for a in AGENTS.values():
        if sellable_only and not a.get("sell"):
            continue
        out.append(_public(a))
    return sorted(out, key=lambda x: (x.get("tier") or "", x.get("id") or ""))


def get_agent(agent_id: str) -> Optional[Dict[str, Any]]:
    a = AGENTS.get((agent_id or "").strip().lower())
    return _public(a) if a else None


def _public(a: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": a["id"],
        "name": a["name"],
        "role": a["role"],
        "engine": a["engine"],
        "tier": a["tier"],
        "pock": a["pock"],
        "usd_hint": a["usd_hint"],
        "sell": a.get("sell", True),
        "headless": True,
        "description": a["description"],
        "examples": a.get("examples") or [],
    }


def route_task(task: str) -> Dict[str, Any]:
    """Cheap keyword router — headless, no LLM required."""
    t = (task or "").lower()
    rules = [
        (["threat", "security", "vuln", "cve", "auth bypass"], "security"),
        (["review", "pr review", "code review", "bug"], "reviewer"),
        (["architect", "design system", "tradeoff", "adr"], "architect"),
        (["readme", "docs", "copy", "changelog", "blog"], "writer"),
        (["cost", "metric", "table", "forecast", "budget"], "data"),
        (["search ", "research ", "fetch ", "what is"], "researcher"),
        (["scout", "quick look", "scan"], "scout"),
        (["open notepad", "list apps", "open edge", "desktop", "open copilot"], "desktop_bot"),
        ([" then ", "multi-step", "doer", "do:"], "doer"),
        (["guppy", "schedule daily", "lookup "], "guppy"),
        (["tweet", "x.com", "browser mode", "open copilot web"], "browser"),
        (["nexus", "bridge list", "mcp"], "nexus_bridge"),
        (["implement", "fix ", "write code", "refactor", "ship"], "coder"),
        (["plan ", "roadmap", "milestone"], "planner"),
        (["dir", "git status", "python --", "diagnose"], "ops"),
        (["squad", "end to end", "full pipeline"], "squad"),
    ]
    for keys, aid in rules:
        if any(k in t for k in keys):
            a = AGENTS[aid]
            return {"ok": True, "agent_id": aid, "name": a["name"], "reason": f"matched {keys[0]}", "agent": _public(a)}
    return {
        "ok": True,
        "agent_id": "planner",
        "name": "Planner",
        "reason": "default safe plan-only route",
        "agent": _public(AGENTS["planner"]),
    }


def build_prompt(agent_id: str, task: str, *, extra: str = "") -> Tuple[str, str, Dict[str, Any]]:
    """Return (engine_mode, prompt, agent_meta)."""
    a = AGENTS.get((agent_id or "").strip().lower())
    if not a:
        raise ValueError(f"unknown agent: {agent_id}")
    engine = a["engine"]
    task = (task or "").strip()
    if engine == "router":
        return "router", task, a
    if engine == "squad":
        return "squad", task, a
    if engine == "web":
        # Prefer research/search command forms the web engine understands
        low = task.lower()
        if not (low.startswith("search ") or low.startswith("fetch ") or low.startswith("research ")):
            task = f"research {task}" if a["id"] == "researcher" else f"search {task}"
        return "web", task, a
    if engine in (
        "shell", "desktop", "nexus", "agent", "doer", "guppy", "browser",
        "capture", "repos", "copilot",
    ):
        if engine in ("agent", "doer"):
            return "agent", task, a
        return engine, task, a
    # plan / codex / grok
    prompt = (
        f"[Headless agent: {a['name']} ({a['id']})]\n"
        f"Role: {a['role']}\n"
        f"Instructions: {a['system']}\n"
    )
    if extra:
        prompt += f"Context:\n{extra[:4000]}\n"
    prompt += f"\nTask:\n{task}"
    return engine if engine in ("codex", "grok", "plan", "shell") else "plan", prompt, a


def run_headless(
    agent_id: str,
    task: str,
    *,
    workspace: str = "workspace",
    cwd: str = "",
    sync: bool = True,
    extra: str = "",
    client_device: Optional[dict] = None,
    api_key_id: str = "",
) -> Dict[str, Any]:
    """Run a headless agent. sync=True waits for result (API product default)."""
    from pocket.jobs import create_job, get as get_job
    from pocket.tokenomics import burn
    from pocket.worker import process_one

    aid = (agent_id or "").strip().lower()
    if aid == "router":
        routed = route_task(task)
        try:
            burn("api_route", meta={"agent": "router"})
        except Exception:
            burn("job_ask", meta={"agent": "router"})
        return {
            "ok": True,
            "agent_id": "router",
            "mode": "router",
            "result": routed,
            "sync": True,
            "at": time.time(),
        }

    if aid == "squad":
        return _run_squad(task, workspace=workspace, cwd=cwd, client_device=client_device, api_key_id=api_key_id)

    engine, prompt, meta = build_prompt(aid, task, extra=extra)
    try:
        burn("api_agent", meta={"agent": aid, "engine": engine, "pock_list": meta.get("pock")}, amount=int(meta.get("pock") or 10))
    except Exception:
        try:
            burn("job_ask", meta={"agent": aid})
        except Exception:
            pass

    job = create_job(
        prompt,
        name=f"agent:{aid}",
        mode=engine if engine not in ("router", "squad") else "plan",
        workspace=workspace,
        cwd=cwd,
        session_id="",
        message_id="",
        client_device=client_device,
    )
    job["agent_id"] = aid
    job["api_key_id"] = api_key_id or ""
    from pocket.jobs import save

    save(job)

    if not sync:
        process_one()
        return {
            "ok": True,
            "agent_id": aid,
            "job_id": job["id"],
            "status": "queued",
            "mode": engine,
            "poll": f"/v1/ai/jobs/{job['id']}",
            "agent": _public(meta),
        }

    # Drain until done (bounded)
    deadline = time.time() + 300
    process_one()
    while time.time() < deadline:
        j = get_job(job["id"])
        if not j:
            break
        st = j.get("status")
        if st in ("done", "failed"):
            return {
                "ok": st == "done" and not j.get("error"),
                "agent_id": aid,
                "job_id": j["id"],
                "status": st,
                "mode": j.get("mode") or engine,
                "engine": j.get("engine"),
                "result": j.get("result") or "",
                "error": j.get("error") or "",
                "agent": _public(meta),
                "pock": meta.get("pock"),
                "at": time.time(),
            }
        process_one()
        time.sleep(0.35)
    j = get_job(job["id"]) or job
    return {
        "ok": False,
        "agent_id": aid,
        "job_id": j.get("id"),
        "status": j.get("status") or "timeout",
        "result": j.get("result") or "",
        "error": j.get("error") or "timeout waiting for headless agent",
        "agent": _public(meta),
    }


def _run_squad(
    task: str,
    *,
    workspace: str,
    cwd: str,
    client_device: Optional[dict],
    api_key_id: str,
) -> Dict[str, Any]:
    """Scout → plan headless chain (no auto-code unless task says implement)."""
    steps = []
    scout = run_headless(
        "scout",
        task,
        workspace=workspace,
        cwd=cwd,
        sync=True,
        client_device=client_device,
        api_key_id=api_key_id,
    )
    steps.append({"step": "scout", **{k: scout.get(k) for k in ("ok", "job_id", "status", "result", "error")}})
    research_snip = (scout.get("result") or "")[:6000]
    plan = run_headless(
        "planner",
        task,
        workspace=workspace,
        cwd=cwd,
        sync=True,
        extra=f"Scout findings:\n{research_snip}",
        client_device=client_device,
        api_key_id=api_key_id,
    )
    steps.append({"step": "planner", **{k: plan.get(k) for k in ("ok", "job_id", "status", "result", "error")}})

    want_code = any(w in (task or "").lower() for w in ("implement", "code", "ship", "fix", "build"))
    code_step = None
    if want_code:
        code_step = run_headless(
            "coder",
            f"Based on this plan, implement the smallest slice:\n{(plan.get('result') or '')[:5000]}\n\nOriginal: {task}",
            workspace=workspace,
            cwd=cwd,
            sync=True,
            client_device=client_device,
            api_key_id=api_key_id,
        )
        steps.append({"step": "coder", **{k: code_step.get(k) for k in ("ok", "job_id", "status", "result", "error")}})

    merged = {
        "task": task,
        "squad": ["scout", "planner"] + (["coder"] if code_step else []),
        "scout": (scout.get("result") or "")[:8000],
        "plan": (plan.get("result") or "")[:12000],
        "code": (code_step.get("result") if code_step else None),
    }
    return {
        "ok": True,
        "agent_id": "squad",
        "status": "done",
        "mode": "squad",
        "result": json.dumps(merged, indent=2, default=str)[:45000],
        "steps": steps,
        "agent": _public(AGENTS["squad"]),
        "pock": AGENTS["squad"]["pock"],
        "at": time.time(),
    }


def pricing_catalog() -> Dict[str, Any]:
    by_tier: Dict[str, List[Dict[str, Any]]] = {}
    for a in list_agents(sellable_only=True):
        by_tier.setdefault(a["tier"], []).append(
            {"id": a["id"], "name": a["name"], "pock": a["pock"], "usd_hint": a["usd_hint"]}
        )
    return {
        "product": "POCKET AI API",
        "unit": "POCK",
        "currency_hint": "USD list price is marketing hint only; bill via POCK or subscription seats",
        "tiers": {
            "starter": {"monthly_usd_hint": 29, "includes": "researcher, planner, writer, data, scout, router"},
            "pro": {"monthly_usd_hint": 99, "includes": "coder, grok_coder, reviewer, security, architect, ops, nexus, desktop"},
            "enterprise": {"monthly_usd_hint": 299, "includes": "squad + volume + multi-key + SLA"},
        },
        "agents": by_tier,
        "endpoints": [
            "GET /v1/ai",
            "GET /v1/ai/agents",
            "POST /v1/ai/agents/{id}/run",
            "POST /v1/ai/chat",
            "POST /v1/ai/route",
            "POST /v1/ai/jobs",
            "GET /v1/ai/jobs/{id}",
            "POST /v1/ai/keys",
            "GET /v1/ai/keys",
            "GET /v1/ai/usage",
        ],
        "auth": "Authorization: Bearer sk_pocket_…  OR  X-API-Key: sk_pocket_…",
    }
