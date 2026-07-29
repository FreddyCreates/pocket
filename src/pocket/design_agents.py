"""Design subagents — UI polish specialists on the mesh.

DESIGN / AESTHETE / LAYOUT / MOTION leave artifacts on E: mesh so other
agents can consume critique + CSS without sharing the chat transcript.

DESIGN is first-class (role=design) — never aliased to SCRIPTOR.
"""

from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional

from pocket.mesh_disk import ensure_agent, leave_artifact, send_message, write_vdisk

AGENTS: Dict[str, Dict[str, str]] = {
    "DESIGN": {
        "role": "lead product design",
        "focus": "overall product cohesion, nav, hierarchy, ship-ready polish",
    },
    "AESTHETE": {
        "role": "visual taste",
        "focus": "color, type, contrast, density, empty states",
    },
    "LAYOUT": {
        "role": "structure",
        "focus": "grid, spacing, composer, rails, responsive breakpoints",
    },
    "MOTION": {
        "role": "motion + feedback",
        "focus": "spinners, toasts, stream pulses, transitions (subtle)",
    },
}

# Alias for dispatch / docs
DESIGN_AGENTS = AGENTS

_CSS_HINT = re.compile(
    r"\b(css|stylesheet|tailwind|token|color|palette|theme|font|typography)\b",
    re.I,
)
_LAYOUT_HINT = re.compile(
    r"\b(layout|grid|flex|spacing|breakpoint|sidebar|nav|hero|card)\b",
    re.I,
)
_MOTION_HINT = re.compile(
    r"\b(motion|animat|transition|easing|fade|slide|spring|duration)\b",
    re.I,
)
_CRITIQUE_HINT = re.compile(
    r"\b(critique|review|aesthet|taste|polish|ugly|pretty|visual)\b",
    re.I,
)


def list_design_agents() -> List[Dict[str, Any]]:
    out = []
    for aid, meta in AGENTS.items():
        ensure_agent(aid, role="design")
        out.append({"id": aid, **meta, "status": "ready", "source": "design"})
    return out


def bootstrap_design_agents() -> Dict[str, Any]:
    """Ensure design specialists exist on the mesh with role=design."""
    ids = []
    for aid in AGENTS:
        ids.append(ensure_agent(aid, role="design"))
    return {
        "ok": True,
        "registered": len(ids),
        "agents": [i["id"] for i in ids],
        "roles": {a: AGENTS[a]["role"] for a in AGENTS},
    }


def _critique(agent: str, prompt: str) -> str:
    meta = AGENTS.get(agent, AGENTS["DESIGN"])
    base = (
        f"# {agent} — {meta['role']}\n\n"
        f"**Focus:** {meta['focus']}\n\n"
        f"## Brief\n{prompt}\n\n"
    )
    if agent == "AESTHETE":
        return base + (
            "## Rubric (1–5)\n"
            "| Axis | Score | Note |\n"
            "|------|-------|------|\n"
            "| Hierarchy | — | Is one thing primary? |\n"
            "| Contrast | — | Text/icon on surface readable? |\n"
            "| Density | — | Breathing room vs cramped |\n"
            "| Consistency | — | Radii, type scale, icon weight |\n"
            "| Polish | — | Alignment, empty states, focus rings |\n\n"
            "## Likely fixes\n"
            "1. Bump muted text contrast on dark panels.\n"
            "2. One accent hue; secondary actions stay neutral.\n"
            "3. 8pt grid — kill 3px gaps.\n"
            "4. Focus states before hover candy.\n"
            "5. Empty/error states share happy-path surface language.\n\n"
            f"— AESTHETE @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
    if agent == "LAYOUT":
        return base + (
            "## Grid\n"
            "- Base unit: 4px / 8px\n"
            "- Content max-width: 1120px product · 720px prose\n"
            "- Columns: 12 desktop · 4 tablet · 2 mobile\n"
            "- Gutter: 16–24px\n\n"
            "## Regions\n"
            "| Region | Desktop | Mobile |\n"
            "|--------|---------|--------|\n"
            "| Shell nav | 240px left rail | bottom tab / top bar |\n"
            "| Main | fluid | full width |\n"
            "| Aside | 280–320px | stacked |\n"
            "| Sticky actions | top-right | full-width bottom |\n\n"
            "## Rules\n"
            "1. One primary action per viewport.\n"
            "2. Related controls share a surface.\n"
            "3. Vertical rhythm multiples of 1rem.\n"
            "4. One scroll owner per column.\n\n"
            f"— LAYOUT @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
    if agent == "MOTION":
        return base + (
            "## Tokens\n"
            "| Token | Value | Use |\n"
            "|-------|-------|-----|\n"
            "| `--pocket-dur` | 120–200ms | micro |\n"
            "| `--pocket-dur-md` | 240–320ms | panel/modal |\n"
            "| `--pocket-ease` | cubic-bezier(0.22, 1, 0.36, 1) | default |\n\n"
            "## Principles\n"
            "1. Enter: opacity + 4–8px translateY.\n"
            "2. Exit faster than enter (×0.75).\n"
            "3. Stagger lists 30–50ms, max 6 items.\n"
            "4. `prefers-reduced-motion: reduce` → opacity only.\n\n"
            f"— MOTION @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        )
    # DESIGN lead
    return base + (
        "## Ship checklist (beta)\n"
        "- [ ] Product nav cohesive (Overview · Desktop · API · Studio)\n"
        "- [ ] Composer focus ring + @dispatch affordance\n"
        "- [ ] Subagent roster readable, status dots clear\n"
        "- [ ] Empty states quiet, not marketing fluff\n"
        "- [ ] Dark palette: panel/line/accent consistent\n"
        "- [ ] Mobile safe-area respected\n"
        "- [ ] Design bus freq-2 artifacts for LAYOUT/MOTION/AESTHETE\n\n"
        "## Notes\n"
        "- Prefer Cursor/Antigravity density over landing-page hero.\n"
        "- Dispatch results: short inline chips, not JSON dumps.\n"
        "- Mesh card: show E: virtual disk when available.\n"
        "- Next: @LAYOUT grid · @MOTION transitions · @AESTHETE critique\n\n"
        f"— DESIGN @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    )


def _css_snippet(agent: str, prompt: str) -> str:
    p = (prompt or "").lower()
    accent = "#10a37f"
    if "warm" in p or "orange" in p:
        accent = "#f97316"
    elif "blue" in p:
        accent = "#3b82f6"
    elif "violet" in p or "purple" in p:
        accent = "#8b5cf6"

    if agent == "LAYOUT":
        return (
            "/* LAYOUT — composer + rails */\n"
            ".composer{padding:10px 20px 14px;border-top:1px solid var(--line)}\n"
            ".box:focus-within{border-color:rgba(16,163,127,.45);"
            "box-shadow:0 0 0 1px rgba(16,163,127,.2)}\n"
            ".rail-roster .rr-h{display:flex;justify-content:space-between;"
            "font-size:11px;color:var(--muted);padding:8px 12px}\n"
            ".pocket-grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px;"
            "max-width:1120px;margin:0 auto}\n"
            f"/* prompt: {(prompt or '')[:100]} */\n"
        )
    if agent == "MOTION":
        return (
            "/* MOTION — subtle feedback */\n"
            ":root{--pocket-dur:180ms;--pocket-ease:cubic-bezier(0.22,1,0.36,1)}\n"
            "@keyframes sa-spin{to{transform:rotate(360deg)}}\n"
            ".sa-dot.run{animation:pulse 1.2s infinite;"
            "box-shadow:0 0 0 3px rgba(16,163,127,.15)}\n"
            ".dispatch-chip{animation:fadein var(--pocket-dur) var(--pocket-ease)}\n"
            "@keyframes fadein{from{opacity:0;transform:translateY(4px)}"
            "to{opacity:1;transform:none}}\n"
            "@media (prefers-reduced-motion:reduce){"
            "*,*::before,*::after{animation-duration:.01ms!important;"
            "transition-duration:.01ms!important}}\n"
        )
    if agent == "AESTHETE":
        return (
            "/* AESTHETE — density + type */\n"
            f":root{{--muted:#8b919a;--line:rgba(255,255,255,.08);"
            f"--accent:{accent};--panel:#141414;--bg:#0b0f14;"
            f"--text:#e8eef6;--radius:12px}}\n"
            ".sa-name{font-weight:600;letter-spacing:.02em}\n"
            ".rr-empty,.wt-empty{color:var(--muted);font-size:12px;"
            "padding:10px 12px}\n"
            ".pocket-card{background:var(--panel);border:1px solid var(--line);"
            "border-radius:var(--radius);padding:1rem;color:var(--text)}\n"
        )
    return (
        "/* DESIGN — product shell cohesion */\n"
        f":root{{--pocket-accent:{accent};--pocket-radius:12px;"
        f"--pocket-bg:#0b0f14;--pocket-surface:#121821;"
        f"--pocket-text:#e8eef6;--pocket-muted:#8b9bb0}}\n"
        ".pnav a.on{color:var(--pocket-accent);border-bottom:2px solid var(--pocket-accent)}\n"
        ".subagents-panel{border-radius:10px;border:1px solid rgba(255,255,255,.08)}\n"
        ".pocket-btn{background:var(--pocket-accent);color:#fff;border:0;"
        "border-radius:8px;padding:.5rem 1rem;"
        "transition:filter 180ms cubic-bezier(0.22,1,0.36,1)}\n"
        ".pocket-btn:hover{filter:brightness(1.08)}\n"
        f"/* prompt: {(prompt or '')[:120]} */\n"
    )


def _component_notes(prompt: str) -> str:
    return (
        f"# Component notes\n\n{prompt}\n\n"
        "- Shell · Card · Button · Status chip · Inbox row · Composer\n"
        "- Prefer CSS variables from design token snippets\n"
        "- Mesh roster: status dots + @mention affordance\n"
        "— DESIGN\n"
    )


def run_design_agent(name: str, prompt: str) -> Dict[str, Any]:
    n = (name or "DESIGN").upper()
    if n not in AGENTS:
        n = "DESIGN"
    ensure_agent(n, role="design")
    p = (prompt or "").strip() or "general product UI pass"
    critique = _critique(n, p)
    css = _css_snippet(n, p)
    art = leave_artifact(n, f"{n.lower()}_critique.md", critique, notify=["ARCHON", "SHIP_HEADLESS"])
    css_art = leave_artifact(n, f"{n.lower()}_snippet.css", css, notify=["DESIGN", "ARCHON"])
    artifacts = [art, css_art]
    if n == "DESIGN":
        notes = leave_artifact(
            n,
            "component_notes.md",
            _component_notes(p),
            notify=["ARCHON", "LAYOUT"],
        )
        artifacts.append(notes)
    v = write_vdisk(
        f"design/{n.lower()}_{int(time.time())}.md",
        critique + "\n\n```css\n" + css + "\n```\n",
        agent_id=n,
    )
    send_message(n, "ARCHON", f"design pass complete: {n}", kind="design", channel="freq-2")
    send_message(n, "SHIP_HEADLESS", "design artifact ready for ship review", kind="design", channel="freq-4")
    return {
        "ok": True,
        "agent": n,
        "role": AGENTS[n]["role"],
        "desc": AGENTS[n]["focus"],
        "artifacts": artifacts,
        "vdisk": v,
        "channel": "freq-2",
        "prompt": p[:500],
    }


def _pick_specialists(prompt: str, agents: Optional[List[str]] = None) -> List[str]:
    if agents:
        return [a.upper() for a in agents if a.upper() in AGENTS] or ["DESIGN"]
    p = prompt or ""
    picks: List[str] = ["DESIGN"]
    if _LAYOUT_HINT.search(p):
        picks.append("LAYOUT")
    if _MOTION_HINT.search(p):
        picks.append("MOTION")
    if _CRITIQUE_HINT.search(p) or _CSS_HINT.search(p):
        picks.append("AESTHETE")
    out: List[str] = []
    for a in picks:
        if a not in out:
            out.append(a)
    return out


def dispatch_design(
    prompt: str,
    *,
    agents: Optional[List[str]] = None,
    from_agent: str = "USER",
    channel: str = "freq-2",
) -> Dict[str, Any]:
    """Route a design prompt to specialists; leave polished mesh artifacts."""
    bootstrap_design_agents()
    text = (prompt or "").strip()
    # If explicit agents list passed without filter intent, run all when agents is None-like empty
    if agents is None and not text:
        targets = list(AGENTS.keys())
    elif agents is not None:
        targets = _pick_specialists(text, agents)
    else:
        # keyword pick; if no specialty keywords, still run DESIGN only
        # (callers wanting full pack pass agents=list(AGENTS))
        targets = _pick_specialists(text, None)
    results = []
    for name in targets:
        send_message(from_agent, name, text, channel=channel, kind="dispatch")
        results.append(run_design_agent(name, text))
    return {
        "ok": all(r.get("ok") for r in results),
        "dispatched": len(results),
        "agents": targets,
        "results": results,
        "count": len(results),
        "mesh": True,
        "channel": channel,
    }
