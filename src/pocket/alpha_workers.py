"""Latin-named Python workers (alphas) — multimodal orchestrators.

GUPPY stays GUPPY. All other production workers get deep names so the platform
can integrate many jobs under stable identities.

ARCHON / HYDRA are alphas: they fan out to specialists.
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit

# ---------------------------------------------------------------------------
# Registry — stable product IDs
# ---------------------------------------------------------------------------

WORKERS: Dict[str, Dict[str, Any]] = {
    "ARCHON": {
        "id": "ARCHON",
        "latin": "Archon",
        "meaning": "ruler / chief magistrate — multimodal desk alpha",
        "class": "alpha",
        "jobs": [
            "orchestrate_demo",
            "browser_flow",
            "research_tweet",
            "record_demo",
            "github_analyze",
            "copilot_send",
            "outlook_draft",
            "screenshot",
            "multi_step",
        ],
        "role": "python",
    },
    "HYDRA": {
        "id": "HYDRA",
        "latin": "Hydra",
        "meaning": "many heads — parallel multi-job alpha",
        "class": "alpha",
        "jobs": ["fanout", "batch_open", "batch_analyze", "schedule_chain"],
        "role": "python",
    },
    "SCRUTATOR": {
        "id": "SCRUTATOR",
        "latin": "Scrutator",
        "meaning": "examiner — research, lookup, fetch, repo inspect",
        "class": "specialist",
        "jobs": ["lookup", "research", "fetch", "analyze_repo", "github_view"],
        "role": "python",
        "legacy": ["research_worker"],
    },
    "SCRIPTOR": {
        "id": "SCRIPTOR",
        "latin": "Scriptor",
        "meaning": "scribe — compose with LLM, draft tweets/emails",
        "class": "specialist",
        "jobs": ["compose_tweet", "compose_email", "compose_intro", "tag_plan"],
        "role": "llm+python",
        "legacy": ["composer"],
    },
    "PORTARIUS": {
        "id": "PORTARIUS",
        "latin": "Portarius",
        "meaning": "doorkeeper — open apps, Edge, signed-in surfaces",
        "class": "specialist",
        "jobs": ["open_app", "open_edge", "open_x", "open_github", "open_outlook"],
        "role": "python",
        "legacy": ["edge_host"],
    },
    "OCULUS": {
        "id": "OCULUS",
        "latin": "Oculus",
        "meaning": "eye — screenshot paste-back",
        "class": "specialist",
        "jobs": ["screenshot", "snip_open"],
        "role": "python",
        "legacy": ["capture"],
    },
    "SPECULUM": {
        "id": "SPECULUM",
        "latin": "Speculum",
        "meaning": "looking-glass — screen record whole demos",
        "class": "specialist",
        "jobs": ["record_start", "record_stop", "record_demo"],
        "role": "python",
    },
    "REPOSITOR": {
        "id": "REPOSITOR",
        "latin": "Repositor",
        "meaning": "storekeeper — folders, zip, git, GitHub",
        "class": "specialist",
        "jobs": ["list_repos", "open_repos", "clone", "analyze", "new_repo", "zip"],
        "role": "python",
        "legacy": ["repos", "github"],
    },
    "CONSILIARIUS": {
        "id": "CONSILIARIUS",
        "latin": "Consiliarius",
        "meaning": "advisor — Windows Copilot paste + send",
        "class": "specialist",
        "jobs": ["copilot_open", "copilot_paste_send", "copilot_intro"],
        "role": "python",
        "legacy": ["copilot_intro"],
    },
    "TABELLARIUS": {
        "id": "TABELLARIUS",
        "latin": "Tabellarius",
        "meaning": "courier — Outlook draft mail",
        "class": "specialist",
        "jobs": ["outlook_open", "outlook_draft"],
        "role": "python",
    },
    "NAVIGATOR": {
        "id": "NAVIGATOR",
        "latin": "Navigator",
        "meaning": "pilot — multi-step web navigation",
        "class": "specialist",
        "jobs": ["browse", "intent_url", "tweet_compose"],
        "role": "python",
    },
    "GUPPY": {
        "id": "GUPPY",
        "latin": "Guppy",
        "meaning": "small fish — commercial silent multi-step (kept)",
        "class": "alpha",
        "jobs": ["multi_step", "lookup", "schedule", "desktop"],
        "role": "python",
    },
}


def list_workers() -> List[Dict[str, Any]]:
    return [dict(v) for v in WORKERS.values()]


def get_worker(name: str) -> Optional[Dict[str, Any]]:
    key = (name or "").strip().upper()
    if key in WORKERS:
        return dict(WORKERS[key])
    # legacy aliases
    low = (name or "").strip().lower()
    for w in WORKERS.values():
        if low in [x.lower() for x in (w.get("legacy") or [])]:
            return dict(w)
        if low == w["latin"].lower():
            return dict(w)
    return None


def run_worker(
    name: str,
    job: str,
    *,
    prompt: str = "",
    params: Optional[Dict[str, Any]] = None,
    cwd: str = "",
    session_job: Optional[Dict] = None,
) -> Tuple[str, str, str]:
    """Dispatch a named worker job. Returns (markdown, error, engine_id)."""
    w = get_worker(name)
    if not w:
        return "", f"unknown worker: {name}", "alpha"
    wid = w["id"]
    j = (job or "help").strip().lower()
    params = params or {}
    emit("worker", f"{wid}.{j}: {(prompt or '')[:100]}", agent=wid, role="python")

    if j in ("help", "identity", "who"):
        return (
            f"# {wid} — {w['latin']}\n\n"
            f"**{w['meaning']}**\n\n"
            f"Class: `{w['class']}` · jobs: {', '.join(w['jobs'])}\n",
            "",
            wid.lower(),
        )

    # --- specialists ---
    if wid == "SCRUTATOR":
        return _scrutator(j, prompt, params)
    if wid == "SCRIPTOR":
        return _scriptor(j, prompt, params, cwd, session_job)
    if wid == "PORTARIUS":
        return _portarius(j, prompt, params)
    if wid == "OCULUS":
        from pocket.capture import run_capture_job

        return run_capture_job(prompt or j)
    if wid == "SPECULUM":
        return _speculum(j, prompt, params)
    if wid == "REPOSITOR":
        return _repositor(j, prompt, params)
    if wid == "CONSILIARIUS":
        return _consiliarius(j, prompt, params, cwd, session_job)
    if wid == "TABELLARIUS":
        return _tabellarius(j, prompt, params)
    if wid == "NAVIGATOR":
        return _navigator(j, prompt, params)
    if wid == "GUPPY":
        from pocket.guppy import run_guppy

        return run_guppy(prompt or j, cwd=cwd, job=session_job)
    if wid == "HYDRA":
        return _hydra(j, prompt, params, cwd, session_job)
    if wid == "ARCHON":
        return _archon(j, prompt, params, cwd, session_job)
    return "", f"{wid} cannot run job {j}", wid.lower()


def _scrutator(j: str, prompt: str, params: Dict) -> Tuple[str, str, str]:
    if j in ("lookup", "research", "search") or prompt.lower().startswith("lookup"):
        from pocket.step_agent import _lookup_and_bring_back

        q = params.get("query") or prompt
        q = q.replace("lookup", "", 1).strip() if q.lower().startswith("lookup") else q
        r = _lookup_and_bring_back(q, open_ui=True)
        md = f"## SCRUTATOR\n\n{r.get('message')}\n\n{r.get('brief') or ''}\n"
        if r.get("deep_fetch") and isinstance(r["deep_fetch"], dict):
            md += f"\n### Deep\n```\n{(r['deep_fetch'].get('text') or '')[:2500]}\n```\n"
        return md, "" if r.get("ok") else r.get("error", ""), "scrutator"
    if j in ("analyze_repo", "analyze", "inspect") or "analyze" in (prompt or "").lower():
        from pocket.repos import analyze_github_repo

        target = params.get("repo") or params.get("url") or prompt
        r = analyze_github_repo(target, useful_for="POCKET multi-agent desk / host co-pilot")
        return _fmt(r, "SCRUTATOR · repo analysis"), "" if r.get("ok") else r.get("error", ""), "scrutator"
    from pocket.repos import run_repos_job

    return run_repos_job(prompt or "help")


def _scriptor(j: str, prompt: str, params: Dict, cwd: str, job: Optional[Dict]) -> Tuple[str, str, str]:
    from pocket.browser_mode import _compose_with_engine, _extract_tweet_text

    engine = params.get("engine") or "auto"
    out, err, eng = _compose_with_engine(prompt, cwd or "", job, engine)
    tweet = _extract_tweet_text(out) if "tweet" in (prompt or "").lower() else ""
    md = f"## SCRIPTOR ({eng})\n\n{out[-8000:]}\n"
    if tweet:
        md += f"\n**Extracted:** {tweet}\n"
    return md, err, "scriptor"


def _portarius(j: str, prompt: str, params: Dict) -> Tuple[str, str, str]:
    from pocket.desktop import open_app
    from pocket.browser_mode import open_edge_url, open_x_home

    if j in ("open_x",) or prompt.lower() in ("open x", "open twitter"):
        r = open_x_home()
    elif j in ("open_edge",) or prompt.lower().startswith("open edge"):
        url = params.get("url") or prompt.replace("open edge", "").strip()
        r = open_edge_url(url or "https://example.com")
    elif j in ("open_outlook",) or "outlook" in prompt.lower():
        r = open_app("outlook")
    else:
        app = params.get("app") or prompt.replace("open", "").strip().split()[0]
        r = open_app(app)
    return f"## PORTARIUS\n\n**{r.get('message') or r.get('error')}**\n```json\n{json.dumps(r, default=str)[:2000]}\n```", "" if r.get("ok") else r.get("error", ""), "portarius"


def _speculum(j: str, prompt: str, params: Dict) -> Tuple[str, str, str]:
    from pocket.screen_record import record_start, record_stop, record_status, run_recorded_demo

    if j in ("record_start", "start"):
        r = record_start()
    elif j in ("record_stop", "stop"):
        r = record_stop()
    elif j in ("status",):
        r = record_status()
    elif j in ("record_demo", "demo"):
        r = run_recorded_demo(prompt or "demo")
    else:
        r = record_status()
        r["help"] = "record_start | record_stop | record_demo <plan>"
    return f"## SPECULUM\n\n```json\n{json.dumps(r, indent=2, default=str)[:4000]}\n```", "" if r.get("ok", True) else r.get("error", ""), "speculum"


def _repositor(j: str, prompt: str, params: Dict) -> Tuple[str, str, str]:
    from pocket.repos import run_repos_job, analyze_github_repo, clone_repo

    if j in ("analyze", "analyze_repo") or prompt.lower().startswith("analyze"):
        target = params.get("repo") or prompt
        r = analyze_github_repo(target, useful_for=params.get("for") or "POCKET")
        return _fmt(r, "REPOSITOR · analyze"), "" if r.get("ok") else r.get("error", ""), "repositor"
    if j in ("clone",) or prompt.lower().startswith("clone "):
        url = params.get("url") or prompt.split(None, 1)[-1]
        r = clone_repo(url)
        return _fmt(r, "REPOSITOR · clone"), "" if r.get("ok") else r.get("error", ""), "repositor"
    return run_repos_job(prompt or "help")


def _consiliarius(j: str, prompt: str, params: Dict, cwd: str, job: Optional[Dict]) -> Tuple[str, str, str]:
    from pocket.copilot_agent import run_copilot_job, paste_and_send_copilot, introduce_to_copilot

    if j in ("copilot_paste_send", "paste_send", "send") or "send" in j:
        text = params.get("text") or prompt
        r = paste_and_send_copilot(text)
        return _fmt(r, "CONSILIARIUS · paste+send"), "" if r.get("ok") else r.get("error", ""), "consiliarius"
    if j in ("copilot_intro", "introduce") or prompt.lower().startswith("introduce"):
        r = introduce_to_copilot(prompt, use_llm=True, cwd=cwd, job=job)
        # also paste+send
        if r.get("intro"):
            r2 = paste_and_send_copilot(r["intro"], already_open=True)
            r["send"] = r2
        return _fmt(r, "CONSILIARIUS · intro+send"), "" if r.get("ok") else "fail", "consiliarius"
    return run_copilot_job(prompt or "help", cwd=cwd, job=job)


def _tabellarius(j: str, prompt: str, params: Dict) -> Tuple[str, str, str]:
    from pocket.outlook_agent import create_draft

    subject = params.get("subject") or "POCKET test subject"
    body = params.get("body") or prompt or "POCKET TABELLARIUS test body — draft only, not sent."
    if prompt.lower().startswith("draft"):
        body = prompt
    r = create_draft(subject=subject, body=body)
    return _fmt(r, "TABELLARIUS · Outlook draft"), "" if r.get("ok") else r.get("error", ""), "tabellarius"


def _navigator(j: str, prompt: str, params: Dict) -> Tuple[str, str, str]:
    from pocket.browser_mode import run_browser_job

    return run_browser_job(prompt or "help", job={"browser_engine": "python"})


def _hydra(j: str, prompt: str, params: Dict, cwd: str, job: Optional[Dict]) -> Tuple[str, str, str]:
    """Multi-head: run several specialist jobs from one prompt."""
    steps = params.get("steps") or []
    if not steps and prompt:
        # parse "then"
        from pocket.step_agent import parse_steps

        steps = [{"job": "raw", "prompt": s} for s in parse_steps(prompt, max_steps=8)]
    results = []
    for s in steps[:8]:
        p = s.get("prompt") or s.get("text") or ""
        # route
        low = p.lower()
        if "outlook" in low or "email" in low or "draft" in low:
            r, e, eng = run_worker("TABELLARIUS", "outlook_draft", prompt=p)
        elif "copilot" in low:
            r, e, eng = run_worker("CONSILIARIUS", "introduce", prompt=p)
        elif "screenshot" in low:
            r, e, eng = run_worker("OCULUS", "screenshot", prompt="screenshot")
        elif "repo" in low or "github" in low or "analyze" in low:
            r, e, eng = run_worker("REPOSITOR", "analyze", prompt=p)
        elif low.startswith("open "):
            r, e, eng = run_worker("PORTARIUS", "open_app", prompt=p)
        else:
            r, e, eng = run_worker("SCRUTATOR", "lookup", prompt=p)
        results.append({"prompt": p, "engine": eng, "error": e, "result": (r or "")[:2000]})
    return (
        "## HYDRA · multi-head\n\n"
        + "\n\n".join(f"### Head {i+1}\n{x['result']}" for i, x in enumerate(results)),
        "",
        "hydra",
    )


def _archon(j: str, prompt: str, params: Dict, cwd: str, job: Optional[Dict]) -> Tuple[str, str, str]:
    """ARCHON alpha — full demo orchestration with optional screen record."""
    low = (prompt or j or "").lower()
    record = params.get("record", True)
    if j in ("help",):
        return (
            "# ARCHON — multimodal desk alpha\n\n"
            "Orchestrates SCRUTATOR, SCRIPTOR, PORTARIUS, OCULUS, SPECULUM, "
            "REPOSITOR, CONSILIARIUS, TABELLARIUS, NAVIGATOR, GUPPY.\n\n"
            "Examples:\n"
            "- `demo` — record + open tools + screenshot\n"
            "- `analyze brain ai` — SCRUTATOR/REPOSITOR on neuroemergence / Brain AI\n"
            "- `outlook draft` · `copilot introduce` · `research tweet …`\n",
            "",
            "archon",
        )

    # Demos via Orchestrator (executor engine — not chat micro-driving)
    if j in (
        "orchestrate_demo", "demo", "record_demo", "grand_demo", "interface_demo",
        "ui_demo", "focused_demo", "wow_demo", "wow",
    ) or low in (
        "demo", "full demo", "record demo", "grand demo", "interface demo",
        "ui demo", "focused demo", "wow demo", "wow", "showcase", "fundable",
    ):
        from pocket.orchestrator import get_orchestrator

        if "wow" in low or "showcase" in low or "fundable" in low or j in ("wow_demo", "wow"):
            r = get_orchestrator().execute("wow_demo")
        elif "focused" in low or j == "focused_demo":
            from pocket.skills_real import run_focused_demo

            r = run_focused_demo()
        else:
            r = get_orchestrator().chat(prompt or "wow showcase fundable demo", record=True)
        return _fmt(r, "ARCHON · orchestrator"), "" if r.get("ok") else r.get("error", ""), "archon"

    if "outlook" in low or "email" in low or "draft" in low:
        return run_worker("TABELLARIUS", "outlook_draft", prompt=prompt, params=params)

    if "copilot" in low or low.startswith("introduce"):
        return run_worker("CONSILIARIUS", "introduce", prompt=prompt, params=params, cwd=cwd, session_job=job)

    if "analyze" in low or "brain" in low or "imagi" in low or "neuro" in low:
        return run_worker("REPOSITOR", "analyze", prompt=prompt, params=params)

    if "tweet" in low or "lookup" in low:
        from pocket.browser_mode import run_browser_job

        return run_browser_job(prompt, cwd=cwd, job=job or {})

    if "screenshot" in low:
        return run_worker("OCULUS", "screenshot", prompt="screenshot")

    if record and j == "orchestrate":
        from pocket.screen_record import run_recorded_demo

        r = run_recorded_demo(prompt)
        return _fmt(r, "ARCHON"), "" if r.get("ok") else r.get("error", ""), "archon"

    # default: browser freeform under ARCHON
    from pocket.browser_mode import run_browser_job

    text, err, eng = run_browser_job(prompt, cwd=cwd, job=job or {})
    return f"## ARCHON → NAVIGATOR/Browser\n\n{text}", err, "archon"


def _fmt(r: Dict[str, Any], title: str) -> str:
    return f"## {title}\n\n**{r.get('message') or ''}**\n\n```json\n{json.dumps(r, indent=2, default=str)[:6000]}\n```\n"


def run_alpha_job(prompt: str, *, cwd: str = "", job: Optional[Dict] = None) -> Tuple[str, str, str]:
    """Session mode=archon / alpha entry — natural language to ARCHON."""
    text = (prompt or "").strip()
    low = text.lower()
    if low in ("help", "workers", "list", "names"):
        lines = ["# Latin Python workers (alphas + specialists)\n"]
        for w in list_workers():
            lines.append(
                f"- **{w['id']}** ({w['latin']}) — {w['meaning']} · `{w['class']}` · jobs: {', '.join(w['jobs'][:6])}"
            )
        lines.append("\nGUPPY kept. Call: `ARCHON demo` · `SCRUTATOR analyze neuroemergence-core` · `CONSILIARIUS introduce`")
        return "\n".join(lines), "", "archon"

    # explicit WORKER job
    for wid in WORKERS:
        if low.startswith(wid.lower() + " ") or low == wid.lower():
            rest = text[len(wid) :].strip()
            job_name = rest.split()[0] if rest else "help"
            rest_prompt = rest[len(job_name) :].strip() if rest else ""
            return run_worker(wid, job_name if rest else "help", prompt=rest_prompt or rest, cwd=cwd, session_job=job)

    return run_worker("ARCHON", "orchestrate", prompt=text, cwd=cwd, session_job=job)
