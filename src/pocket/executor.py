"""Real PC agent execution — Codex / Claude / shell / WSL / Grok handoff."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pocket.jobs import WORK_DIR

PARALLAX_ROOT = r"E:\PARALLAX-Exchange-Clearinghouse"
AURO_ROOT = str(Path.home() / "Documents" / "GitHub" / "Auro14B")

KNOWN_WORKSPACES: List[Dict[str, str]] = [
    {
        "id": "parallax",
        "label": "PARALLAX Exchange Clearinghouse",
        "path": PARALLAX_ROOT,
    },
    {
        "id": "pocket",
        "label": "POCKET itself",
        "path": str(Path.home() / "OneDrive" / "pocket-os"),
    },
    {
        "id": "auro",
        "label": "Auro14B / RO14B",
        "path": AURO_ROOT,
    },
    {
        "id": "hz",
        "label": "HZ Offline mesh",
        "path": str(Path.home() / "OneDrive" / "hz-offline"),
    },
    {
        "id": "monad",
        "label": "MonadBuilder / Hackaton",
        "path": str(Path.home() / "Documents" / "GitHub" / "Monad-Hackaton"),
    },
    {
        "id": "mesie",
        "label": "MESIE engine",
        "path": str(Path.home() / "Multi-Element-Spectral-Intelligence-Engine-MESIE-"),
    },
    {
        "id": "tokenomics",
        "label": "Tokenomics desk",
        "path": str(WORK_DIR / "tokenomics"),
    },
    {
        "id": "workspace",
        "label": "POCKET scratch workspace",
        "path": str(WORK_DIR),
    },
]

# Ensure tokenomics desk exists with a seed README
_tok = WORK_DIR / "tokenomics"
_tok.mkdir(parents=True, exist_ok=True)
_seed = _tok / "README.md"
if not _seed.exists():
    _seed.write_text(
        "# Tokenomics desk\n\nUse POCKET multi-agent sessions to design supply, "
        "vesting, utility sinks, and on-chain token contracts here.\n",
        encoding="utf-8",
    )

_SUBST_CACHE: Dict[str, str] = {}
_SUBST_LETTERS = "PQRSTUVWXYZ"


def which_codex() -> str:
    """Prefer node → codex.js (reliable stdin/argv). Never codex.ps1 (Notepad / broken args)."""
    # Direct node entry — most reliable on Windows for multi-line prompts via stdin
    npm_codex_js = (
        Path(os.environ.get("APPDATA") or "")
        / "npm"
        / "node_modules"
        / "@openai"
        / "codex"
        / "bin"
        / "codex.js"
    )
    if npm_codex_js.is_file():
        node = shutil.which("node") or ""
        if node:
            return f"node+{npm_codex_js}"
    # Explicit Windows cmd shim (stdin works; avoid .ps1)
    for p in (
        Path(os.environ.get("APPDATA") or "") / "npm" / "codex.cmd",
        Path(os.environ.get("ProgramFiles") or "") / "nodejs" / "codex.cmd",
    ):
        if p.is_file():
            return str(p)
    w = shutil.which("codex") or ""
    if w.lower().endswith(".ps1"):
        cmd = w[:-4] + ".cmd"
        if os.path.isfile(cmd):
            return cmd
        # Never return .ps1 — Notepad / broken argv
        return ""
    return w


def which_claude() -> str:
    return shutil.which("claude") or ""


def which_wsl() -> str:
    return shutil.which("wsl") or ""


def which_grok_cli() -> str:
    g = shutil.which("grok") or ""
    if g:
        return g
    cand = Path.home() / ".grok" / "bin" / "grok.exe"
    return str(cand) if cand.exists() else ""


def _needs_onedrive_bridge(path: str) -> bool:
    p = path.replace("/", "\\").lower()
    return "onedrive" in p


def _list_subst() -> Dict[str, str]:
    out: Dict[str, str] = {}
    try:
        p = subprocess.run(["subst"], capture_output=True, text=True, timeout=10, shell=True)
        for line in (p.stdout or "").splitlines():
            m = re.match(r"^([A-Za-z]):\\:\s*=>\s*(.+)\s*$", line.strip())
            if not m:
                continue
            letter, target = m.group(1).upper(), m.group(2).strip()
            key = os.path.normcase(os.path.normpath(target))
            out[key] = f"{letter}:\\"
    except Exception:
        pass
    return out


def _free_drive_letter() -> Optional[str]:
    used = set()
    for d in range(ord("A"), ord("Z") + 1):
        if os.path.exists(f"{chr(d)}:\\"):
            used.add(chr(d))
    for ch in _SUBST_LETTERS:
        if ch not in used:
            return ch
    return None


def bridge_path_for_codex(path: str) -> Tuple[str, str]:
    real = str(Path(path).resolve()) if Path(path).exists() else path
    if not _needs_onedrive_bridge(real):
        return real, ""
    key = os.path.normcase(os.path.normpath(real))
    if key in _SUBST_CACHE and os.path.isdir(_SUBST_CACHE[key]):
        return _SUBST_CACHE[key], f"OneDrive bridge via {_SUBST_CACHE[key]}"
    existing = _list_subst()
    if key in existing:
        _SUBST_CACHE[key] = existing[key]
        return existing[key], f"OneDrive bridge via {existing[key]}"
    letter = _free_drive_letter()
    if not letter:
        return real, "No free drive letter for OneDrive bridge"
    try:
        p = subprocess.run(
            ["subst", f"{letter}:", real],
            capture_output=True,
            text=True,
            timeout=15,
            shell=True,
        )
        if p.returncode != 0:
            return real, f"SUBST failed: {(p.stderr or p.stdout or '')[:200]}"
        mapped = f"{letter}:\\"
        _SUBST_CACHE[key] = mapped
        return mapped, f"OneDrive bridge via {mapped} → {real}"
    except Exception as e:
        return real, f"SUBST error: {e}"


def _is_scratch_workspace(path: str) -> bool:
    n = (path or "").replace("/", "\\").lower()
    return (not n) or n.rstrip("\\").endswith("\\.pocket\\workspace") or n.rstrip("\\").endswith("\\.pocket\\workspace\\")


def prefer_product_cwd(path: str = "") -> str:
    """Prefer real product trees over empty ~/.pocket/workspace scratch."""
    if path and not _is_scratch_workspace(path) and Path(path).is_dir():
        return str(Path(path).resolve())
    for cand in (
        os.environ.get("POCKET_CODEX_CWD") or "",
        PARALLAX_ROOT,
        AURO_ROOT,
        str(Path.home() / "OneDrive" / "pocket-os"),
        path,
    ):
        if cand and Path(cand).is_dir():
            return str(Path(cand).resolve())
    Path(WORK_DIR).mkdir(parents=True, exist_ok=True)
    return str(WORK_DIR)


def resolve_cwd(job: Dict) -> str:
    """Resolve job working directory.

    Founder edition (host_power): full local product trees on THIS machine.
    Market edition: only tenants/<user> (their local sandbox + virtual).
    Never allow market jobs into founder deny paths.
    """
    from pocket.platform_space import (
        is_under_tenant,
        path_is_founder_private,
        tenant_cwd,
    )

    owner = (job.get("owner") or "").strip().lower()
    host_power = bool(job.get("host_power"))
    edition = (job.get("edition") or ("founder" if host_power else "market")).lower()
    ws = (job.get("workspace") or "").strip()

    # Market / non-founder: jail to their space
    if edition == "market" or (owner and not host_power):
        if not owner:
            owner = "anonymous"
            try:
                return tenant_cwd("market", "files")
            except Exception:
                p = Path.home() / ".pocket" / "tenants" / "_anon" / "files"
                p.mkdir(parents=True, exist_ok=True)
                return str(p)
        cwd0 = (job.get("cwd") or "").strip()
        if cwd0 and is_under_tenant(owner, cwd0) and not path_is_founder_private(cwd0):
            return str(Path(cwd0).resolve())
        # local vs virtual surface inside tenant
        surface = "local" if ws in ("local",) else (ws if ws.startswith("tenant") else ws or "files")
        return tenant_cwd(owner, surface)

    # Founder: normal host paths
    cwd = (job.get("cwd") or "").strip()
    if ws and ws not in ("workspace", "default", "scratch") and not ws.startswith("tenant:"):
        for w in KNOWN_WORKSPACES:
            if w["id"] == ws or w["path"] == ws:
                p = Path(w["path"])
                if p.is_dir():
                    return str(p.resolve())
        p = Path(ws)
        if p.is_dir():
            return str(p.resolve())
    if cwd and Path(cwd).is_dir() and not _is_scratch_workspace(cwd):
        return str(Path(cwd).resolve())
    return prefer_product_cwd(cwd)


def available_engines() -> Dict[str, object]:
    codex = which_codex()
    claude = which_claude()
    wsl = which_wsl()
    return {
        "codex": bool(codex),
        "codex_path": codex or None,
        "claude": bool(claude),
        "claude_path": claude or None,
        "shell": True,
        "wsl": bool(wsl),
        "wsl_path": wsl or None,
        "grok": bool(which_grok_cli()),
        "grok_path": which_grok_cli() or None,
        "handoff": True,
        "term": True,
        "desktop": True,
        "web": True,
        "nexus": True,
        "agent": True,
        "doer": True,
        "guppy": True,
        "browser": True,
        "capture": True,
        "repos": True,
        "copilot": True,
        "archon": True,
        "alpha": True,
        "autonomy": True,
        "streaming": True,
        "headless_agents": True,
        "ai_api": True,
        "session_resume": True,
        "default": "codex" if codex else ("claude" if claude else "shell"),
        "workspaces": [{**w, "exists": Path(w["path"]).is_dir()} for w in KNOWN_WORKSPACES],
        "note": "AI for the whole computer — desk UI + headless sellable API. One session tab = one Codex thread.",
        "value": [
            "Codex/Grok/Claude for code (Codex resumes same thread per tab)",
            "Headless doer · multi-step desktop (≤5) without chat",
            "15+ headless agents (researcher, squad, security…)",
            "Desktop 40+ apps (native + third-party + Copilot)",
            "Sellable AI API with sk_pocket_ keys + metering",
            "Phone remote + POCK credits + safety allowlists",
        ],
    }


def run_job(job: Dict) -> Tuple[str, str, str]:
    mode = (job.get("mode") or "codex").lower()
    prompt = (job.get("prompt") or "").strip()
    cwd = resolve_cwd(job)
    Path(cwd).mkdir(parents=True, exist_ok=True)
    jid = job.get("id") or ""

    if mode == "shell":
        return _run_shell(prompt, cwd, job_id=jid)
    if mode in ("wsl", "wsl_native", "wsl-native", "linux"):
        from pocket.wsl_agent import run_wsl_job

        return run_wsl_job(prompt, cwd=cwd, job=job)
    if mode == "claude":
        return _run_claude(prompt, cwd, job_id=jid)
    if mode == "ask":
        return _run_ask(prompt, cwd)
    if mode == "plan":
        return _run_planning_ai(prompt, cwd, job_id=jid)
    if mode == "handoff":
        return _run_plan_handoff(prompt, cwd)
    if mode == "grok":
        return _run_grok_agent(prompt, cwd, job_id=jid)
    if mode in ("novae_grok", "novae-grok", "novae"):
        from pocket.novae import run_novae_job

        return run_novae_job(prompt, cwd=cwd, job=job, kind="grok")
    if mode in ("novae_codex", "novae-codex"):
        from pocket.novae import run_novae_job

        return run_novae_job(prompt, cwd=cwd, job=job, kind="codex")
    if mode in ("wiki", "infinite_wiki", "codebase"):
        from pocket.infinite_wiki import run_wiki_job

        return run_wiki_job(prompt, cwd=cwd, job=job)
    if mode in ("dream",):
        from pocket.dream_mode import dream_once, list_dreams, status as dream_status

        low = (prompt or "").strip().lower()
        if low in ("status", "list", ""):
            return json.dumps({"status": dream_status(), "recent": list_dreams(8)}, indent=2), "", "dream"
        return json.dumps(dream_once(force=True), indent=2, default=str), "", "dream"
    if mode in ("duel",):
        from pocket.agent_duels import duel

        r = duel((prompt or "").strip() or "How should we ship the next slice?")
        return (r.get("verdict") or {}).get("winning_plan") or json.dumps(r, indent=2), "", "duel"
    if mode in ("capsule",):
        from pocket.time_capsules import create_capsule, status as cap_status

        low = (prompt or "").strip()
        if low.lower() in ("list", "status", ""):
            return json.dumps(cap_status(), indent=2, default=str), "", "capsule"
        # "in 120s: message" or "capsule message"
        m = re.match(r"(?:in\s+)?(\d+)\s*(?:s|sec|seconds)?\s*[:\-]?\s*(.+)$", low, re.I)
        if m:
            return json.dumps(create_capsule(m.group(2), after_sec=int(m.group(1))), indent=2), "", "capsule"
        return json.dumps(create_capsule(low, after_sec=300), indent=2), "", "capsule"
    if mode in ("serendipity",):
        from pocket.serendipity import find_links

        return json.dumps(find_links(limit=10), indent=2), "", "serendipity"
    if mode in ("proof",):
        from pocket.proof_chain import list_receipts, mint_receipt, status as proof_status, verify_chain

        low = (prompt or "").strip().lower()
        if low in ("verify", "check"):
            return json.dumps(verify_chain(), indent=2), "", "proof"
        if low in ("list", "status", ""):
            return json.dumps({"status": proof_status(), "recent": list_receipts(10)}, indent=2), "", "proof"
        return json.dumps(mint_receipt("manual", prompt or "manual"), indent=2), "", "proof"
    if mode in ("dual", "cortex", "subcortex"):
        from pocket.cortex_subcortex import run_dual_job

        return run_dual_job(prompt, cwd=cwd, job=job)
    if mode in ("swarm",):
        from pocket.always_on_swarm import pulse_now, start as swarm_start, status as swarm_status

        low = (prompt or "").strip().lower()
        if low in ("start", "on", "enable"):
            return json.dumps(swarm_start(), indent=2), "", "swarm"
        if low in ("status", "help", ""):
            return json.dumps(swarm_status(), indent=2), "", "swarm"
        return json.dumps(pulse_now(), indent=2), "", "swarm"
    if mode in ("build", "ship", "use_case", "emergent", "loop"):
        from pocket.build_loop import manage_until_done, run_use_case, start_loop
        from pocket.use_cases import get_use_case, list_use_cases

        text = (prompt or "").strip()
        low = text.lower()
        # list use cases
        if low in ("help", "list", "use cases", "usecases", "parity"):
            from pocket.use_cases import parity_report

            if "parity" in low:
                return json.dumps(parity_report(), indent=2), "", "build"
            lines = ["# POCKET real use cases (Emergent+)\n"]
            for u in list_use_cases():
                lines.append(f"- **{u['id']}**: {u['title']}")
            lines.append("\nStart: `use_case:fullstack_web_app` or describe the app to ship.")
            return "\n".join(lines), "", "build"
        # explicit use case
        uc_id = ""
        m = re.match(r"(?:use[_-]?case|uc|run)[:\s]+([a-z0-9_]+)", low)
        if m:
            uc_id = m.group(1)
        elif get_use_case(text.split()[0] if text else ""):
            uc_id = text.split()[0].lower()
        owner = (job.get("owner") or "pocket") if job else "pocket"
        if uc_id:
            started = run_use_case(uc_id, goal=text, owner=owner)
        else:
            started = start_loop(text, owner=owner, template="web_static", loop_kind="ship")
        if not started.get("ok"):
            return "", started.get("error") or "loop failed to start", "build"
        lid = started.get("id") or ""
        final = manage_until_done(lid, timeout_sec=120.0)
        loop = final.get("loop") or started
        summary = (
            f"# Build loop {'DONE' if final.get('ok') else loop.get('status','').upper()}\n\n"
            f"**id:** `{lid}`\n"
            f"**goal:** {loop.get('goal')}\n"
            f"**phase:** {loop.get('phase')} · **status:** {loop.get('status')}\n"
            f"**project:** `{loop.get('project')}`\n"
            f"**progress:** {loop.get('progress')}\n\n"
            f"Poll: `/v1/build-loops/{lid}`\n"
            f"History phases: {len(loop.get('history') or [])}\n"
        )
        return summary, "" if final.get("ok") or loop.get("status") == "done" else (loop.get("error") or "incomplete"), "build"
    if mode == "custom_agent":
        from pocket.custom_agents import create_agent, list_agents, run_custom_agent

        text = (prompt or "").strip()
        low = text.lower()
        if low.startswith("create ") or low.startswith("new "):
            # create name: Role — personality
            body = text.split(" ", 1)[-1]
            name = body.split(":")[0].strip() or "CustomAgent"
            rest = body.split(":", 1)[-1].strip() if ":" in body else "specialist"
            rec = create_agent(name=name, role=rest, owner=(job or {}).get("owner") or "pocket")
            return json.dumps(rec, indent=2), "", "custom_agent"
        if low in ("list", "help"):
            return json.dumps({"agents": list_agents()}, indent=2), "", "custom_agent"
        # run: AgentId task...
        parts = text.split(None, 1)
        aid = parts[0] if parts else "AGENT"
        task = parts[1] if len(parts) > 1 else text
        r = run_custom_agent(aid, task, cwd=cwd, job=job)
        return r.get("summary") or json.dumps(r, indent=2), "" if r.get("ok") else r.get("error", ""), "custom_agent"
    if mode == "desktop":
        from pocket.desktop import run_desktop_job

        return run_desktop_job(prompt)
    if mode == "web":
        from pocket.web_research import run_web_job

        return run_web_job(prompt)
    if mode == "nexus":
        from pocket.nexus_bridge import run_nexus_job

        return run_nexus_job(prompt)
    if mode == "mesie":
        from pocket.mesie_bridge import run_mesie_job

        return run_mesie_job(prompt)
    if mode in ("auro", "auro14b", "ro14b", "him"):
        from pocket.auro14b_bridge import run_auro_job

        return run_auro_job(prompt)
    if mode in ("agent", "doer"):
        from pocket.step_agent import run_step_agent

        return run_step_agent(prompt, cwd=cwd, job=job, max_steps=10)
    if mode == "guppy":
        from pocket.guppy import run_guppy

        return run_guppy(prompt, cwd=cwd, job=job)
    if mode == "browser":
        from pocket.browser_mode import run_browser_job

        return run_browser_job(prompt, cwd=cwd, job=job)
    if mode == "capture":
        from pocket.capture import run_capture_job

        return run_capture_job(prompt)
    if mode == "repos":
        from pocket.repos import run_repos_job

        return run_repos_job(prompt)
    if mode == "copilot":
        from pocket.copilot_agent import run_copilot_job

        return run_copilot_job(prompt, cwd=cwd, job=job)
    if mode in ("archon", "alpha", "workers"):
        from pocket.alpha_workers import run_alpha_job

        return run_alpha_job(prompt, cwd=cwd, job=job)
    if mode in ("woa", "wrapped-orch", "wrapped_orch", "orchestrator-llm"):
        from pocket.wrapped_orchestrator import run_woa_job

        return run_woa_job(prompt, cwd=cwd, job=job)
    if mode in ("offload", "embody", "embodiment", "realworld"):
        from pocket.offload_queue import enqueue, ensure_worker

        ensure_worker()
        # "offload: ..." or free text → queue and return ticket
        goal = prompt
        if goal.lower().startswith("offload:"):
            goal = goal.split(":", 1)[1].strip()
        r = enqueue(
            goal,
            agent=(job.get("mode") or "AI").upper(),
            session_id=job.get("session_id") or "",
            workspace=job.get("workspace") or "parallax",
        )
        body = (
            f"## Offload accepted\n\n"
            f"**Ticket:** `{r.get('ticket')}`\n"
            f"**Goal:** {goal[:500]}\n\n"
            f"Chat turn is free. Poll `GET /v1/offload/{r.get('ticket')}` or right-rail previews.\n"
            f"Worker runs embodiment steps + proof pack in background.\n"
        )
        return body, ("" if r.get("ok") else r.get("error") or "offload failed"), "offload"
    if mode in ("cowork", "work", "demo", "embody-desk"):
        from pocket.cowork import run_cowork_job

        return run_cowork_job(prompt, cwd=cwd, job=job)
    if mode in ("git", "forge", "sovereign-git", "sovereign_git"):
        from pocket.sovereign_git import run_git_job

        return run_git_job(prompt)
    if mode in ("ghost", "ghost-math", "math"):
        from pocket.ghost_math import run_ghost

        return run_ghost(prompt)
    if mode == "term":
        # Interactive terminals are handled via /v1/terminals — not one-shot jobs
        return (
            "This is a live terminal session. Type commands in the UI; they go to the long-lived shell.",
            "",
            "term",
        )
    return _run_codex(prompt, cwd, job_id=jid, job=job)


def _run_shell(cmd: str, cwd: str, job_id: str = "") -> Tuple[str, str, str]:
    try:
        from pocket.safety import allow_shell

        ok, msg = allow_shell(cmd)
        if not ok:
            return "", msg, "shell"
    except Exception:
        pass
    blocked = (
        "rm -rf /",
        "format c:",
        "format c ",
        "del /s /q c:\\",
        "shutdown",
        "mkfs",
        "rd /s /q c:\\",
        "reg delete",
        "net user",
    )
    low = cmd.lower()
    if any(b in low for b in blocked):
        return "", "Blocked dangerous shell command", "shell"
    from pocket.stream_util import run_streaming

    out, rc, err = run_streaming(
        cmd,
        job_id=job_id,
        cwd=cwd,
        timeout=300,
        engine="shell",
        shell=True,
    )
    out = (out or "").strip()[-50000:]
    if err:
        return out, err, "shell"
    if rc != 0:
        return out or f"(exit {rc})", f"exit {rc}", "shell"
    return out or "(no output)", "", "shell"


def _run_wsl(cmd: str, job_id: str = "") -> Tuple[str, str, str]:
    if not which_wsl():
        return "", "WSL not installed", "wsl"
    distro_args: List[str] = ["wsl"]
    try:
        p = subprocess.run(
            ["wsl", "-l", "-q"],
            capture_output=True,
            timeout=8,
            text=True,
            encoding="utf-16-le",
            errors="replace",
        )
        names = [n.strip() for n in (p.stdout or "").splitlines() if n.strip()]
        if any(n.lower() == "debian" for n in names):
            distro_args = ["wsl", "-d", "Debian"]
    except Exception:
        pass
    full = distro_args + ["--", "bash", "-lc", cmd]
    from pocket.stream_util import run_streaming

    out, rc, err = run_streaming(full, job_id=job_id, timeout=300, engine="wsl")
    out = (out or "").strip()[-50000:]
    if err:
        return out, err, "wsl"
    if rc != 0:
        return out or f"(exit {rc})", f"wsl exit {rc}", "wsl"
    return out or "(no output)", "", "wsl"


def _run_ask(prompt: str, cwd: str) -> Tuple[str, str, str]:
    engines = available_engines()
    return (
        f"## Plan only (no code execution)\n\n"
        f"**Request:** {prompt[:2000]}\n\n"
        f"**Workspace:** `{cwd}`\n\n"
        f"**Engines:** Codex={engines['codex']} · Claude={engines['claude']} · WSL={engines['wsl']}\n\n"
        "1. Clarify goal and constraints\n"
        "2. Identify files/modules to touch\n"
        "3. Implement smallest change\n"
        "4. Run tests / real verification\n"
        "5. Report diff summary\n\n"
        "Open a **Codex** or **Claude** session to execute.",
        "",
        "ask",
    )


def _run_planning_ai(prompt: str, cwd: str, job_id: str = "") -> Tuple[str, str, str]:
    """Planning AI chat — real model, no code edits."""
    from pocket.stream_util import run_streaming
    from pocket.grok_bridge import which_grok

    grok = which_grok()
    plan_prompt = (
        "You are a product/engineering planning partner. PLAN ONLY.\n"
        "Do not write code, do not edit files, do not run shell.\n"
        "Give: goals, constraints, ordered steps, risks, open questions, success metrics.\n"
        f"Workspace context: {cwd}\n\n"
        f"User:\n{prompt}"
    )
    if grok:
        cmd = [
            grok,
            "--single",
            plan_prompt[:12000],
            "--cwd",
            cwd,
            "--max-turns",
            "6",
            "--permission-mode",
            "plan",
            "--output-format",
            "plain",
        ]
        env = {**os.environ}
        env["PATH"] = str(Path(grok).parent) + os.pathsep + env.get("PATH", "")
        out, rc, err = run_streaming(
            cmd, job_id=job_id, cwd=cwd, env=env, timeout=300, engine="plan"
        )
        text = (out or "").strip()
        header = f"[engine=planning-ai · no code · cwd={cwd}]\n\n"
        if text:
            return header + text[-50000:], ("" if rc == 0 else (err or f"exit {rc}")), "plan"
        # fall through to template if empty
    plan, _, _ = _run_ask(prompt, cwd)
    return (
        "[engine=planning-ai-template]\n\n"
        + plan
        + "\n\n_(Install/use Grok CLI for live Planning AI chat.)_",
        "",
        "plan",
    )


def _run_plan_handoff(prompt: str, cwd: str) -> Tuple[str, str, str]:
    """Deferred planning package only — no coding agent."""
    from pocket.grok_bridge import run_plan_handoff

    return run_plan_handoff(prompt, cwd)


def _run_grok_agent(prompt: str, cwd: str, job_id: str = "") -> Tuple[str, str, str]:
    """Real Grok coding agent via grok --single (streamed)."""
    from pocket.grok_bridge import run_grok_exec

    return run_grok_exec(prompt, cwd, job_id=job_id)


def _codex_argv(codex: str) -> List[str]:
    """Build argv prefix for codex binary (handles node+path form)."""
    if codex.startswith("node+"):
        js = codex[5:]
        node = shutil.which("node") or "node"
        return [node, js]
    return [codex]


def _codex_cmd_base(codex: str, agent_cwd: str) -> List[str]:
    return _codex_argv(codex) + [
        "exec",
        "--skip-git-repo-check",
        "-C",
        agent_cwd,
        "-s",
        "workspace-write",
    ]


def _parse_codex_thread_id(text: str) -> str:
    """Extract Codex conversation/session UUID from CLI output."""
    if not text:
        return ""
    # Common lines: "session id: 019f…" or "thread id: …" or UUID alone near session
    patterns = (
        r"(?:session|thread|conversation)\s*id[:\s]+([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
        r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b",
    )
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            return m.group(1)
    return ""


def _bind_codex_thread(session_id: str, thread_id: str, *, resumed: bool = False) -> None:
    if not session_id or not thread_id:
        return
    try:
        from pocket.sessions import bind_engine_thread

        bind_engine_thread(session_id, thread_id, engine="codex", resumed=resumed)
    except Exception:
        pass


_IDLE_ASK_RE = re.compile(
    r"what (?:do you want me to|would you like me to) work on"
    r"|what (?:do you want|would you like) me to (?:work on|do)"
    r"|what should i (?:work on|do)(?:\s+next)?"
    r"|how can i help you today"
    r"|ready for (?:your |a )?task"
    r"|awaiting (?:your )?(?:task|instructions?)",
    re.I,
)


def _strip_device_prefix(text: str) -> str:
    """Pull the real user task out from [Client device: …] wrappers."""
    t = (text or "").strip()
    t = re.sub(
        r"^\[Client device:[^\]]*\]\s*",
        "",
        t,
        count=1,
        flags=re.I | re.S,
    ).strip()
    return t or (text or "").strip()


def _wants_research_only(task: str) -> bool:
    """True only when the user explicitly asked for a paper / research writeup."""
    low = (task or "").lower()
    explicit = (
        "research paper",
        "write a paper",
        "write the paper",
        "draft a paper",
        "literature review",
        "write docs only",
        "documentation only",
        "markdown paper",
        "zenodo",
        "latex manuscript",
    )
    if any(p in low for p in explicit):
        return True
    # "research X" alone is often product research — still prefer code when ship words present
    ship = ("ship", "production", "implement", "fix", "code", "test", "alpha", "paradise", "overnight")
    if any(w in low for w in ship):
        return False
    return False


def _build_codex_prompt(prompt: str, agent_cwd: str, cwd: str, bridge_note: str = "") -> str:
    """
    Build a prompt that survives Windows truncation and idle-resume threads.
    Put the concrete TASK first so the first line always carries the work.
    """
    raw = (prompt or "").strip()
    task = _strip_device_prefix(raw)
    if not task:
        task = (
            "Continue the current task. If nothing is in progress, inventory this "
            "workspace for production gaps and implement one concrete improvement."
        )
    # Single-line task lead (critical): if anything truncates at first newline, task still lands.
    task_one_line = " ".join(task.split())
    research_only = _wants_research_only(task_one_line)
    work_rules = [
        "You are the POCKET host coding agent on the operator machine.",
        "Do real work in the working directory. Do NOT ask what to work on — the TASK is already stated.",
        "If the workspace is PARALLAX, prioritize production/alpha readiness (paper/testnet first).",
    ]
    if research_only:
        work_rules.append(
            "User asked for research/paper work: improve docs/research with tight structure, "
            "but still leave a short 'how to verify / next code step' note."
        )
    else:
        work_rules.extend(
            [
                "DEFAULT = CODE WORK, not research essays.",
                "Prefer file edits, tests, configs, and short verification over new markdown papers.",
                "Only write or expand research docs if the user explicitly asked for a paper/writeup.",
                "Ship tasks (production/alpha/paradise/overnight): implement a concrete vertical slice and verify.",
                "End with: what changed, how to verify, one next step — keep chat replies clean and readable.",
            ]
        )
    parts = [
        f"TASK: {task_one_line}",
        "",
        *work_rules,
        "",
        f"Working directory: {agent_cwd}",
    ]
    if bridge_note:
        parts.append(f"[POCKET] {bridge_note}. Real project path: {cwd}")
    if raw and raw != task_one_line:
        parts.extend(["", "Full user message:", raw])
    return "\n".join(parts) + "\n"


def _codex_looks_idle(text: str) -> bool:
    """True when Codex ignored the task and only asked what to work on."""
    if not text:
        return False
    low = text.lower()
    if _IDLE_ASK_RE.search(low):
        # If it also did real work (exec/edit), not idle
        if "```" in text or "\nexec\n" in low or "succeeded in" in low:
            return False
        return True
    return False


def _run_codex(prompt: str, cwd: str, job_id: str = "", job: Optional[Dict] = None) -> Tuple[str, str, str]:
    codex = which_codex()
    if not codex:
        if which_claude():
            result, err, _ = _run_claude(prompt, cwd, job_id=job_id)
            return result + "\n\n_(Codex missing — Claude.)_", err, "claude-fallback"
        plan, _, _ = _run_ask(prompt, cwd)
        return plan + "\n\nInstall Codex CLI.", "codex not installed", "ask-fallback"

    job = job or {}
    pocket_sid = (job.get("session_id") or "").strip()
    # Prefer explicit job field, else load from POCKET session (one button = one Codex thread)
    engine_thread = ""
    if not job.get("_no_resume"):
        engine_thread = (job.get("engine_thread_id") or job.get("codex_session_id") or "").strip()
        if not engine_thread and pocket_sid:
            try:
                from pocket.sessions import get as get_sess

                s = get_sess(pocket_sid) or {}
                engine_thread = (s.get("engine_thread_id") or s.get("codex_session_id") or "").strip()
            except Exception:
                engine_thread = ""

    product_cwd = prefer_product_cwd(cwd)
    agent_cwd, bridge_note = bridge_path_for_codex(product_cwd)
    if _is_scratch_workspace(agent_cwd):
        agent_cwd = prefer_product_cwd("")
        bridge_note = bridge_note or "product cwd remap"

    full_prompt = _build_codex_prompt(prompt, agent_cwd, product_cwd, bridge_note)
    try:
        from pocket.ai_workspace import inject_for_prompt

        full_prompt = inject_for_prompt(
            full_prompt,
            workspace=(job.get("workspace") or "parallax"),
            session_id=(job.get("session_id") or ""),
            cwd=product_cwd,
        )
    except Exception:
        pass
    resumed = bool(engine_thread)

    # Always pass prompt via stdin ("-") — multi-line argv is unreliable on Windows cmd shims
    if resumed:
        # codex exec resume [OPTIONS] SESSION_ID [PROMPT]
        # OPTIONS before SESSION_ID; prompt last as "-"
        cmd = _codex_argv(codex) + [
            "exec",
            "resume",
            "--skip-git-repo-check",
            engine_thread,
            "-",
        ]
    else:
        cmd = _codex_cmd_base(codex, agent_cwd) + ["-"]

    from pocket.stream_util import estimate_tokens, run_streaming

    out, rc, err = run_streaming(
        cmd,
        job_id=job_id,
        cwd=agent_cwd if os.path.isdir(agent_cwd) else product_cwd,
        env={**os.environ, "CI": "1"},
        timeout=900,
        engine="codex",
        stdin_text=full_prompt,
    )
    combined = (out or "").strip()
    thread_id = _parse_codex_thread_id(combined) or engine_thread
    if thread_id and pocket_sid and not _codex_looks_idle(combined):
        _bind_codex_thread(pocket_sid, thread_id, resumed=resumed)

    header = f"[engine=codex cwd={agent_cwd}"
    if bridge_note:
        header += f" · {bridge_note}"
    if resumed and engine_thread:
        header += f" · resume={engine_thread[:13]}…"
    elif thread_id:
        header += f" · new_thread={thread_id[:13]}…"
    header += f"]\n[pocket_session={pocket_sid or '—'} · one POCKET tab = one Codex thread]\n"
    header += f"[stream_tokens≈{estimate_tokens(combined)}]\n\n"

    def _fallback_fresh(reason: str) -> Tuple[str, str, str]:
        try:
            from pocket.sessions import clear_engine_thread

            if pocket_sid:
                clear_engine_thread(pocket_sid)
        except Exception:
            pass
        fresh_job = {
            **job,
            "engine_thread_id": "",
            "codex_session_id": "",
            "_no_resume": True,
            "_idle_retry": True,
        }
        result2, err2, eng2 = _run_codex(prompt, product_cwd, job_id=job_id, job=fresh_job)
        return (
            header
            + f"(fresh thread: {reason})\n\n"
            + result2,
            err2,
            eng2,
        )

    if job.get("_no_resume"):
        pass  # already in fresh path — do not recurse on idle
    elif resumed and (err or rc != 0):
        reason = err or f"exit {rc}"
        return _fallback_fresh(f"resume failed for {engine_thread}: {reason[:100]}")
    elif (not job.get("_idle_retry")) and _codex_looks_idle(combined):
        # Poisoned/empty first turn or truncated prompt — one hard fresh retry
        return _fallback_fresh("idle ask-what-to-work-on; clearing thread")

    try:
        from pocket.reply_format import polish_agent_output

        polished = polish_agent_output(combined[-60000:], engine="codex")
    except Exception:
        polished = combined[-60000:]

    if err:
        return header + (polished or combined[-60000:]), err, "codex"
    if rc != 0:
        e = f"codex exit {rc}"
        if "os error 2" in combined.lower():
            e += f" (path/sandbox bridge={bridge_note or 'none'})"
        return header + (polished or combined[-60000:]), e, "codex"
    # record parsed tokens
    try:
        from pocket.sessions import record_llm_tokens
        from pocket.stream_util import _parse_tokens

        t = _parse_tokens(combined) or estimate_tokens(combined)
        if t:
            record_llm_tokens(t, engine="codex")
    except Exception:
        pass
    note = ""
    if thread_id and not _codex_looks_idle(combined):
        note = (
            f"\n\n[POCKET] Codex thread `{thread_id}` bound to this session. "
            "Next messages resume it — press +Codex for a separate session."
        )
    elif _codex_looks_idle(combined):
        note = (
            "\n\n[POCKET] Codex returned an idle prompt. Thread was not bound. "
            "Send again or press +Codex for a fresh session."
        )
    body = polished or "(empty)"
    if note and note.strip() not in body:
        body = body + note
    return header + body, "", "codex"


def _run_claude(prompt: str, cwd: str, job_id: str = "") -> Tuple[str, str, str]:
    claude = which_claude()
    if not claude:
        if which_codex():
            result, err, _ = _run_codex(prompt, cwd, job_id=job_id)
            return result + "\n\n_(Claude missing — Codex.)_", err, "codex-fallback"
        return "", "claude CLI not installed", "claude"
    from pocket.stream_util import run_streaming

    for cmd in (
        [claude, "-p", prompt, "--output-format", "text"],
        [claude, "--print", prompt],
        [claude, "-p", prompt],
    ):
        out, rc, err = run_streaming(
            cmd, job_id=job_id, cwd=cwd, timeout=900, engine="claude"
        )
        text = (out or "").strip()
        if rc == 0 and text:
            return f"[engine=claude cwd={cwd}]\n\n{text[-60000:]}", "", "claude"
        if "login" in text.lower() or "auth" in text.lower():
            return "", f"claude failed: {text[:2000]}", "claude"
        last = text or err or f"exit {rc}"
    return "", f"claude failed: {last[:2000]}", "claude"
