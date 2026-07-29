"""Wrapped Orchestrator Agent (WOA) for POCKET host.

Routes goals across:
  - mine  — local deterministic POCKET/PARALLAX helpers
  - grok  — Grok coding agent
  - codex — Codex coding agent

Crypto / blockchain native ship surface. Paper/testnet-first.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List


def classify_goal(goal: str) -> Dict[str, Any]:
    g = (goal or "").lower()
    if re.search(r"\b(trade|order|paper desk|fill|settlement)\b", g):
        return {"domain": "trade", "engines": ["mine", "codex"]}
    if re.search(r"\b(deploy|release|ship|canister)\b", g):
        return {"domain": "deploy", "engines": ["codex", "grok", "mine"]}
    if re.search(r"\b(maintain|fix|patch|health)\b", g):
        return {"domain": "maintain", "engines": ["grok", "codex"]}
    if re.search(r"\b(create|scaffold|build|implement)\b", g):
        return {"domain": "create", "engines": ["codex", "grok"]}
    if re.search(r"\b(crypto|encrypt|sha|pq|aes|post.?quantum)\b", g):
        return {"domain": "crypto", "engines": ["mine", "codex"]}
    if re.search(r"\b(blockchain|chain|ledger|icp|eth|sol|btc)\b", g):
        return {"domain": "blockchain", "engines": ["mine", "grok", "codex"]}
    if re.search(r"\b(work|production|alpha)\b", g):
        return {"domain": "work", "engines": ["grok", "codex", "mine"]}
    return {"domain": "answer", "engines": ["mine", "grok"]}


def build_plan(goal: str) -> Dict[str, Any]:
    cls = classify_goal(goal)
    domain = cls["domain"]
    engines: List[str] = list(cls["engines"])
    steps: List[Dict[str, Any]] = [
        {
            "id": "mine-0",
            "engine": "mine",
            "domain": domain,
            "intent": f"Local posture + inventory: {(goal or '')[:160]}",
            "status": "planned",
        }
    ]
    if "codex" in engines:
        steps.append(
            {
                "id": "codex-1",
                "engine": "codex",
                "domain": domain,
                "intent": f"Code-first implement: {(goal or '')[:200]}",
                "status": "planned",
            }
        )
    if "grok" in engines:
        steps.append(
            {
                "id": "grok-2",
                "engine": "grok",
                "domain": domain,
                "intent": f"Long-horizon ship/verify: {(goal or '')[:200]}",
                "status": "planned",
            }
        )
    steps.append(
        {
            "id": "ensemble-9",
            "engine": "ensemble",
            "domain": "answer",
            "intent": "Merge into operator summary",
            "status": "planned",
        }
    )
    return {
        "schema": "parallax.wrapped-orchestrator.v1",
        "goal": (goal or "").strip() or "(empty)",
        "domain": domain,
        "engines": engines,
        "steps": steps,
        "created_at": time.time(),
        "public_posture": "paper_testnet_first",
    }


def _mine_result(step: Dict[str, Any], plan: Dict[str, Any]) -> str:
    lines = [
        f"WOA · mine · {step.get('domain')}",
        "Posture: paper/testnet-first (no live money).",
        f"Goal: {plan.get('goal')}",
        f"Domain: {plan.get('domain')}",
        "Caffeine limits are NOT ours — multi-language, multi-cloud, websockets,",
        "external DBs, and third-party auth are first-class on the PARALLAX stack.",
        f"Intent: {step.get('intent')}",
    ]
    return "\n".join(lines)


def run_wrapped(
    goal: str,
    *,
    remote: bool = True,
    cwd: str = "",
    job_id: str = "",
) -> Dict[str, Any]:
    """
    Execute WOA plan. mine/ensemble local; codex/grok via executor when remote.
    """
    plan = build_plan(goal)
    artifacts: List[str] = []
    for step in plan["steps"]:
        eng = step["engine"]
        step["status"] = "running"
        t0 = time.time()
        try:
            if eng in ("mine", "ensemble"):
                step["result"] = _mine_result(step, plan)
                step["status"] = "done"
                artifacts.append(f"mine:{step['id']}")
            elif eng in ("codex", "grok") and remote:
                from pocket.executor import run_job

                prompt = (
                    f"TASK: {step['intent']}\n"
                    "You are a WOA worker under the Wrapped Orchestrator.\n"
                    "Prefer concrete code over research essays. Paper/testnet first.\n"
                )
                result, err, engine = run_job(
                    {
                        "mode": eng,
                        "prompt": prompt,
                        "cwd": cwd,
                        "workspace": "parallax",
                        "id": job_id or "",
                    }
                )
                step["result"] = (result or "")[-8000:]
                step["status"] = "done" if not err else "failed"
                step["error"] = err or ""
                step["engine_used"] = engine
                if not err:
                    artifacts.append(f"{eng}:{step['id']}")
            else:
                step["result"] = f"{eng} deferred (local-only)."
                step["status"] = "skipped"
        except Exception as e:
            step["status"] = "failed"
            step["result"] = str(e)
        step["ms"] = int((time.time() - t0) * 1000)

    done = sum(1 for s in plan["steps"] if s.get("status") == "done")
    summary = (
        f"Wrapped Orchestrator · {done}/{len(plan['steps'])} steps · "
        f"domain={plan['domain']} · paper/testnet-first"
    )
    return {
        "ok": done > 0,
        "plan": plan,
        "summary": summary,
        "artifacts": artifacts,
        "message": summary,
    }


def run_woa_job(prompt: str, cwd: str = "", job: Dict | None = None) -> tuple:
    job = job or {}
    r = run_wrapped(
        prompt,
        remote=True,
        cwd=cwd or job.get("cwd") or "",
        job_id=job.get("id") or "",
    )
    body = r.get("summary", "") + "\n\n" + str(r.get("plan", {}))[:4000]
    return body, ("" if r.get("ok") else r.get("message", "woa failed")), "wrapped-orch"
