"""POCKET AI API — sellable multi-agent HTTP product.

OpenAPI-style surface for third parties, apps, and automations.
Auth: API key (sk_pocket_…) or desk login.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from pocket.agents import get_agent, list_agents, pricing_catalog, route_task, run_headless
from pocket.api_keys import create_key, list_keys, record_usage, revoke_key, usage_for


PRODUCT = {
    "name": "POCKET AI API",
    "version": "1.0.0",
    "tagline": "Headless multi-agent AI you can sell — research, plan, code, secure, squad.",
    "host_model": "Runs on the operator POCKET host (or your deployment). Meter with POCK + API keys.",
}


def product_manifest() -> Dict[str, Any]:
    return {
        "ok": True,
        "product": PRODUCT,
        "pricing": pricing_catalog(),
        "agents": list_agents(sellable_only=True),
        "quickstart": {
            "1_create_key": "POST /v1/ai/keys  {\"name\":\"prod\",\"tier\":\"pro\"}",
            "2_list_agents": "GET /v1/ai/agents",
            "3_run_agent": "POST /v1/ai/agents/researcher/run  {\"task\":\"…\"}",
            "4_chat": "POST /v1/ai/chat  {\"messages\":[{\"role\":\"user\",\"content\":\"…\"}],\"agent\":\"planner\"}",
            "5_async": "POST /v1/ai/jobs  {\"agent\":\"coder\",\"task\":\"…\"} then GET /v1/ai/jobs/{id}",
            "auth": "Authorization: Bearer sk_pocket_…",
        },
        "sell": {
            "model": "Subscription seats + metered POCK per agent call",
            "starter_usd": 29,
            "pro_usd": 99,
            "enterprise_usd": 299,
            "notes": [
                "API keys are the product surface for third-party apps",
                "Headless agents do not need the desk UI",
                "Heavy agents (coder/squad) map to real Codex/Grok on host",
            ],
        },
    }


def chat_complete(
    messages: List[Dict[str, str]],
    *,
    agent: str = "planner",
    workspace: str = "workspace",
    api_key_id: str = "",
    sync: bool = True,
    cwd: str = "",
    inject_wiki: bool = True,
) -> Dict[str, Any]:
    """OpenAI-shaped chat completion over a headless agent.

    Infinite Wiki inject (default on for coding agents): attaches Profile Cards
    for paths/symbols so third-party API clients get hierarchical code context
    without saturating context windows.
    """
    # Flatten messages into a task
    parts = []
    last_user = ""
    for m in messages or []:
        role = (m.get("role") or "user").lower()
        content = (m.get("content") or "").strip()
        if content:
            parts.append(f"{role}: {content}")
            if role == "user":
                last_user = content
    task = "\n".join(parts).strip()
    if not task:
        return {"ok": False, "error": "messages required"}

    agent = (agent or "planner").strip().lower()
    if agent == "auto":
        routed = route_task(task)
        agent = routed.get("agent_id") or "planner"

    wiki_meta: Dict[str, Any] = {"injected": False}
    coding = agent in {
        "coder",
        "grok_coder",
        "architect",
        "planner",
        "squad",
        "security",
        "reviewer",
        "data",
        "researcher",
    }
    if inject_wiki and coding:
        try:
            from pocket.infinite_wiki import inject_wiki_context

            base = last_user or task
            injected = inject_wiki_context(base, cwd=cwd or workspace or "")
            if injected != base:
                wiki_meta = {"injected": True, "chars": len(injected)}
                # Keep multi-turn envelope but enrich the working task
                task = injected if not last_user else task.replace(last_user, injected, 1)
                if last_user and last_user not in task:
                    task = injected
        except Exception as e:
            wiki_meta = {"injected": False, "error": str(e)[:120]}

    res = run_headless(
        agent,
        task,
        workspace=workspace,
        sync=sync,
        api_key_id=api_key_id,
    )
    text = ""
    if isinstance(res.get("result"), dict):
        import json

        text = json.dumps(res["result"], indent=2, default=str)
    else:
        text = str(res.get("result") or res.get("error") or "")

    meta = get_agent(agent) or {}
    pock = int(meta.get("pock") or 10)
    if api_key_id:
        record_usage(api_key_id, agent=agent, pock=pock)

    # OpenAI-compatible envelope (subset) + pocket fields
    return {
        "ok": res.get("ok", True),
        "id": res.get("job_id") or f"chat-{int(time.time())}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": f"pocket-{agent}",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": "stop" if res.get("ok") else "error",
            }
        ],
        "usage": {
            "pock": pock,
            "agent": agent,
            "prompt_hint": len(task) // 4,
            "completion_hint": len(text) // 4,
        },
        "pocket": {
            "agent": meta,
            "job_id": res.get("job_id"),
            "status": res.get("status"),
            "infinite_wiki": wiki_meta,
            "error": res.get("error") or "",
            "steps": res.get("steps"),
        },
    }


def run_agent_api(
    agent_id: str,
    task: str,
    *,
    workspace: str = "workspace",
    sync: bool = True,
    api_key_id: str = "",
    extra: str = "",
    cwd: str = "",
    inject_wiki: bool = True,
) -> Dict[str, Any]:
    wiki_meta: Dict[str, Any] = {"injected": False}
    task_use = task
    if inject_wiki and (agent_id or "").lower() in {
        "coder",
        "grok_coder",
        "architect",
        "planner",
        "squad",
        "security",
        "reviewer",
    }:
        try:
            from pocket.infinite_wiki import inject_wiki_context

            inj = inject_wiki_context(task, cwd=cwd or workspace or "")
            if inj != task:
                task_use = inj
                wiki_meta = {"injected": True, "chars": len(inj)}
        except Exception as e:
            wiki_meta = {"injected": False, "error": str(e)[:120]}
    res = run_headless(
        agent_id,
        task_use,
        workspace=workspace,
        sync=sync,
        extra=extra,
        api_key_id=api_key_id,
    )
    meta = get_agent(agent_id) or {}
    pock = int(res.get("pock") or meta.get("pock") or 0)
    if api_key_id:
        record_usage(api_key_id, agent=agent_id, pock=pock)
    if isinstance(res, dict):
        res = {**res, "infinite_wiki": wiki_meta}
    return res


def create_api_key_admin(body: dict, owner: str = "pocket") -> Dict[str, Any]:
    return create_key(
        name=body.get("name") or "api",
        owner=body.get("owner") or owner,
        tier=body.get("tier") or "pro",
        monthly_quota=int(body.get("monthly_quota") or 10_000),
    )


def keys_list(owner: str = "") -> Dict[str, Any]:
    return {"ok": True, "keys": list_keys(owner=owner)}


def keys_revoke(key_id: str) -> Dict[str, Any]:
    return revoke_key(key_id)


def usage(key_id: str = "", owner: str = "") -> Dict[str, Any]:
    return usage_for(key_id, owner=owner)
