"""Grok coding agent (real) + plan handoff packages + research pulls."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pocket.jobs import WORK_DIR, list_jobs
from pocket.live import probe_all
from pocket.platform import list_deploys, platform_manifest
from pocket.sessions import get_usage, list_sessions, record_llm_tokens
from pocket.tokenomics import burn, estimate_session_cost, snapshot as token_snapshot

POCKET_ROOT = Path(__file__).resolve().parents[2]
INBOX = POCKET_ROOT / "GROK_INBOX.md"
PULLS_DIR = Path.home() / ".pocket" / "grok_pulls"
PULLS_DIR.mkdir(parents=True, exist_ok=True)


def which_grok() -> str:
    g = shutil.which("grok")
    if g:
        return g
    # Common install on this machine
    cand = Path.home() / ".grok" / "bin" / "grok.exe"
    if cand.exists():
        return str(cand)
    return ""


def build_research_plan(user_prompt: str = "", cwd: str = "") -> Dict:
    live = probe_all()
    usage = get_usage()
    tok = token_snapshot()
    sessions = list_sessions(30)
    jobs = list_jobs(15)
    deploys = list_deploys()
    plat = platform_manifest()
    open_n = len(sessions)
    cost = estimate_session_cost(
        open_n,
        concurrent_jobs=max(1, sum(1 for s in sessions if s.get("status") == "running")),
    )
    running = [s for s in sessions if s.get("status") == "running"]
    failed_jobs = [j for j in jobs if j.get("status") == "failed"]
    queued = [j for j in jobs if j.get("status") == "queued"]

    research = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "prompt": user_prompt,
        "cwd": cwd or str(WORK_DIR),
        "platform": {
            "product": "POCKET Multi-Agent Platform",
            "what_user_have": plat.get("you_have"),
            "tools": plat.get("tools"),
        },
        "live_services": [
            {"name": s.get("name"), "live": s.get("live")} for s in (live.get("services") or [])
        ],
        "sessions": {
            "open": open_n,
            "running": len(running),
            "by_mode": _count_modes(sessions),
            "titles": [
                {
                    "id": s.get("id"),
                    "mode": s.get("mode"),
                    "title": s.get("title"),
                    "status": s.get("status"),
                }
                for s in sessions[:12]
            ],
        },
        "jobs": {
            "recent": len(jobs),
            "queued": len(queued),
            "failed": len(failed_jobs),
        },
        "deploys": {
            "total": len(deploys),
            "running": len([d for d in deploys if d.get("status") == "running"]),
            "urls": [d.get("url_local") for d in deploys if d.get("status") == "running"][:8],
        },
        "tokenomics": {
            "balance": tok.get("balance"),
            "unit": tok.get("unit"),
            "lifetime_burned": tok.get("lifetime_burned"),
            "session_cost_model": cost,
            "llm_tokens_tracked": usage.get("llm_tokens") or usage.get("est_tokens"),
        },
        "usage": usage,
        "prior_art_notes": [
            "Grok coding agent uses headless `grok --single` with acceptEdits — real work, not a mailbox.",
            "Plan handoff is the deliberate queue for deferred planning without burning agent turns.",
            "Multi-session cost scales with concurrent LLM jobs, not open tab count alone.",
        ],
    }

    plan_steps = [
        "1. Read live services — reconnect anything DOWN.",
        "2. Review open sessions and failed jobs.",
        "3. Pick workspace for the user request.",
        "4. Grok coding agent OR Codex for implementation; Shell/WSL to verify.",
        "5. Deploy static if UI ship needed.",
        "6. Note POCK burn + any reported LLM tokens.",
        "7. Write durable notes; leave plan handoff only if deferred work remains.",
        "8. Report: changes, cost, deploys, next 3 actions.",
    ]
    if user_prompt.strip():
        plan_steps.insert(0, f"0. USER REQUEST: {user_prompt.strip()[:500]}")

    return {
        "schema": "pocket.grok_pull.v2",
        "research": research,
        "plan": plan_steps,
        "recommended_commands": [
            "Grok coding session for implementation",
            "Plan handoff session for deferred planning only",
            "GET /v1/usage for llm_tokens",
            "POST /v1/deploy for local app",
        ],
    }


def _count_modes(sessions: List[Dict]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for s in sessions:
        m = s.get("mode") or "?"
        out[m] = out.get(m, 0) + 1
    return out


def format_pull_markdown(pkg: Dict) -> str:
    r = pkg.get("research") or {}
    lines = [
        "# PLAN HANDOFF / GROK RESEARCH PULL",
        "",
        f"**When:** {r.get('timestamp')}",
        f"**CWD:** `{r.get('cwd')}`",
        "",
        "## User request",
        "",
        (r.get("prompt") or "_(status pull)_")[:2000],
        "",
        "## Research snapshot",
        "",
        f"- Open sessions: **{(r.get('sessions') or {}).get('open')}**",
        f"- Modes: `{(r.get('sessions') or {}).get('by_mode')}`",
        f"- POCK balance: **{(r.get('tokenomics') or {}).get('balance')}**",
        f"- LLM tokens tracked: **{(r.get('tokenomics') or {}).get('llm_tokens_tracked')}**",
        "",
        "### Live services",
        "",
    ]
    for s in r.get("live_services") or []:
        lines.append(f"- {'LIVE' if s.get('live') else 'DOWN'} — {s.get('name')}")
    lines += [
        "",
        "### Session cost model",
        "```json",
        json.dumps((r.get("tokenomics") or {}).get("session_cost_model"), indent=2)[:2000],
        "```",
        "",
        "## Whole plan",
        "",
    ]
    for step in pkg.get("plan") or []:
        lines.append(f"- {step}")
    lines.append("")
    return "\n".join(lines)


def write_pull_package(user_prompt: str = "", cwd: str = "") -> Tuple[Path, Dict]:
    pkg = build_research_plan(user_prompt, cwd)
    burn("research_pull", meta={"prompt": (user_prompt or "")[:200]})
    md = format_pull_markdown(pkg)
    ts = time.strftime("%Y%m%d-%H%M%S")
    path = PULLS_DIR / f"pull-{ts}.md"
    path.write_text(md, encoding="utf-8")
    header = (
        "# PLAN HANDOFF INBOX — latest full package\n\n"
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "Use **Plan handoff** sessions for deferred planning. "
        "Use **Grok coding agent** sessions for real Grok execution.\n\n"
        f"Archive: `{path}`\n\n---\n\n"
    )
    INBOX.write_text(header + md, encoding="utf-8")
    (PULLS_DIR / f"pull-{ts}.json").write_text(json.dumps(pkg, indent=2), encoding="utf-8")
    return path, pkg


def run_plan_handoff(prompt: str, cwd: str) -> Tuple[str, str, str]:
    """Plan handoff only — full research package, no Grok agent exec."""
    path, pkg = write_pull_package(prompt, cwd)
    burn("job_grok_handoff", meta={"kind": "plan_handoff", "path": str(path)})
    body = (
        "## Plan handoff (not a coding agent)\n\n"
        f"Full research + plan written to:\n- `{path}`\n- `GROK_INBOX.md`\n\n"
        "Open a **Grok coding agent** session to execute, or **Codex**.\n\n"
        + format_pull_markdown(pkg)
    )
    return body, "", "plan-handoff"


def _parse_tokens(text: str) -> int:
    """Extract reported LLM tokens from agent logs when present."""
    if not text:
        return 0
    total = 0
    # codex: "tokens used\n10,326" or "tokens used: 10326"
    for m in re.finditer(r"tokens used[:\s]*([0-9,]+)", text, re.I):
        try:
            total += int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    # generic token_count
    for m in re.finditer(r'"total_tokens"\s*:\s*(\d+)', text):
        try:
            total += int(m.group(1))
        except ValueError:
            pass
    return total


def _strip_device_prefix(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"^\[Client device:[^\]]*\]\s*", "", t, count=1, flags=re.I | re.S).strip()
    return t or (text or "").strip()


def _prefer_product_cwd(cwd: str) -> str:
    """Prefer Parallax / product trees over empty scratch when possible."""
    try:
        from pocket.executor import prefer_product_cwd

        return prefer_product_cwd(cwd or "")
    except Exception:
        p = Path(cwd) if cwd else Path()
        if p.is_dir() and ".pocket" not in str(p).replace("\\", "/").lower():
            return str(p.resolve())
        parallax = Path(r"E:\PARALLAX-Exchange-Clearinghouse")
        if parallax.is_dir():
            return str(parallax)
        return cwd or str(WORK_DIR)


def build_grok_system_prompt(user_prompt: str, cwd: str, pkg: Dict, research_path: str) -> str:
    """Tight production system prompt — task first, paper/testnet posture for Parallax."""
    task = _strip_device_prefix(user_prompt)
    task_one = " ".join(task.split()) if task else "Continue the current production task."
    is_parallax = "parallax" in (cwd or "").lower()
    posture = (
        "PARALLAX posture: paper/testnet-first. No live money, no live broker routing, "
        "emit receipts when you change settlement paths."
        if is_parallax
        else "Ship real improvements. Prefer small verified diffs over long plans."
    )
    return (
        f"TASK: {task_one}\n\n"
        "You are the Grok coding agent inside POCKET (Edge desktop / host co-pilot).\n"
        "Rules:\n"
        "1. Execute the TASK — do not ask what to work on.\n"
        "2. Prefer concrete file edits + short verification over essays and research dumps.\n"
        "3. Research package is optional context only — do not spend the whole turn writing papers "
        "unless the user explicitly asked for a research paper.\n"
        "4. If a prior turn was cancelled/superseded, ignore it and follow this TASK only.\n"
        "5. Keep chat replies readable: short paragraphs, bullets for changes, how to verify.\n"
        f"6. {posture}\n"
        f"Working directory: {cwd}\n"
        f"Research package (optional context): {research_path}\n"
        f"Host: sessions_open={pkg.get('research', {}).get('sessions', {}).get('open')} "
        f"POCK={pkg.get('research', {}).get('tokenomics', {}).get('balance')} "
        f"deploys={pkg.get('research', {}).get('deploys', {}).get('running')}\n\n"
        f"## Full user message\n{user_prompt.strip()[:6000]}\n"
    )


def run_grok_exec(prompt: str, cwd: str, job_id: str = "") -> Tuple[str, str, str]:
    """
    Real Grok coding agent via `grok --single` with live streaming when job_id set.
    """
    agent_cwd = _prefer_product_cwd(cwd)
    path, pkg = write_pull_package(prompt, agent_cwd)
    grok = which_grok()
    full_prompt = build_grok_system_prompt(prompt, agent_cwd, pkg, str(path))
    try:
        from pocket.ai_workspace import inject_for_prompt

        full_prompt = inject_for_prompt(
            full_prompt,
            workspace="parallax" if "parallax" in (agent_cwd or "").lower() else "workspace",
            cwd=agent_cwd,
        )
    except Exception:
        pass
    if not grok:
        return (
            format_pull_markdown(pkg)
            + "\n\n**Grok CLI not found** — cannot run coding agent. Install Grok Build CLI.\n",
            "grok CLI missing",
            "grok",
        )

    env = {**os.environ}
    gbin = str(Path(grok).parent)
    env["PATH"] = gbin + os.pathsep + env.get("PATH", "")
    env["CI"] = "1"

    # Grok CLI takes the prompt as argv; keep under Windows limits, task-first already.
    cmd = [
        grok,
        "--single",
        full_prompt[:12000],
        "--cwd",
        agent_cwd,
        # Overnight / long ship sessions need headroom; default 48 (was 16 → "max turns reached")
        "--max-turns",
        str(max(8, min(200, int(os.environ.get("POCKET_GROK_MAX_TURNS") or "48")))),
        "--always-approve",
        "--output-format",
        "plain",
    ]
    burn("job_grok_exec", meta={"cwd": agent_cwd, "cli": grok})
    from pocket.stream_util import estimate_tokens, run_streaming

    max_turns = max(8, min(200, int(os.environ.get("POCKET_GROK_MAX_TURNS") or "48")))
    # ~2–3 min per turn worst case; floor 15m, cap 3h for overnight ship sessions
    grok_timeout = max(900, min(10800, max_turns * 120))
    out, rc, err = run_streaming(
        cmd,
        job_id=job_id,
        cwd=agent_cwd,
        env=env,
        timeout=float(grok_timeout),
        engine="grok",
    )
    out = (out or "").strip()
    toks = _parse_tokens(out)
    if not toks and out:
        toks = max(1, len(full_prompt + out) // 4)
        est_note = f"[llm_tokens≈{toks} estimated]\n"
    else:
        est_note = f"[llm_tokens={toks}]\n" if toks else f"[stream_tokens≈{estimate_tokens(out)}]\n"
    if toks:
        try:
            record_llm_tokens(toks, engine="grok")
        except Exception:
            pass
    header = (
        f"[engine=grok-coding-agent cwd={agent_cwd}]\n"
        f"[cli={grok}]\n"
        f"[research_package={path}]\n"
        f"{est_note}\n"
    )
    try:
        from pocket.reply_format import polish_agent_output

        polished = polish_agent_output(out[-60000:] if out else "", engine="grok")
    except Exception:
        polished = out[-60000:] if out else ""
    if err == "cancelled" or rc == -2:
        return (
            header
            + (polished or out or "")
            + "\n\n[POCKET] Grok turn cancelled — send a new message to reorganize.",
            "cancelled",
            "grok",
        )
    if err:
        return header + (polished or out or format_pull_markdown(pkg)), err, "grok"
    if rc != 0 and not out:
        return header + format_pull_markdown(pkg), f"grok exit {rc}", "grok"
    return header + (polished or "(empty)"), ("" if rc == 0 else f"grok exit {rc}"), "grok"


def can_codex_start_grok() -> Dict[str, object]:
    g = which_grok()
    return {
        "yes": bool(g),
        "how": "POCKET mode=grok runs `grok --single` with acceptEdits; Codex can shell the same",
        "cli": g or None,
        "api": "POST /v1/sessions {mode:'grok'} then POST .../messages",
        "plan_handoff": "mode=handoff for deferred plans without agent exec",
        "note": "Working coding agent when CLI present — not a mailbox.",
    }
