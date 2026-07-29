"""NEXUS product integration — MERIDIAN workers inside POCKET."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.safety import audit
from pocket.tokenomics import burn

def _pick_nexus_root() -> Path:
    env = os.environ.get("NEXUS_ROOT")
    if env:
        return Path(env)
    for p in (
        Path.home() / "OneDrive" / "nexus",
        Path.home() / "nexus",
        Path("C:/Users/Medin/OneDrive/nexus"),
    ):
        if p.is_dir() and ((p / "src").is_dir() or (p / "nexus").is_dir()):
            return p
    return Path.home() / "OneDrive" / "nexus"


NEXUS_ROOT = _pick_nexus_root()

WORKER_HELP = {
    "Bridge": "Federated MCP catalog (Slack, Tavily, Linear, …) — list_servers",
    "Archon": "GitHub intelligence — list_repos, index_repo (needs GITHUB_TOKEN)",
    "Scribe": "Drafts/articles — never auto-publish",
    "Cipher": "Security audits / threat models",
    "Forge": "ML pipelines / artifacts",
    "Herald": "Analytics / competitive / radar",
    "Lumen": "Cross-repo search / knowledge graph",
    "Weaver": "Build tools / prompts / skills",
    "Hermes": "Lab messaging / presence",
}


def nexus_available() -> Dict[str, Any]:
    ok = NEXUS_ROOT.is_dir() and ((NEXUS_ROOT / "src").is_dir() or (NEXUS_ROOT / "nexus").is_dir())
    return {
        "ok": ok,
        "product": "NEXUS Universal Intelligence",
        "root": str(NEXUS_ROOT),
        "workers": list(WORKER_HELP.keys()),
        "worker_help": WORKER_HELP,
        "monetization": {
            "model": "NEXUS credits via POCK burns on tool calls",
            "subscription_hook": "Refill POCK / sell NEXUS seats",
            "free_layer": "list + Bridge catalog",
            "paid_layer": "Scribe/Archon/Cipher/Forge heavy tasks",
        },
        "github_token": bool(os.environ.get("GITHUB_TOKEN")),
        "anthropic": bool(os.environ.get("ANTHROPIC_API_KEY")),
    }


def _ensure_path() -> None:
    root = str(NEXUS_ROOT.resolve())
    if root not in sys.path:
        sys.path.insert(0, root)


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                return ex.submit(asyncio.run, coro).result(timeout=180)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def list_capabilities() -> Dict[str, Any]:
    info = nexus_available()
    if not info["ok"]:
        return {"ok": False, "error": f"NEXUS not found at {NEXUS_ROOT}. Clone/install nexus under OneDrive/nexus.", **info}
    try:
        _ensure_path()
        from nexus.workers import Bridge

        async def go():
            return await Bridge().register().run("list_servers", {})

        result = _run_async(go())
        data = result.to_dict() if hasattr(result, "to_dict") else result
        try:
            burn("nexus_tool", meta={"task": "list_servers"})
        except Exception:
            burn("job_ask", meta={"nexus": "list"})
        audit("nexus_list", ok=True)
        return {"ok": True, "result": data, **{k: info[k] for k in ("workers", "worker_help", "monetization", "root")}}
    except Exception as e:
        audit("nexus_list_fail", error=str(e))
        return {"ok": False, "error": str(e), **info}


def run_worker(worker: str, task: str, params: Optional[dict] = None) -> Dict[str, Any]:
    info = nexus_available()
    if not info["ok"]:
        return {"ok": False, "error": f"NEXUS not found at {NEXUS_ROOT}"}
    worker = (worker or "Bridge").strip()
    task = (task or "list_servers").strip()
    params = params or {}

    heavy = {"scribe", "archon", "cipher", "forge", "weaver"}
    try:
        if worker.lower() in heavy:
            burn("job_codex" if worker.lower() in ("forge", "scribe") else "job_claude", meta={"nexus": worker, "task": task})
        else:
            burn("nexus_tool", meta={"nexus": worker, "task": task})
    except Exception:
        burn("job_ask", meta={"nexus": worker})

    try:
        _ensure_path()
        from nexus import workers as W

        cls_map = {
            "bridge": W.Bridge,
            "archon": W.Archon,
            "scribe": W.Scribe,
            "cipher": W.Cipher,
            "forge": W.Forge,
            "herald": W.Herald,
            "lumen": W.Lumen,
            "weaver": W.Weaver,
            "hermes": W.Hermes,
        }
        cls = cls_map.get(worker.lower())
        if not cls:
            return {"ok": False, "error": f"Unknown worker {worker}", "workers": list(WORKER_HELP)}

        async def go():
            return await cls().register().run(task, params)

        result = _run_async(go())
        data = result.to_dict() if hasattr(result, "to_dict") else result
        audit("nexus_run", worker=worker, task=task, success=True)
        return {"ok": True, "worker": worker, "task": task, "help": WORKER_HELP.get(worker), "result": data}
    except Exception as e:
        audit("nexus_run_fail", worker=worker, task=task, error=str(e))
        return {"ok": False, "error": str(e), "worker": worker, "task": task}


def run_nexus_job(prompt: str) -> Tuple[str, str, str]:
    text = (prompt or "").strip()
    low = text.lower()

    if low in ("", "list", "workers", "status", "help"):
        caps = list_capabilities()
        body = (
            "# NEXUS (product)\n\n"
            "Universal intelligence workers inside POCKET.\n\n"
            f"**Root:** `{caps.get('root')}`\n"
            f"**Ready:** {caps.get('ok')}\n\n"
            "## Workers\n"
        )
        for w, h in WORKER_HELP.items():
            body += f"- **{w}** — {h}\n"
        body += (
            "\n## Commands\n"
            "- `list` — catalog + Bridge servers\n"
            "- `run Bridge list_servers`\n"
            "- `run Archon list_repos {}`\n"
            "- `run Scribe …` (drafts; never auto-publish)\n\n"
            "## Monetization\n"
            "Heavy workers burn POCK (NEXUS credit hook). Sell refills/subscriptions.\n\n"
        )
        if caps.get("ok"):
            body += "```json\n" + json.dumps(caps.get("result") or caps, indent=2, default=str)[:25000] + "\n```\n"
        else:
            body += f"**Error:** {caps.get('error')}\n"
        err = "" if caps.get("ok") else (caps.get("error") or "nexus unavailable")
        return body, err, "nexus"

    if low.startswith("run "):
        rest = text[4:].strip()
        parts = rest.split(None, 2)
        worker = parts[0] if parts else "Bridge"
        task = parts[1] if len(parts) > 1 else "list_servers"
        params: dict = {}
        if len(parts) > 2:
            try:
                params = json.loads(parts[2])
            except Exception:
                params = {"q": parts[2]}
        res = run_worker(worker, task, params)
        dump = json.dumps(res, indent=2, default=str)[:45000]
        if res.get("ok"):
            return f"# NEXUS {worker}.{task}\n\n```json\n{dump}\n```", "", "nexus"
        return dump, res.get("error") or "nexus failed", "nexus"

    # natural language → Bridge list
    res = list_capabilities()
    return json.dumps(res, indent=2, default=str)[:30000], ("" if res.get("ok") else res.get("error") or ""), "nexus"
