"""AI Workspace — token-saving live context for every coding agent.

Activates per product workspace + optional session. Auto-updates as jobs run so
Grok / Codex / Claude / plan / WOA do not re-walk the whole tree every turn.

Layout (under ~/.pocket/ai_workspace/):
  {ws}/CONTEXT.md      — inject into agent prompts (compact)
  {ws}/SUMMARY.md      — rolling human+AI summary
  {ws}/INDEX.json      — shallow file index + mtimes
  {ws}/RECENT.jsonl    — last N events
  {ws}/sessions/{sid}/ — per coding-session overlays
  {ws}/previews/       — last preview snippets for the right rail

Internal: agents also leave hashed mesh artifacts via mesh_disk (existing bus).
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket" / "ai_workspace"
ROOT.mkdir(parents=True, exist_ok=True)
_lock = Lock()

# Cap inject size — this is the whole point (tokens)
CONTEXT_MAX_CHARS = 2800
SUMMARY_MAX_CHARS = 4000
INDEX_MAX_FILES = 80
RECENT_MAX = 40
SKIP_DIRS = {
    "node_modules",
    ".git",
    ".pnpm-store",
    "dist",
    "build",
    "target",
    "__pycache__",
    ".mops",
    ".old",
}


def _safe_ws(name: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9._-]+", "_", (name or "workspace").strip())[:64]
    return s or "workspace"


def ws_dir(workspace: str = "parallax") -> Path:
    d = ROOT / _safe_ws(workspace)
    d.mkdir(parents=True, exist_ok=True)
    (d / "sessions").mkdir(exist_ok=True)
    (d / "previews").mkdir(exist_ok=True)
    return d


def session_dir(workspace: str, session_id: str) -> Path:
    d = ws_dir(workspace) / "sessions" / _safe_ws(session_id or "anon")
    d.mkdir(parents=True, exist_ok=True)
    return d


def resolve_product_cwd(workspace: str = "", cwd: str = "") -> str:
    try:
        from pocket.executor import KNOWN_WORKSPACES, prefer_product_cwd, resolve_cwd

        if workspace:
            for w in KNOWN_WORKSPACES:
                if w["id"] == workspace or w["path"] == workspace:
                    p = Path(w["path"])
                    if p.is_dir():
                        return str(p.resolve())
        if cwd and Path(cwd).is_dir():
            return str(Path(cwd).resolve())
        return prefer_product_cwd(cwd or "")
    except Exception:
        return cwd or str(Path.home() / ".pocket" / "workspace")


def _shallow_index(root: str, *, max_files: int = INDEX_MAX_FILES) -> List[Dict[str, Any]]:
    base = Path(root)
    if not base.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    try:
        # top-level first
        for p in sorted(base.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if p.name.startswith(".") and p.name not in (".github",):
                if p.name in (".git", ".pnpm-store", ".mops", ".old"):
                    continue
            if p.is_dir() and p.name in SKIP_DIRS:
                continue
            try:
                st = p.stat()
                out.append(
                    {
                        "path": p.name + ("/" if p.is_dir() else ""),
                        "kind": "dir" if p.is_dir() else "file",
                        "bytes": st.st_size if p.is_file() else 0,
                        "mtime": st.st_mtime,
                    }
                )
            except OSError:
                continue
            if len(out) >= max_files // 2:
                break
        # second level for important product folders
        for sub in ("src", "docs", "scripts", "src/frontend/src", "src/backend"):
            sp = base / sub.replace("/", "\\") if "\\" in str(base) else base.joinpath(*sub.split("/"))
            if not sp.is_dir():
                continue
            for p in sorted(sp.iterdir(), key=lambda x: x.name.lower())[:18]:
                if p.name in SKIP_DIRS or p.name.startswith("."):
                    continue
                try:
                    st = p.stat()
                    rel = f"{sub}/{p.name}".replace("\\", "/")
                    if p.is_dir():
                        rel += "/"
                    out.append(
                        {
                            "path": rel,
                            "kind": "dir" if p.is_dir() else "file",
                            "bytes": st.st_size if p.is_file() else 0,
                            "mtime": st.st_mtime,
                        }
                    )
                except OSError:
                    continue
                if len(out) >= max_files:
                    break
            if len(out) >= max_files:
                break
    except Exception:
        pass
    return out[:max_files]


def _extractive_summary(
    *,
    prompt: str,
    result: str,
    engine: str,
    mode: str,
    prior: str = "",
) -> str:
    """Cheap summary — no LLM. Saves tokens for the next turn."""
    p = " ".join((prompt or "").split())[:280]
    # Prefer polished tail of agent reply
    r = (result or "").strip()
    # drop engine headers
    lines = [
        ln
        for ln in r.splitlines()
        if ln.strip()
        and not ln.strip().startswith("[engine=")
        and not ln.strip().startswith("[cli=")
        and not ln.strip().startswith("[research_package=")
        and not ln.strip().startswith("[pocket_session=")
        and not ln.strip().startswith("[stream_tokens")
        and not ln.strip().startswith("[llm_tokens")
    ]
    body = "\n".join(lines)
    # keep last substantive chunk
    if len(body) > 900:
        body = body[-900:]
    body = " ".join(body.split())[:700]
    stamp = time.strftime("%Y-%m-%d %H:%M")
    block = (
        f"### {stamp} · {mode}/{engine or '?'}\n"
        f"**User:** {p or '(empty)'}\n"
        f"**Agent:** {body or '(no text)'}\n"
    )
    if prior:
        # keep newest first
        merged = block + "\n" + prior
    else:
        merged = block
    return merged[:SUMMARY_MAX_CHARS]


def _build_context_md(meta: Dict[str, Any]) -> str:
    files = meta.get("index") or []
    file_lines = "\n".join(
        f"- `{f.get('path')}`" for f in files[:35]
    )
    recent = meta.get("recent_events") or []
    recent_lines = "\n".join(
        f"- {e.get('at_h','')}: {e.get('mode','')} · {(e.get('prompt_snip') or '')[:90]}"
        for e in recent[:8]
    )
    summary_snip = (meta.get("summary_snip") or "")[:1200]
    return (
        f"# AI Workspace · {meta.get('workspace')}\n\n"
        f"> Auto-maintained. **Do not re-list the whole repo** unless a path is missing.\n"
        f"> Posture: paper/testnet-first for PARALLAX. Prefer diffs over re-reads.\n\n"
        f"## Now\n"
        f"- **cwd:** `{meta.get('cwd')}`\n"
        f"- **session:** `{meta.get('session_id') or '—'}`\n"
        f"- **mode:** `{meta.get('last_mode') or '—'}` · engine `{meta.get('last_engine') or '—'}`\n"
        f"- **updated:** {meta.get('updated_h')}\n"
        f"- **token_hint:** use this CONTEXT + SUMMARY; avoid full-tree `rg --files` / Get-ChildItem -Recurse\n\n"
        f"## Rolling summary (newest first)\n{summary_snip or '_none yet_'}\n\n"
        f"## Tree snapshot (shallow)\n{file_lines or '_empty_'}\n\n"
        f"## Recent jobs\n{recent_lines or '_none_'}\n\n"
        f"## Agent bus\n"
        f"- Mesh: hashed envelopes on POCKET_MESH (inbox/outbox/artifacts)\n"
        f"- Channel: `freq-coding` for coding-agent swarm notes\n"
        f"- Leave artifacts instead of re-explaining prior work\n"
        f"- Offload multi-step real-world work: POST /v1/offload (free the chat turn)\n"
        f"- Capability map: see CAPABILITIES section below\n\n"
        f"## Capabilities (live snip)\n"
        f"{meta.get('caps_snip') or '_see GET /v1/capabilities_'}\n"
    )[:CONTEXT_MAX_CHARS]


def _append_recent(ws: Path, event: Dict[str, Any]) -> None:
    path = ws / "RECENT.jsonl"
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")
    # trim
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) > RECENT_MAX * 2:
            path.write_text("\n".join(lines[-RECENT_MAX:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def _read_recent(ws: Path, limit: int = 12) -> List[Dict[str, Any]]:
    path = ws / "RECENT.jsonl"
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return list(reversed(out))


def refresh_index(workspace: str = "parallax", cwd: str = "") -> Dict[str, Any]:
    product = resolve_product_cwd(workspace, cwd)
    idx = _shallow_index(product)
    ws = ws_dir(workspace)
    payload = {
        "workspace": _safe_ws(workspace),
        "cwd": product,
        "indexed_at": time.time(),
        "files": idx,
        "count": len(idx),
    }
    (ws / "INDEX.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def touch_from_job(job: Dict[str, Any]) -> Dict[str, Any]:
    """Call after every finished job — auto-update workspace (no LLM)."""
    workspace = (job.get("workspace") or "parallax") or "parallax"
    sid = (job.get("session_id") or "").strip()
    cwd = (job.get("cwd") or "").strip()
    prompt = job.get("prompt") or ""
    result = job.get("result") or ""
    engine = job.get("engine") or ""
    mode = job.get("mode") or ""
    product = resolve_product_cwd(workspace, cwd)

    with _lock:
        ws = ws_dir(workspace)
        # index (throttled: refresh if missing or older than 10 min)
        idx_path = ws / "INDEX.json"
        need_idx = True
        if idx_path.exists():
            try:
                old = json.loads(idx_path.read_text(encoding="utf-8"))
                if time.time() - float(old.get("indexed_at") or 0) < 600:
                    need_idx = False
                    idx_files = old.get("files") or []
                else:
                    idx_files = []
            except Exception:
                idx_files = []
        else:
            idx_files = []
        if need_idx:
            idx_payload = refresh_index(workspace, product)
            idx_files = idx_payload.get("files") or []

        prior_sum = ""
        sum_path = ws / "SUMMARY.md"
        if sum_path.exists():
            prior_sum = sum_path.read_text(encoding="utf-8", errors="replace")
        summary = _extractive_summary(
            prompt=prompt,
            result=result,
            engine=str(engine),
            mode=str(mode),
            prior=prior_sum,
        )
        sum_path.write_text(summary, encoding="utf-8")

        event = {
            "at": time.time(),
            "at_h": time.strftime("%H:%M:%S"),
            "session_id": sid,
            "mode": mode,
            "engine": engine,
            "status": job.get("status"),
            "prompt_snip": " ".join(prompt.split())[:160],
            "result_snip": " ".join((result or "").split())[:200],
            "job_id": job.get("id"),
        }
        _append_recent(ws, event)
        recent = _read_recent(ws)

        caps_snip = ""
        try:
            from pocket.capability_map import capability_markdown

            caps_snip = capability_markdown()[:900]
        except Exception:
            caps_snip = ""
        meta = {
            "workspace": _safe_ws(workspace),
            "cwd": product,
            "session_id": sid,
            "last_mode": mode,
            "last_engine": engine,
            "updated": time.time(),
            "updated_h": time.strftime("%Y-%m-%d %H:%M:%S"),
            "index": idx_files,
            "recent_events": recent,
            "summary_snip": summary[:1400],
            "caps_snip": caps_snip,
        }
        ctx = _build_context_md(meta)
        (ws / "CONTEXT.md").write_text(ctx, encoding="utf-8")
        (ws / "STATE.json").write_text(json.dumps(meta, indent=2, default=str), encoding="utf-8")

        # session overlay
        if sid:
            sd = session_dir(workspace, sid)
            (sd / "SUMMARY.md").write_text(summary[:3000], encoding="utf-8")
            (sd / "LAST.json").write_text(json.dumps(event, indent=2), encoding="utf-8")
            (sd / "CONTEXT.md").write_text(ctx, encoding="utf-8")

        # preview snippet of last agent prose
        prev = (ws / "previews" / "last_agent.md")
        prev.write_text(
            f"# Last agent output · {mode}/{engine}\n\n"
            f"**Prompt:** {event['prompt_snip']}\n\n"
            f"{(result or '')[-3500:]}\n",
            encoding="utf-8",
        )

        # mesh: leave artifact for swarm (hashed identity already in mesh_disk)
        try:
            from pocket.mesh_disk import leave_artifact, send_message

            agent = (engine or mode or "AGENT").upper().replace("-", "_")[:24] or "AGENT"
            leave_artifact(
                agent,
                f"session_{(sid or 'na')[:10]}_note.md",
                f"# Handoff note\n\n{event['prompt_snip']}\n\n{(result or '')[:1500]}\n",
                notify=["ARCHON", "SHIP_HEADLESS"] if mode in ("grok", "codex", "claude") else None,
            )
            send_message(
                agent,
                "ARCHON",
                f"job done mode={mode} session={sid[:12] if sid else '—'} :: {event['prompt_snip'][:120]}",
                channel="freq-coding",
                kind="handoff",
            )
        except Exception:
            pass

        return {
            "ok": True,
            "workspace": meta["workspace"],
            "cwd": product,
            "context_chars": len(ctx),
            "summary_chars": len(summary),
            "index_files": len(idx_files),
            "session_id": sid,
        }


def get_context_block(
    workspace: str = "parallax",
    *,
    session_id: str = "",
    cwd: str = "",
    max_chars: int = CONTEXT_MAX_CHARS,
) -> str:
    """Compact block to prepend/append to agent prompts — primary token saver."""
    ws = ws_dir(workspace)
    # prefer session overlay
    if session_id:
        sp = session_dir(workspace, session_id) / "CONTEXT.md"
        if sp.exists():
            t = sp.read_text(encoding="utf-8", errors="replace")
            if t.strip():
                return t[:max_chars]
    cp = ws / "CONTEXT.md"
    if cp.exists():
        t = cp.read_text(encoding="utf-8", errors="replace")
        if t.strip():
            return t[:max_chars]
    # bootstrap empty workspace
    product = resolve_product_cwd(workspace, cwd)
    refresh_index(workspace, product)
    meta = {
        "workspace": _safe_ws(workspace),
        "cwd": product,
        "session_id": session_id,
        "last_mode": "",
        "last_engine": "",
        "updated_h": time.strftime("%Y-%m-%d %H:%M:%S"),
        "index": _shallow_index(product),
        "recent_events": [],
        "summary_snip": "_first turn — index only_",
    }
    ctx = _build_context_md(meta)
    (ws / "CONTEXT.md").write_text(ctx, encoding="utf-8")
    return ctx[:max_chars]


def get_workspace_view(
    workspace: str = "parallax",
    *,
    session_id: str = "",
) -> Dict[str, Any]:
    """Right-rail payload: summary, previews, index, bus hints."""
    ws = ws_dir(workspace)
    state = {}
    if (ws / "STATE.json").exists():
        try:
            state = json.loads((ws / "STATE.json").read_text(encoding="utf-8"))
        except Exception:
            state = {}
    summary = ""
    if (ws / "SUMMARY.md").exists():
        summary = (ws / "SUMMARY.md").read_text(encoding="utf-8", errors="replace")[:2500]
    if session_id:
        sp = session_dir(workspace, session_id) / "SUMMARY.md"
        if sp.exists():
            summary = sp.read_text(encoding="utf-8", errors="replace")[:2500]

    previews: List[Dict[str, Any]] = []
    prev_dir = ws / "previews"
    if prev_dir.is_dir():
        for p in sorted(prev_dir.glob("*"), key=lambda x: x.stat().st_mtime, reverse=True)[:8]:
            try:
                text = p.read_text(encoding="utf-8", errors="replace")[:1200]
            except Exception:
                text = ""
            previews.append(
                {
                    "name": p.name,
                    "path": str(p),
                    "preview": text,
                    "mtime": p.stat().st_mtime,
                }
            )

    # mesh bus tail
    bus: List[Dict[str, Any]] = []
    try:
        from pocket.mesh_disk import channel_tail

        bus = (channel_tail("freq-coding", limit=12).get("messages") or [])[-12:]
        # decrypt for UI if present
        for m in bus:
            if m.get("body_cipher") and not m.get("body_plain"):
                try:
                    from pocket.mesh_disk import decrypt_body

                    m["body_plain"] = decrypt_body(m["body_cipher"])
                except Exception:
                    pass
    except Exception:
        bus = []

    return {
        "ok": True,
        "workspace": _safe_ws(workspace),
        "session_id": session_id or "",
        "cwd": state.get("cwd") or resolve_product_cwd(workspace),
        "summary": summary,
        "summary_html_ready": True,
        "context_chars": len(get_context_block(workspace, session_id=session_id) or ""),
        "index": state.get("index") or [],
        "recent": _read_recent(ws, 10),
        "previews": previews,
        "bus": [
            {
                "from": m.get("from"),
                "to": m.get("to"),
                "kind": m.get("kind"),
                "body": (m.get("body_plain") or m.get("body") or "")[:240],
                "at": m.get("at"),
                "hmac": (m.get("hmac_sha256") or "")[:16],
            }
            for m in bus
        ],
        "token_tips": [
            "CONTEXT.md is injected automatically — don't re-list the tree",
            "Use mesh artifacts for cross-agent handoffs instead of pasting long history",
            "Prefer path-scoped reads over recursive repo walks",
            "Subagents live on the right rail — activate with @ only when needed",
        ],
        "updated": state.get("updated"),
        "updated_h": state.get("updated_h"),
    }


def inject_for_prompt(
    base_prompt: str,
    *,
    workspace: str = "parallax",
    session_id: str = "",
    cwd: str = "",
) -> str:
    """Wrap a user/system prompt with workspace context (token-efficient)."""
    block = get_context_block(workspace, session_id=session_id, cwd=cwd)
    if not block.strip():
        return base_prompt
    return (
        f"{base_prompt.rstrip()}\n\n"
        f"---\n"
        f"## AI_WORKSPACE (auto · do not re-scan whole repo)\n"
        f"{block}\n"
        f"---\n"
    )
