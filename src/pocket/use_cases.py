"""Real product use cases — POCKET vs Emergent and beyond.

Each use case is executable: starts a managed multi-agent build loop
that plans, codes, tests, and ships into a real workspace on the host
(or tenant sandbox), not a chat-only demo.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Emergent offers: conversation→full-stack, multi-agent team, custom agents,
# test/troubleshoot, deploy, GitHub, visual review.
# POCKET matches each and adds sovereign host, WSL, phone, mesh, Novae, isolation.

USE_CASES: List[Dict[str, Any]] = [
    {
        "id": "fullstack_web_app",
        "title": "Full-stack web app from prompt",
        "emergent": "vibe-code full-stack apps in English",
        "pocket_more": "Runs on YOUR host · real files · WSL tools · no vendor lock-in cloud-only",
        "loop": "ship",
        "agents": ["PLANNER", "DESIGN", "FRONTEND", "BACKEND", "TESTER", "DEPLOYER"],
        "template": "web_static",
        "prompt_hint": "Build a landing page + contact form API stub for a local services business",
    },
    {
        "id": "saas_dashboard",
        "title": "SaaS dashboard (auth shell + metrics)",
        "emergent": "multi-agent frontend + backend + auth",
        "pocket_more": "Founder host desktop + real Git vault; market seats sandboxed",
        "loop": "ship",
        "agents": ["PLANNER", "DESIGN", "FRONTEND", "BACKEND", "SECURITY", "TESTER"],
        "template": "dashboard",
        "prompt_hint": "Admin dashboard with login shell, KPI cards, and mock API",
    },
    {
        "id": "api_microservice",
        "title": "JSON API microservice",
        "emergent": "backend + test agents",
        "pocket_more": "Codex/Grok Novae + WSL native pytest on host",
        "loop": "ship",
        "agents": ["PLANNER", "BACKEND", "TESTER", "SHIP"],
        "template": "api_flask",
        "prompt_hint": "REST API with health, items CRUD, and pytest suite",
    },
    {
        "id": "cli_tool",
        "title": "CLI tool ship",
        "emergent": "partial (web-first)",
        "pocket_more": "First-class host shell + WSL packaging",
        "loop": "ship",
        "agents": ["PLANNER", "BACKEND", "TESTER", "SHIP"],
        "template": "cli",
        "prompt_hint": "Python CLI that processes a folder of files and writes a report",
    },
    {
        "id": "agent_inside_product",
        "title": "Custom agent inside your product",
        "emergent": "custom agents with tools + sub-agents",
        "pocket_more": "Mesh identity + platform workspace + host hands (founder)",
        "loop": "agent_build",
        "agents": ["PLANNER", "AGENTSMITH", "TESTER"],
        "template": "custom_agent",
        "prompt_hint": "Support agent that answers FAQ and escalates to human",
    },
    {
        "id": "github_sync_ship",
        "title": "Code → git vault → export",
        "emergent": "GitHub sync (paid plans)",
        "pocket_more": "Sovereign git inside POCKET + zip export without cloud bill",
        "loop": "ship",
        "agents": ["PLANNER", "BACKEND", "SHIP", "GIT"],
        "template": "web_static",
        "prompt_hint": "Ship a mini site and commit to sovereign git",
    },
    {
        "id": "test_troubleshoot",
        "title": "Autonomous test + fix loop",
        "emergent": "testing & troubleshooting agents",
        "pocket_more": "Retry loops with caps, WSL pytest, proof artifacts on mesh",
        "loop": "fix_fix",
        "agents": ["TESTER", "FIXER", "REVIEWER"],
        "template": "api_flask",
        "prompt_hint": "Generate failing tests then fix until green",
    },
    {
        "id": "mobile_remote_build",
        "title": "Build from phone on the go",
        "emergent": "web/mobile apps (their cloud)",
        "pocket_more": "Phone desk drives host builders while you are away",
        "loop": "ship",
        "agents": ["PLANNER", "FRONTEND", "BACKEND", "TESTER"],
        "template": "web_static",
        "prompt_hint": "Phone-triggered build of a status board page",
    },
    {
        "id": "research_to_product",
        "title": "Research → product brief → code",
        "emergent": "planning agent",
        "pocket_more": "Grok Novae research + DESIGN mesh + real code artifacts",
        "loop": "ship",
        "agents": ["RESEARCH", "PLANNER", "DESIGN", "FRONTEND"],
        "template": "web_static",
        "prompt_hint": "Research multi-agent desks and ship a comparison landing page",
    },
    {
        "id": "host_automation",
        "title": "Real-world host automation",
        "emergent": "not on your PC",
        "pocket_more": "Desktop/browser/capture/offload — Emergent cannot touch your machine",
        "loop": "host_ops",
        "agents": ["PLANNER", "DOER", "OCULUS"],
        "template": "ops",
        "prompt_hint": "Open Edge to docs hub and screenshot proof",
    },
    {
        "id": "wsl_native_build",
        "title": "Native Linux build via WSL",
        "emergent": "managed Linux containers (their cloud)",
        "pocket_more": "First-class WSL agent on YOUR Windows host",
        "loop": "wsl_build",
        "agents": ["PLANNER", "WSL", "TESTER"],
        "template": "cli",
        "prompt_hint": "Create a Python package under ~/pocket-wsl and run tests",
    },
    {
        "id": "multi_agent_swarm",
        "title": "Managed swarm until finished",
        "emergent": "coordinated multi-agent architecture",
        "pocket_more": "Persistent loop manager + retries + stop conditions + mission bus",
        "loop": "ship",
        "agents": ["ARCHON", "PLANNER", "FRONTEND", "BACKEND", "TESTER", "SHIP"],
        "template": "dashboard",
        "prompt_hint": "Coordinate a full team to ship a KPI dashboard app",
    },
]


PARITY = {
    "schema": "pocket.emergent_parity.v1",
    "competitor": "Emergent (emergent.sh) — agentic vibe-coding app builder",
    "pocket_stance": (
        "Match conversation→code multi-agent shipping, then surpass with sovereign host, "
        "WSL, phone remote, mesh subagents, Novae hands, founder/market isolation."
    ),
    "matrix": [
        {"feature": "Prompt → full-stack app", "emergent": True, "pocket": True, "note": "build_loop ship"},
        {"feature": "Specialized multi-agents", "emergent": True, "pocket": True, "note": "PLANNER…DEPLOYER + Latin/mesh"},
        {"feature": "Custom agents + tools + sub-agents", "emergent": True, "pocket": True, "note": "custom_agents"},
        {"feature": "Test & troubleshoot loops", "emergent": True, "pocket": True, "note": "test_fix loop"},
        {"feature": "Deploy / live preview", "emergent": True, "pocket": True, "note": "static deploy + /desk preview"},
        {"feature": "GitHub / git", "emergent": True, "pocket": True, "note": "sovereign git + export"},
        {"feature": "Runs on your PC (sovereign)", "emergent": False, "pocket": True, "note": "host power"},
        {"feature": "Phone remote desk", "emergent": False, "pocket": True, "note": "/phone"},
        {"feature": "Native WSL Linux agent", "emergent": False, "pocket": True, "note": "wsl_agent"},
        {"feature": "Market seat isolation", "emergent": False, "pocket": True, "note": "tenants never founder disk"},
        {"feature": "Desktop embodiment / capture", "emergent": False, "pocket": True, "note": "host ops"},
        {"feature": "Mesh hashed subagent bus", "emergent": False, "pocket": True, "note": "mesh_disk"},
        {"feature": "Novae Grok/Codex instances", "emergent": False, "pocket": True, "note": "novae"},
        {"feature": "Vendor lock-in required", "emergent": True, "pocket": False, "note": "self-host research license"},
    ],
    "use_case_count": len(USE_CASES),
}


def list_use_cases() -> List[Dict[str, Any]]:
    return list(USE_CASES)


def get_use_case(uid: str) -> Dict[str, Any] | None:
    uid = (uid or "").strip().lower()
    for u in USE_CASES:
        if u["id"] == uid:
            return dict(u)
    return None


def parity_report() -> Dict[str, Any]:
    pocket_wins = sum(1 for r in PARITY["matrix"] if r["pocket"] and not r["emergent"])
    both = sum(1 for r in PARITY["matrix"] if r["pocket"] and r["emergent"])
    return {
        **PARITY,
        "score": {
            "shared_capabilities": both,
            "pocket_only_advantages": pocket_wins,
            "use_cases_executable": len(USE_CASES),
        },
    }
