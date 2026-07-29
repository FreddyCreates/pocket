"""Embedded POCKET tokenomics — local ledger + session cost model (product economy)."""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket"
LEDGER = ROOT / "tokenomics_ledger.json"
_lock = Lock()

# Internal unit: POCK (platform credits). Not a public chain token yet — embedded product economy.
# Designed so users *use* credits heavily as they open agents and run jobs.
UNIT = "POCK"

# Cost table (credits). Tuned so multi-agent use is the main sink.
COSTS = {
    "session_open": 5,       # open a new agent/terminal tab
    "session_idle_hour": 1,  # soft hold cost (accounted on close/sample)
    "job_shell": 2,
    "job_wsl": 3,
    "job_ask": 1,
    "job_grok_handoff": 8,   # plan package write
    "job_grok_exec": 40,     # real grok -p run
    "job_codex": 50,         # real coding agent
    "job_claude": 45,
    "deploy_start": 15,      # local deploy
    "deploy_hour": 5,
    "research_pull": 12,     # full plan+research package
    "nexus_tool": 15,        # NEXUS worker call (subscription/credits hook)
    "desktop_open": 2,
    "web_fetch": 5,
    "web_search": 8,
    "api_route": 1,          # headless router
    "api_agent": 10,         # default API agent call (overridden by agent pock)
    "api_chat": 12,          # chat completion wrapper
    "api_key_create": 0,
}

# Rough USD mapping for *display* (research / cost awareness) — not billing
# Based on typical agent SaaS order-of-magnitude, not a quote.
USD_HINTS = {
    "job_codex": 0.15,       # ~mid agent turn estimate
    "job_claude": 0.12,
    "job_grok_exec": 0.10,
    "job_shell": 0.0,
    "job_wsl": 0.0,
    "job_ask": 0.0,
    "job_grok_handoff": 0.0,
    "session_open": 0.0,
    "deploy_start": 0.0,
    "research_pull": 0.0,
}

DEFAULT_GRANT = 10_000  # starting credits so product feels usable


def _default_state() -> Dict[str, Any]:
    return {
        "schema": "pocket.tokenomics.v1",
        "unit": UNIT,
        "balance": DEFAULT_GRANT,
        "lifetime_minted": DEFAULT_GRANT,
        "lifetime_burned": 0,
        "events": [],
        "created_at": time.time(),
        "updated_at": time.time(),
        "thesis": {
            "name": "POCK embedded credits",
            "purpose": "Meter multi-agent compute, deploys, and research pulls on the desk",
            "sinks": list(COSTS.keys()),
            "sources": ["signup_grant", "manual_topup", "future_chain_bridge"],
            "note": "Local ledger first. Chain token (IPO/TGE) is design-only until markets ship.",
        },
    }


def _load() -> Dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    if LEDGER.exists():
        try:
            return json.loads(LEDGER.read_text(encoding="utf-8"))
        except Exception:
            pass
    st = _default_state()
    _save(st)
    return st


def _save(st: Dict[str, Any]) -> None:
    st["updated_at"] = time.time()
    # keep last 200 events
    ev = st.get("events") or []
    if len(ev) > 200:
        st["events"] = ev[-200:]
    LEDGER.write_text(json.dumps(st, indent=2), encoding="utf-8")


def snapshot() -> Dict[str, Any]:
    with _lock:
        st = _load()
        return {
            "ok": True,
            "unit": st.get("unit", UNIT),
            "balance": st.get("balance", 0),
            "lifetime_minted": st.get("lifetime_minted", 0),
            "lifetime_burned": st.get("lifetime_burned", 0),
            "costs": COSTS,
            "usd_hints": USD_HINTS,
            "thesis": st.get("thesis"),
            "recent": list(reversed((st.get("events") or [])[-12:])),
            "docs": {
                "tokenomics_paper": "/v1/docs/tokenomics",
                "usage_cost_paper": "/v1/docs/usage-cost",
                "platform_paper": "/v1/docs/platform",
            },
        }


def burn(kind: str, *, meta: Optional[Dict[str, Any]] = None, amount: Optional[int] = None) -> Dict[str, Any]:
    amt = int(amount if amount is not None else COSTS.get(kind, 1))
    with _lock:
        st = _load()
        bal = int(st.get("balance") or 0)
        # soft floor: allow negative display as debt so UX never hard-blocks builders
        st["balance"] = bal - amt
        st["lifetime_burned"] = int(st.get("lifetime_burned") or 0) + amt
        ev = {
            "id": f"tx-{uuid.uuid4().hex[:10]}",
            "type": "burn",
            "kind": kind,
            "amount": amt,
            "balance_after": st["balance"],
            "usd_hint": USD_HINTS.get(kind, 0),
            "meta": meta or {},
            "at": time.time(),
        }
        st.setdefault("events", []).append(ev)
        _save(st)
        return {"ok": True, **ev, "unit": UNIT}


def mint(amount: int, *, reason: str = "topup") -> Dict[str, Any]:
    amount = max(0, int(amount))
    with _lock:
        st = _load()
        st["balance"] = int(st.get("balance") or 0) + amount
        st["lifetime_minted"] = int(st.get("lifetime_minted") or 0) + amount
        ev = {
            "id": f"tx-{uuid.uuid4().hex[:10]}",
            "type": "mint",
            "kind": reason,
            "amount": amount,
            "balance_after": st["balance"],
            "at": time.time(),
        }
        st.setdefault("events", []).append(ev)
        _save(st)
        return {"ok": True, **ev, "unit": UNIT}


def cost_for_mode(mode: str, *, grok_exec: bool = False) -> str:
    m = (mode or "").lower()
    if m == "codex":
        return "job_codex"
    if m == "claude":
        return "job_claude"
    if m == "shell":
        return "job_shell"
    if m == "wsl":
        return "job_wsl"
    if m == "ask":
        return "job_ask"
    if m == "plan":
        return "job_ask"
    if m == "web":
        return "web_search"
    if m == "nexus":
        return "nexus_tool"
    if m == "desktop":
        return "desktop_open"
    if m == "grok":
        return "job_grok_exec" if grok_exec else "job_grok_handoff"
    if m in ("researcher", "scout", "planner", "reviewer", "security", "writer", "data", "architect", "squad", "router"):
        return "api_agent"
    return "job_shell"


def estimate_session_cost(open_sessions: int, concurrent_jobs: int = 1) -> Dict[str, Any]:
    """Research-facing estimate for open multi-agent desks."""
    open_cost = open_sessions * COSTS["session_open"]
    heavy = concurrent_jobs * COSTS["job_codex"]
    light = concurrent_jobs * COSTS["job_shell"]
    usd_heavy = concurrent_jobs * USD_HINTS["job_codex"]
    return {
        "open_sessions": open_sessions,
        "credits_to_open_all": open_cost,
        "credits_if_all_run_codex": open_cost + heavy,
        "credits_if_all_run_shell": open_cost + light,
        "usd_hint_if_all_codex": round(usd_heavy, 2),
        "note": "POCK is embedded platform credits. USD hints estimate external agent SaaS cost only.",
        "unit": UNIT,
        "cost_table": COSTS,
    }


def cost_analysis_20_users() -> Dict[str, Any]:
    """
    Analysis only — not a quote. Assumptions for 20 operators on shared/self-host style desk.
    """
    users = 20
    # light: 5 agent jobs/user/day; heavy: 25
    light_jobs = users * 5 * 22  # workdays/month
    heavy_jobs = users * 25 * 22
    # mix 60% codex-class, 30% shell, 10% grok
    def usd(jobs: int) -> float:
        codex = jobs * 0.6 * USD_HINTS["job_codex"]
        grok = jobs * 0.1 * USD_HINTS["job_grok_exec"]
        return round(codex + grok, 2)

    def pock(jobs: int) -> int:
        return int(
            jobs * 0.6 * COSTS["job_codex"]
            + jobs * 0.3 * COSTS["job_shell"]
            + jobs * 0.1 * COSTS["job_grok_exec"]
            + users * 3 * COSTS["session_open"] * 22  # ~3 sessions/day
        )

    # Infra if you host for 20 (one beefy PC or small VPS cluster) — rough
    infra = {
        "self_host_one_pc": "Your current model: $0–50/mo power; not true multi-tenant",
        "small_vps_or_gpu_box": "$40–200/mo depending on region/CPU",
        "cloudflare_tunnel_named": "Free–$7+/mo depending on CF plan",
        "multi_tenant_auth_db": "Engineering cost; not free",
    }
    return {
        "users": users,
        "assumptions": {
            "workdays_per_month": 22,
            "light_jobs_per_user_day": 5,
            "heavy_jobs_per_user_day": 25,
            "mix": "60% Codex-class, 30% shell, 10% Grok",
            "usd_per_codex_job_hint": USD_HINTS["job_codex"],
            "usd_per_grok_job_hint": USD_HINTS["job_grok_exec"],
        },
        "light_month": {
            "agent_jobs": light_jobs,
            "usd_hint_llm": usd(light_jobs),
            "pock_burn": pock(light_jobs),
            "usd_hint_monthly": f"${usd(light_jobs)}–${usd(light_jobs)+80}",
        },
        "heavy_month": {
            "agent_jobs": heavy_jobs,
            "usd_hint_llm": usd(heavy_jobs),
            "pock_burn": pock(heavy_jobs),
            "usd_hint_monthly": f"${usd(heavy_jobs)}–${usd(heavy_jobs)+200}",
        },
        "infra_notes": infra,
        "honest": (
            "Today POCKET is single-operator multi-agent. 20 users needs auth, isolation, "
            "and per-user API keys or pooled billing. LLM cost is the main variable; POCK is internal meter."
        ),
        "your_personal_cost_now": (
            "You pay existing Codex/Grok subscriptions + electricity. "
            "POCK does not bill USD. Parallel sessions multiply LLM spend when they run, not when idle."
        ),
    }
