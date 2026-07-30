"""COWORK mode — desktop embodiment for demos, not deep coding.

Agents (Grok/Codex/Claude workers via host) use the desk: open apps, record screen,
screenshot, notes, light file deliverables. Planning stays in plan mode; this is *working*.
"""

from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit


def _parse_steps(prompt: str) -> List[Dict[str, Any]]:
    """Cheap deterministic plan — no LLM."""
    p = (prompt or "").strip()
    low = p.lower()
    steps: List[Dict[str, Any]] = []

    want_record = any(
        w in low
        for w in ("record", "demo", "video", "screen record", "capture demo", "film")
    )
    if want_record:
        steps.append({"action": "record_start", "label": "cowork"})

    steps.append({"action": "capability_snapshot"})

    # open apps / urls
    m_url = re.search(r"https?://[^\s]+", p)
    if m_url or "browser" in low or "edge" in low or "open site" in low:
        url = m_url.group(0) if m_url else "https://example.com"
        steps.append({"action": "browser", "url": url})

    for app in ("notepad", "code", "calc", "excel", "word", "paint", "explorer"):
        if re.search(rf"\bopen\s+{app}\b", low) or re.search(rf"\b{app}\b", low) and "open" in low:
            steps.append({"action": "open_app", "app": app})

    if "screenshot" in low or "shot" in low or want_record:
        steps.append({"action": "screenshot"})

    # light deliverable note (code-adjacent but not deep refactor)
    if any(w in low for w in ("write", "draft", "deliver", "note", "readme", "script")):
        steps.append({"action": "deliver_note", "text": p[:1500]})

    steps.append({"action": "note", "text": f"cowork: {p[:400]}"})

    if want_record:
        steps.append({"action": "record_stop"})

    # always at least a short loop
    if len(steps) < 2:
        steps = [
            {"action": "capability_snapshot"},
            {"action": "screenshot"},
            {"action": "note", "text": p or "cowork idle check"},
        ]
    return steps[:14]


def _dispatch(step: Dict[str, Any]) -> Dict[str, Any]:
    act = (step.get("action") or "").lower()
    if act == "record_start":
        from pocket.screen_record import record_start

        return {**record_start(label=step.get("label") or "cowork"), "action": act}
    if act == "record_stop":
        from pocket.screen_record import record_stop

        return {**record_stop(), "action": act}
    if act == "deliver_note":
        # Platform deliverable — prefer tenant space when job owner is a market seat
        body = step.get("text") or ""
        owner = (step.get("owner") or "").strip().lower()
        if owner:
            try:
                from pocket.platform_space import tenant_cwd

                root = Path(tenant_cwd(owner, "deliverables"))
            except Exception:
                root = Path.home() / ".pocket" / "workspace" / "cowork_deliverables"
        else:
            root = Path.home() / ".pocket" / "workspace" / "cowork_deliverables"
        root.mkdir(parents=True, exist_ok=True)
        path = root / f"note-{int(time.time())}.md"
        path.write_text(
            f"# Cowork deliverable (platform space)\n\n{body}\n\n"
            f"_POCKET virtual workspace — not operator host files_\n",
            encoding="utf-8",
        )
        return {"ok": True, "action": act, "path": str(path), "message": f"Wrote {path}"}
    # Host embodiment (screenshot / open apps) — founder only
    if step.get("host_power") is False or step.get("platform_only"):
        return {
            "ok": False,
            "action": act,
            "error": "Host PC actions blocked for market seats. Use platform files/git space.",
        }
    from pocket.embodiment import dispatch_action

    return dispatch_action(step)


def run_cowork(
    prompt: str,
    *,
    record: Optional[bool] = None,
    agent: str = "COWORK",
    cwd: str = "",
    owner: str = "",
    host_power: bool = True,
) -> Dict[str, Any]:
    emit("cowork", f"start {(prompt or '')[:100]}", agent=agent, role="host" if host_power else "platform")
    # Market seats: virtual deliverables only — no host screen/apps
    if not host_power:
        steps = [
            {"action": "deliver_note", "text": prompt or "cowork note", "owner": owner, "platform_only": True},
            {"action": "note", "text": f"platform cowork: {(prompt or '')[:400]}", "platform_only": True},
        ]
        results = []
        for step in steps:
            if step.get("action") == "note":
                results.append({"ok": True, "action": "note", "text": step.get("text")})
            else:
                results.append(_dispatch({**step, "owner": owner, "host_power": False, "platform_only": True}))
        proof = {
            "schema": "pocket.cowork.v1",
            "ok": True,
            "platform_only": True,
            "owner": owner,
            "cwd": cwd,
            "summary": "Platform cowork wrote to virtual space (no host PC).",
            "results": results,
        }
        return proof
    steps = _parse_steps(prompt)
    if record is True and not any(s.get("action") == "record_start" for s in steps):
        steps = [{"action": "record_start", "label": "cowork"}] + steps + [{"action": "record_stop"}]
    if record is False:
        steps = [s for s in steps if s.get("action") not in ("record_start", "record_stop")]

    log: List[Dict[str, Any]] = []
    t0 = time.time()
    ok_n = 0
    for i, step in enumerate(steps):
        r = _dispatch(step)
        r["i"] = i
        log.append(r)
        if r.get("ok") or r.get("already"):
            ok_n += 1
        time.sleep(0.25)

    # proof pack via embodiment helper pattern
    try:
        import json
        from pathlib import Path as _P

        pd = _P.home() / ".pocket" / "proofs" / f"{int(time.time())}_{agent[:40]}"
        pd.mkdir(parents=True, exist_ok=True)
        summary = f"Cowork {ok_n}/{len(log)} · {(prompt or '')[:120]}"
        proof = {
            "schema": "pocket.cowork.v1",
            "goal": prompt,
            "ok": ok_n >= max(1, len(log) // 2),
            "ok_steps": ok_n,
            "total": len(log),
            "duration_sec": round(time.time() - t0, 2),
            "log": log,
            "dir": str(pd),
        }
        (pd / "cowork.json").write_text(json.dumps(proof, indent=2, default=str), encoding="utf-8")
        md = [f"# Cowork proof\n\n**Goal:** {prompt}\n\n## Steps\n"]
        for r in log:
            md.append(
                f"- `{r.get('action')}` · {'ok' if r.get('ok') or r.get('already') else 'fail'} · "
                f"{(r.get('message') or r.get('error') or '')[:140]}"
            )
        (pd / "COWORK.md").write_text("\n".join(md), encoding="utf-8")
        proof["summary"] = summary
        proof["proof_md"] = "\n".join(md)
    except Exception as e:
        proof = {
            "ok": ok_n > 0,
            "summary": f"Cowork {ok_n}/{len(log)} (proof err: {e})",
            "log": log,
        }

    try:
        from pocket.mesh_disk import leave_artifact, send_message

        leave_artifact(
            agent,
            f"cowork_{int(time.time())}.md",
            proof.get("proof_md") or proof.get("summary") or "",
            notify=["ARCHON", "USER"],
        )
        send_message(agent, "ARCHON", proof.get("summary") or "cowork done", channel="freq-coding", kind="cowork")
    except Exception:
        pass

    emit("cowork", proof.get("summary") or "done", agent=agent, role="host")
    return proof


def run_cowork_job(prompt: str, cwd: str = "", job: Optional[Dict] = None) -> Tuple[str, str, str]:
    job = job or {}
    rec = None
    low = (prompt or "").lower()
    owner = (job.get("owner") or "").strip().lower()
    host_power = bool(job.get("host_power"))
    if "no record" in low or "without record" in low:
        rec = False
    elif host_power and ("record" in low or "demo" in low):
        rec = True
    else:
        rec = False if not host_power else rec
    r = run_cowork(
        prompt,
        record=rec,
        agent=(job.get("mode") or "COWORK").upper(),
        cwd=cwd,
        owner=owner,
        host_power=host_power,
    )
    if r.get("platform_only"):
        body = (
            f"## Platform cowork\n\n"
            f"{r.get('summary') or ''}\n\n"
            f"Wrote into **your virtual space** (not the operator PC).\n"
            f"**cwd:** `{cwd}`\n"
        )
        for step in (r.get("results") or [])[:10]:
            body += f"- `{step.get('action')}`: {(step.get('message') or step.get('error') or '')[:120]}\n"
        return body, "", "cowork"
    body = (
        f"## Cowork session (host)\n\n"
        f"{r.get('summary') or ''}\n\n"
        f"**Recorded / steps:** {r.get('ok_steps')}/{r.get('total')}\n"
        f"**Proof:** `{r.get('dir') or '—'}`\n\n"
        f"Host mode: desktop embodiment for the **founder/operator** machine only.\n"
    )
    for step in (r.get("log") or [])[:10]:
        body += f"- `{step.get('action')}`: {(step.get('message') or step.get('error') or '')[:120]}\n"
    return body, ("" if r.get("ok") else r.get("error") or "cowork partial"), "cowork"
