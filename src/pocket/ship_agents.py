"""Ship subagents — marketing + demo + Electron checklist on the mesh.

MARKETING / DEMO / ELECTRON leave artifacts on E:POCKET_MESH so SHIP_HEADLESS
and peers can consume one-pagers, demo scripts, and desktop ship checklists.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from pocket.mesh_disk import ensure_agent, leave_artifact, send_message

AGENTS: Dict[str, Dict[str, str]] = {
    "MARKETING": {
        "role": "marketing one-pager",
        "focus": "promise, audience, proof points, call-to-action",
    },
    "DEMO": {
        "role": "demo script",
        "focus": "live walkthrough beats, talk track, success criteria",
    },
    "ELECTRON": {
        "role": "electron / desktop ship",
        "focus": "tray install, packaging, auto-start, API keys, real verify",
    },
}

SHIP_AGENTS = AGENTS


def list_ship_agents() -> List[Dict[str, Any]]:
    out = []
    for aid, meta in AGENTS.items():
        ensure_agent(aid, role="ship")
        out.append({"id": aid, **meta, "status": "ready", "source": "ship"})
    return out


def bootstrap_ship_agents() -> Dict[str, Any]:
    ids = []
    for aid in AGENTS:
        ids.append(ensure_agent(aid, role="ship"))
    return {
        "ok": True,
        "registered": len(ids),
        "agents": [i["id"] for i in ids],
        "roles": {a: AGENTS[a]["role"] for a in AGENTS},
    }


def _one_pager(prompt: str) -> str:
    return (
        "# POCKET — Marketing one-pager\n\n"
        f"**Brief:** {prompt or 'ship beta'}\n\n"
        "## Promise\n"
        "Code and instruct suite agents from your phone. Queue lands on the PC "
        "for Grok / terminal / away-watch.\n\n"
        "## Who\n"
        "- Solo builders who live on phone + desk\n"
        "- Labs needing host co-pilot + mesh subagents\n"
        "- Teams shipping beta demos without a full mobile rewrite\n\n"
        "## Proof\n"
        "- Product nav: Overview · Desktop · API · Studio\n"
        "- @dispatch mesh agents (DESIGN · FORGE · SHIP · …)\n"
        "- E: virtual mesh disk artifacts + headless heartbeats\n"
        "- Fusion sense + RFE + phone product shell\n\n"
        "## CTA\n"
        "1. `python -m pocket serve --port 8787`\n"
        "2. Open phone → LAN:8787 · run `@DEMO` walkthrough\n"
        "3. Ship desktop via `@ELECTRON` checklist\n\n"
        f"— MARKETING @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


def _demo_script(prompt: str) -> str:
    return (
        "# POCKET — Demo script\n\n"
        f"**Focus:** {prompt or 'beta live demo'}\n\n"
        "## Setup (2 min)\n"
        "1. Boot host: `Start-POCKET.ps1` or `python -m pocket serve --port 8787`\n"
        "2. Confirm mesh hook armed · headless pack alive\n"
        "3. Phone or second browser on same LAN\n\n"
        "## Beats\n"
        "| # | Beat | Talk track | Success |\n"
        "|---|------|------------|----------|\n"
        "| 1 | Overview | \"Phone is the remote; PC is the brain.\" | Product shell loads |\n"
        "| 2 | Composer @ | \"@DESIGN polish · @SHIP checklist.\" | Dispatch chips appear |\n"
        "| 3 | Desktop | \"Host sees the screen and opens apps.\" | Sense/screenshot ok |\n"
        "| 4 | Mesh | \"Artifacts land on E:POCKET_MESH.\" | leave_artifact visible |\n"
        "| 5 | Studio | \"Same path becomes the marketing clip.\" | Studio/phone view |\n\n"
        "## Close\n"
        "- Recap: mesh agents · headless ship · phone remote\n"
        "- Hand off one-pager (`@MARKETING`) + Electron checklist (`@ELECTRON`)\n\n"
        f"— DEMO @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


def _electron_checklist(prompt: str) -> str:
    items = [
        "Desktop install script / tray launch (Install-POCKET-Desktop.ps1)",
        "Window chrome loads product shell (not blank WebView)",
        "Auto-start / AlwaysOn optional path verified",
        "API /developers keys path works offline-host",
        "Mesh root E:\\POCKET_MESH writable from packaged host",
        "Headless pack + @SHIP_HEADLESS checklist green",
        "Deep link / tray menu: open UI · status · quit",
        "Real: serve · watch · one @DEMO beat · one artifact",
        "Icons + name POCKET in Start menu / tray",
        "Uninstall path documented",
    ]
    body = (
        "# Electron / desktop ship checklist\n\n"
        f"**Prompt:** {prompt or 'package desktop'}\n\n"
        + "\n".join(f"- [ ] {c}" for c in items)
        + f"\n\n— ELECTRON @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    )
    return body


def run_ship_agent(name: str, prompt: str) -> Dict[str, Any]:
    n = (name or "MARKETING").upper()
    if n not in AGENTS:
        n = "MARKETING"
    ensure_agent(n, role="ship")
    p = (prompt or "").strip() or "ship beta"

    if n == "DEMO":
        content = _demo_script(p)
        fname = "demo_script.md"
    elif n == "ELECTRON":
        content = _electron_checklist(p)
        fname = "electron_ship_checklist.md"
    else:
        content = _one_pager(p)
        fname = "marketing_one_pager.md"

    art = leave_artifact(
        n, fname, content, notify=["ARCHON", "SHIP_HEADLESS"]
    )
    send_message(n, "ARCHON", f"ship pass complete: {n}", kind="ship", channel="freq-4")
    send_message(
        n, "SHIP_HEADLESS", f"{fname} ready", kind="ship", channel="freq-4"
    )
    return {
        "ok": True,
        "agent": n,
        "role": AGENTS[n]["role"],
        "desc": AGENTS[n]["focus"],
        "artifact": art,
        "filename": fname,
        "channel": "freq-4",
        "prompt": p[:500],
    }


def dispatch_ship(
    prompt: str,
    *,
    agents: Optional[List[str]] = None,
    from_agent: str = "USER",
    channel: str = "freq-4",
) -> Dict[str, Any]:
    bootstrap_ship_agents()
    text = (prompt or "").strip()
    targets = [a.upper() for a in (agents or list(AGENTS)) if a.upper() in AGENTS]
    if not targets:
        targets = ["MARKETING"]
    results = []
    for name in targets:
        send_message(from_agent, name, text, channel=channel, kind="dispatch")
        results.append(run_ship_agent(name, text))
    return {
        "ok": all(r.get("ok") for r in results),
        "dispatched": len(results),
        "agents": targets,
        "results": results,
        "mesh": True,
        "channel": channel,
    }
