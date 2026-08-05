"""GUPPY — local commercial desk fish.

Funny name, serious job: a Python instance that lives on the operator PC and
swims through apps + web without needing chat or LLM tokens for the path itself.

Guppy does:
  · multi-step desktop (open apps, Edge+URL)
  · look up queries (open Copilot/Bing + bring Python web results back)
  · schedule autonomous daily/hourly fetches (background Python workers)
  · report in markdown — no questions asked

Claimed by ItsNotAI Labs / Medina Tech Labs as the commercial local seat agent.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

PRODUCT = "GUPPY"
PRODUCT_FULL = "GUPPY Local Commercial Desk Agent"
TAGLINE = "Small fish. Big desk. Opens apps, looks things up, brings them back."
LAB = "ItsNotAI Labs"
COMPANY = "Medina Tech Labs"
MAX_STEPS = 10


def identity() -> Dict[str, Any]:
    return {
        "id": "guppy",
        "product": PRODUCT,
        "full": PRODUCT_FULL,
        "tagline": TAGLINE,
        "lab": LAB,
        "company": COMPANY,
        "max_steps": MAX_STEPS,
        "token_path": "python-worker",  # not LLM token burns for desktop/web fetch path
        "capabilities": [
            "open_allowlisted_apps",
            "edge_url_navigate",
            "copilot_lookup_open",
            "python_web_search_bring_back",
            "multi_step_upto_10",
            "scheduled_background_fetch",
            "daily_autonomous_jobs",
            "desktop_co_pilot_pattern",
        ],
        "engines_beyond_code": {
            "codex": [
                "code edit",
                "repo health",
                "file ops in workspace",
                "test/real verification via shell tools",
                "multi-turn resume per POCKET session",
            ],
            "grok": [
                "planning",
                "research synthesis",
                "coding when CLI present",
                "handoff packages",
            ],
            "claude": [
                "review",
                "docs",
                "code when CLI present",
            ],
            "guppy_python": [
                "desktop control (zero LLM)",
                "web search/fetch (zero LLM)",
                "schedules",
                "multi-step doer",
            ],
        },
    }


def run_guppy(prompt: str, *, cwd: str = "", job: Optional[Dict] = None) -> Tuple[str, str, str]:
    """Main entry — silent commercial worker."""
    text = (prompt or "").strip()
    low = text.lower()

    if low in ("", "help", "who are you", "identity", "?"):
        idn = identity()
        lines = [
            f"# {PRODUCT} — {TAGLINE}",
            "",
            f"**{PRODUCT_FULL}** · {LAB} / {COMPANY}",
            "",
            "I do not chat. I **do**. Up to "
            f"**{MAX_STEPS} steps**. Desktop + web via **Python workers** (not LLM tokens).",
            "",
            "### Commands",
            "- `open copilot` · `open edge https://…` · `list apps`",
            "- `lookup <query>` — open Copilot/Bing **and** bring Python search results back",
            "- `research <topic>` — web research brief (Python fetch)",
            "- multi-step: `open edge https://a.com then open notepad then lookup climate data`",
            "- `schedule daily lookup market news` · `schedule list` · `schedule cancel <id>`",
            "- `status` — schedules + identity",
            "",
            "### Browser mode (separate desk box)",
            "Use **+ Browser** for Codex/Grok + signed-in Edge/X tweets + Windows Copilot.",
            "Example: look up topic then write a tweet for https://x.com/you",
            "",
            "### Why Guppy",
            "Commercial local instance on **your** PC: open the same apps a human would,",
            "walk the internet, return text. Background jobs fetch on a clock.",
            "",
            "```json",
            json.dumps({k: idn[k] for k in ("id", "product", "lab", "company", "max_steps", "capabilities")}, indent=2),
            "```",
        ]
        return "\n".join(lines), "", "guppy"

    if low.startswith("status") or low in ("ping", "alive"):
        from pocket.autonomy import list_schedules, runner_status

        return (
            f"## GUPPY status\n\n"
            f"- runner: `{runner_status()}`\n"
            f"- schedules: {len(list_schedules())}\n"
            f"- max_steps: {MAX_STEPS}\n"
            f"- path: python-worker (desktop/web)\n",
            "",
            "guppy",
        )

    if low.startswith("schedule"):
        from pocket.autonomy import handle_schedule_command

        return handle_schedule_command(text)

    # Default: multi-step doer with Guppy brand + lookup skills
    from pocket.step_agent import run_step_agent

    result, err, eng = run_step_agent(text, cwd=cwd, job=job, max_steps=MAX_STEPS)
    header = f"[engine=guppy · {LAB} · steps≤{MAX_STEPS} · python-worker]\n\n"
    return header + result, err, "guppy"
