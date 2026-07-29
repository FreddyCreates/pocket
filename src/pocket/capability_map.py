"""Live host capability map — what AIs can actually do *right now*.

Injected into AI workspace so agents stop guessing and re-probing.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List


def build_capability_map() -> Dict[str, Any]:
    caps: Dict[str, Any] = {
        "schema": "pocket.capability-map.v1",
        "at": time.time(),
        "at_h": time.strftime("%Y-%m-%d %H:%M:%S"),
        "engines": {},
        "embodiment": {},
        "infra": {},
        "safety": {},
        "ai_workspace": {},
        "tips": [],
    }
    try:
        from pocket.executor import available_engines

        eng = available_engines()
        caps["engines"] = {
            "codex": bool(eng.get("codex")),
            "grok": bool(eng.get("grok")),
            "claude": bool(eng.get("claude")),
            "shell": True,
            "wsl": bool(eng.get("wsl")),
            "desktop": True,
            "browser": True,
            "woa": True,
            "paths": {
                "codex": eng.get("codex_path"),
                "grok": eng.get("grok_path"),
                "claude": eng.get("claude_path"),
            },
        }
    except Exception as e:
        caps["engines"] = {"error": str(e)}

    try:
        from pocket.desktop import list_apps

        apps = list_apps() if callable(list_apps) else []
        if isinstance(apps, dict):
            apps = apps.get("apps") or apps.get("items") or []
        caps["embodiment"]["apps"] = [
            (a.get("id") if isinstance(a, dict) else str(a)) for a in (apps or [])[:40]
        ]
        caps["embodiment"]["app_count"] = len(apps or [])
    except Exception:
        try:
            from pocket.safety import ALLOWED_APPS

            caps["embodiment"]["apps"] = sorted(list(ALLOWED_APPS))[:40]
            caps["embodiment"]["app_count"] = len(ALLOWED_APPS)
        except Exception as e:
            caps["embodiment"]["error"] = str(e)

    caps["embodiment"].update(
        {
            "screenshot": True,
            "vision": True,
            "browser_agent": True,
            "offload_queue": True,
            "proof_packs": True,
            "ui_click": True,
            "clipboard": True,
        }
    )

    try:
        from pocket.mesh_disk import mesh_root

        caps["infra"]["mesh_root"] = str(mesh_root())
        caps["infra"]["agent_bus"] = True
        caps["infra"]["channels"] = ["freq-0", "freq-coding", "freq-4"]
    except Exception as e:
        caps["infra"]["mesh"] = str(e)

    try:
        from pocket.ai_workspace import ROOT as AW

        caps["ai_workspace"]["root"] = str(AW)
        caps["ai_workspace"]["auto_inject"] = True
    except Exception:
        pass

    try:
        from pocket.learn import list_learned

        skills = list_learned()
        caps["infra"]["learned_skills"] = len(skills)
    except Exception:
        caps["infra"]["learned_skills"] = 0

    try:
        from pocket.offload_queue import list_tasks

        caps["infra"]["offload_queued"] = len(list_tasks(status="queued", limit=50))
        caps["infra"]["offload_done"] = len(list_tasks(status="done", limit=50))
    except Exception:
        pass

    caps["safety"] = {
        "shell_allowlist": True,
        "app_allowlist": True,
        "url_policy": True,
        "audit_log": str((__import__("pathlib").Path.home() / ".pocket" / "safety.log")),
        "paper_money_only_for_parallax": True,
    }

    caps["tips"] = [
        "Prefer /v1/offload for multi-step real-world work — free the chat turn",
        "Read AI_WORKSPACE CONTEXT before listing the repo",
        "Use mesh bus artifacts for peer handoffs",
        "Check capability map before probing engines",
        "Screenshot + proof pack after desktop actions",
    ]
    return caps


def capability_markdown(cmap: Dict[str, Any] | None = None) -> str:
    c = cmap or build_capability_map()
    eng = c.get("engines") or {}
    emb = c.get("embodiment") or {}
    inf = c.get("infra") or {}
    lines = [
        "# Host capability map (live)",
        "",
        f"Updated: {c.get('at_h')}",
        "",
        "## Engines",
        f"- Codex: {eng.get('codex')} · Grok: {eng.get('grok')} · Claude: {eng.get('claude')}",
        f"- Desktop/Browser/WOA: on",
        "",
        "## Embodiment",
        f"- Apps allowlisted: {emb.get('app_count', 0)}",
        f"- Screenshot/vision/offload/proof: yes",
        f"- Sample apps: {', '.join((emb.get('apps') or [])[:12])}",
        "",
        "## Infra",
        f"- Mesh: {inf.get('mesh_root', '—')}",
        f"- Learned skills: {inf.get('learned_skills', 0)}",
        f"- Offload queued/done: {inf.get('offload_queued', 0)}/{inf.get('offload_done', 0)}",
        "",
        "## Tips",
    ]
    for t in c.get("tips") or []:
        lines.append(f"- {t}")
    return "\n".join(lines)
