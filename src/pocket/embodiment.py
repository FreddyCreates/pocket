"""Unified real-world embodiment toolkit for coding agents.

One surface: capability snapshot, desktop apps, browser open, screenshot,
safe shell note, file peek, proof packs. Prefer offload_queue for multi-step.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

PROOF_ROOT = Path.home() / ".pocket" / "proofs"
PROOF_ROOT.mkdir(parents=True, exist_ok=True)


def _proof_dir(tag: str) -> Path:
    d = PROOF_ROOT / f"{int(time.time())}_{tag[:40]}"
    d.mkdir(parents=True, exist_ok=True)
    return d


def action_capability_snapshot() -> Dict[str, Any]:
    from pocket.capability_map import build_capability_map, capability_markdown

    cmap = build_capability_map()
    md = capability_markdown(cmap)
    return {"ok": True, "action": "capability_snapshot", "map": cmap, "markdown": md, "message": md[:500]}


def action_screenshot() -> Dict[str, Any]:
    try:
        from pocket.capture import run_capture_job

        text, err, eng = run_capture_job("screenshot")
        return {
            "ok": not bool(err),
            "action": "screenshot",
            "result": (text or "")[:4000],
            "error": err or "",
            "engine": eng,
            "message": "screenshot captured" if not err else err,
        }
    except Exception as e:
        # fallback: try vision frame
        try:
            from pocket.live_vision import latest_frame

            fr = latest_frame(include_image=False)
            return {
                "ok": bool(fr.get("path")),
                "action": "screenshot",
                "path": fr.get("path"),
                "message": f"vision frame {fr.get('path')}",
            }
        except Exception as e2:
            return {"ok": False, "action": "screenshot", "error": f"{e}; {e2}"}


def action_open_app(app: str = "notepad", url: str = "") -> Dict[str, Any]:
    try:
        from pocket.desktop import run_desktop_job

        prompt = f"open {app}" + (f" {url}" if url else "")
        text, err, eng = run_desktop_job(prompt)
        return {
            "ok": not bool(err),
            "action": "open_app",
            "app": app,
            "result": (text or "")[:3000],
            "error": err or "",
            "message": text[:200] if text else (err or "opened"),
        }
    except Exception as e:
        return {"ok": False, "action": "open_app", "error": str(e)}


def action_browser(url: str = "https://example.com") -> Dict[str, Any]:
    u = (url or "").strip()
    if not u.startswith("http"):
        u = "https://" + u
    return action_open_app("edge", u)


def action_file_peek(path: str, *, max_chars: int = 2000) -> Dict[str, Any]:
    p = Path(path)
    if not p.is_file():
        return {"ok": False, "action": "file_peek", "error": f"not a file: {path}"}
    try:
        # safety: only under known roots
        roots = [
            Path.home() / "OneDrive" / "pocket-os",
            Path(r"E:\PARALLAX-Exchange-Clearinghouse"),
            Path.home() / ".pocket",
        ]
        resolved = p.resolve()
        if not any(str(resolved).lower().startswith(str(r.resolve()).lower()) for r in roots if r.exists()):
            return {"ok": False, "action": "file_peek", "error": "path outside allow roots"}
        text = resolved.read_text(encoding="utf-8", errors="replace")[:max_chars]
        return {
            "ok": True,
            "action": "file_peek",
            "path": str(resolved),
            "preview": text,
            "message": f"read {resolved.name} ({len(text)} chars)",
        }
    except Exception as e:
        return {"ok": False, "action": "file_peek", "error": str(e)}


def action_note(text: str) -> Dict[str, Any]:
    return {"ok": True, "action": "note", "text": (text or "")[:2000], "message": "note stored"}


def action_list_apps() -> Dict[str, Any]:
    try:
        from pocket.safety import ALLOWED_APPS

        apps = sorted(ALLOWED_APPS)
        return {"ok": True, "action": "list_apps", "apps": apps, "message": f"{len(apps)} apps"}
    except Exception as e:
        return {"ok": False, "action": "list_apps", "error": str(e)}


def action_workspace_refresh(workspace: str = "parallax") -> Dict[str, Any]:
    try:
        from pocket.ai_workspace import get_context_block, refresh_index

        refresh_index(workspace)
        ctx = get_context_block(workspace)
        return {
            "ok": True,
            "action": "workspace_refresh",
            "context_chars": len(ctx),
            "message": f"workspace {workspace} refreshed",
        }
    except Exception as e:
        return {"ok": False, "action": "workspace_refresh", "error": str(e)}


def dispatch_action(step: Dict[str, Any]) -> Dict[str, Any]:
    act = (step.get("action") or step.get("skill") or step.get("op") or "note").lower().strip()
    if act in ("capability_snapshot", "capabilities", "caps"):
        return action_capability_snapshot()
    if act in ("screenshot", "screen", "capture"):
        return action_screenshot()
    if act in ("open", "open_app", "app"):
        return action_open_app(step.get("app") or step.get("name") or "notepad", step.get("url") or "")
    if act in ("browser", "edge", "url"):
        return action_browser(step.get("url") or step.get("text") or "https://example.com")
    if act in ("file_peek", "read", "peek"):
        return action_file_peek(step.get("path") or step.get("file") or "")
    if act in ("list_apps", "apps"):
        return action_list_apps()
    if act in ("workspace_refresh", "refresh_ws"):
        return action_workspace_refresh(step.get("workspace") or "parallax")
    if act in ("note", "log"):
        return action_note(step.get("text") or step.get("prompt") or "")
    return {"ok": False, "action": act, "error": f"unknown action {act}"}


def run_embodiment_plan(
    goal: str,
    *,
    steps: Optional[List[Dict[str, Any]]] = None,
    agent: str = "AI",
    workspace: str = "parallax",
) -> Dict[str, Any]:
    """Run a short real-world plan and write a proof pack."""
    plan = list(steps or [])
    if not plan:
        plan = [
            {"action": "capability_snapshot"},
            {"action": "screenshot"},
            {"action": "note", "text": goal},
        ]
    log: List[Dict[str, Any]] = []
    t0 = time.time()
    ok_n = 0
    for i, step in enumerate(plan[:12]):
        r = dispatch_action(step)
        r["i"] = i
        r["ms"] = int((time.time() - t0) * 1000)
        log.append(r)
        if r.get("ok"):
            ok_n += 1

    proof_dir = _proof_dir(agent)
    proof = {
        "schema": "pocket.proof-pack.v1",
        "goal": goal,
        "agent": agent,
        "workspace": workspace,
        "ok": ok_n == len(log) and len(log) > 0,
        "ok_steps": ok_n,
        "total": len(log),
        "duration_sec": round(time.time() - t0, 2),
        "log": log,
        "dir": str(proof_dir),
        "at": time.time(),
    }
    (proof_dir / "proof.json").write_text(json.dumps(proof, indent=2, default=str), encoding="utf-8")
    md_lines = [
        f"# Proof pack · {agent}",
        "",
        f"**Goal:** {goal}",
        f"**OK:** {proof['ok_steps']}/{proof['total']} · {proof['duration_sec']}s",
        f"**Dir:** `{proof_dir}`",
        "",
        "## Steps",
    ]
    for r in log:
        md_lines.append(
            f"- `{r.get('action')}` · {'ok' if r.get('ok') else 'fail'} · {(r.get('message') or r.get('error') or '')[:160]}"
        )
    # attach capability markdown if present
    for r in log:
        if r.get("action") == "capability_snapshot" and r.get("markdown"):
            md_lines.extend(["", "## Capability snapshot", "", r["markdown"][:2500]])
            break
    proof_md = "\n".join(md_lines)
    (proof_dir / "PROOF.md").write_text(proof_md, encoding="utf-8")
    proof["proof_md"] = proof_md
    proof["summary"] = (
        f"Embodiment {ok_n}/{len(log)} · goal={(goal or '')[:120]} · proof={proof_dir}"
    )
    return proof
