"""Skills packs for Latin workers — multi-skill agents (not single-job).

Each worker has many skills. Skills are callable by id for demos, API, and ARCHON.
"""

from __future__ import annotations

from typing import Any, Dict, List

# skill_id → definition
SKILLS: Dict[str, Dict[str, Any]] = {
    # PORTARIUS
    "open_app": {"worker": "PORTARIUS", "desc": "Open allowlisted desktop app"},
    "open_edge_url": {"worker": "PORTARIUS", "desc": "Open URL in signed-in Edge"},
    "open_spacex": {"worker": "PORTARIUS", "desc": "Open spacex.com"},
    "open_tradingview_web": {"worker": "PORTARIUS", "desc": "Open tradingview.com"},
    "open_tradingview_app": {"worker": "PORTARIUS", "desc": "Open TradingView desktop"},
    "open_metatrader": {"worker": "PORTARIUS", "desc": "Open MetaTrader 5"},
    "open_cursor": {"worker": "PORTARIUS", "desc": "Open Cursor"},
    "open_antigravity": {"worker": "PORTARIUS", "desc": "Open Antigravity"},
    "close_edge": {"worker": "PORTARIUS", "desc": "Close Edge windows only"},
    # SCRUTATOR / REPOSITOR
    "github_open_top5": {"worker": "REPOSITOR", "desc": "Open first 5 GitHub repos in Edge"},
    "github_explore_tabs": {"worker": "REPOSITOR", "desc": "Click/open all major GitHub project tabs"},
    "github_research": {"worker": "SCRUTATOR", "desc": "Full research bring-back on a repo"},
    "clone_https": {"worker": "REPOSITOR", "desc": "Shallow HTTPS clone under workspaces"},
    # NAVIGATOR / SCRIPTOR
    "tweet_research": {"worker": "NAVIGATOR", "desc": "Open X compose with research text"},
    "research_to_tweet": {"worker": "SCRIPTOR", "desc": "Compose tweet from research"},
    # CONSILIARIUS
    "copilot_chat_send": {"worker": "CONSILIARIUS", "desc": "Paste into Copilot chat and Enter"},
    "copilot_search_bar": {"worker": "CONSILIARIUS", "desc": "Win search / Copilot search skill (fallback)"},
    # TABELLARIUS / OCULUS / SPECULUM
    "outlook_draft_research": {"worker": "TABELLARIUS", "desc": "Draft email with research body"},
    "notepad_hello": {"worker": "PORTARIUS", "desc": "Notepad + type hello world message"},
    "explorer_new_file": {"worker": "PORTARIUS", "desc": "Explorer + create a file"},
    "calc_run": {"worker": "PORTARIUS", "desc": "Calculator + run a sum"},
    "powershell_run": {"worker": "PORTARIUS", "desc": "PowerShell + run a command"},
    "screenshot": {"worker": "OCULUS", "desc": "Screenshot paste-back"},
    "record_start": {"worker": "SPECULUM", "desc": "Start screen record"},
    "record_stop": {"worker": "SPECULUM", "desc": "Stop screen record"},
    # ARCHON
    "grand_demo": {"worker": "ARCHON", "desc": "Legacy multi-surface demo"},
    "focused_demo": {"worker": "ARCHON", "desc": "Real one-GitHub + record + discrete skills"},
    "github_one_page": {"worker": "REPOSITOR", "desc": "ONE GitHub page, scroll/UI only"},
    "antigravity_explore": {"worker": "PORTARIUS", "desc": "Open Antigravity and explore UI"},
    "github_desktop_peek": {"worker": "REPOSITOR", "desc": "GitHub Desktop peek"},
    "email_hi_world": {"worker": "TABELLARIUS", "desc": "Draft hi-to-the-world email"},
    "research_interest": {"worker": "SCRUTATOR", "desc": "What interests us in a repo"},
    "record_start": {"worker": "SPECULUM", "desc": "Start full-screen record"},
    "record_stop": {"worker": "SPECULUM", "desc": "Stop record and save"},
}

WORKER_SKILLS: Dict[str, List[str]] = {
    "ARCHON": ["grand_demo", "github_open_top5", "github_explore_tabs", "github_research", "tweet_research",
               "outlook_draft_research", "copilot_chat_send", "open_tradingview_web", "open_tradingview_app",
               "open_metatrader", "calc_run", "powershell_run", "close_edge", "record_start", "record_stop"],
    "HYDRA": ["github_open_top5", "open_cursor", "open_antigravity", "copilot_chat_send", "calc_run"],
    "SCRUTATOR": ["github_research", "clone_https"],
    "SCRIPTOR": ["research_to_tweet"],
    "PORTARIUS": ["open_app", "open_edge_url", "open_spacex", "open_tradingview_web", "open_tradingview_app",
                  "open_metatrader", "open_cursor", "open_antigravity", "close_edge", "notepad_hello",
                  "explorer_new_file", "calc_run", "powershell_run"],
    "OCULUS": ["screenshot"],
    "SPECULUM": ["record_start", "record_stop"],
    "REPOSITOR": ["github_open_top5", "github_explore_tabs", "clone_https"],
    "CONSILIARIUS": ["copilot_chat_send", "copilot_search_bar"],
    "TABELLARIUS": ["outlook_draft_research"],
    "NAVIGATOR": ["tweet_research", "open_spacex", "open_tradingview_web"],
    "GUPPY": ["open_app", "github_open_top5", "screenshot"],
}


def skills_for(worker: str) -> List[Dict[str, Any]]:
    w = (worker or "").upper()
    ids = WORKER_SKILLS.get(w) or []
    return [{"id": i, **SKILLS[i]} for i in ids if i in SKILLS]


def all_skills() -> List[Dict[str, Any]]:
    return [{"id": k, **v} for k, v in SKILLS.items()]
