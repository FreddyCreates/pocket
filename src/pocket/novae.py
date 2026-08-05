"""NOVAE agents — live Grok / Codex instances in platform workspace.

Founder uses them as lab hands (browser + physical host when host_power).
Market seats use them only inside their tenant sandbox — never founder disk.

  GROK_NOVAE  — research, plan, compose, web-facing hands
  CODEX_NOVAE — coding, forge, workspace edits

Activate from desk or phone; they keep workspace state under ~/.pocket/novae/
and mesh identity under the virtual mesh disk.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket" / "novae"
ROOT.mkdir(parents=True, exist_ok=True)
_lock = Lock()

NOVAE_DEFS = {
    "GROK_NOVAE": {
        "id": "GROK_NOVAE",
        "engine": "grok",
        "mode": "novae_grok",
        "title": "Grok Novae",
        "role": "hands",
        "color": "#a78bfa",
        "tagline": "Browser + research hands · plan · compose · real-world assist",
        "worlds": ["browser", "web", "plan", "physical_assist"],
    },
    "CODEX_NOVAE": {
        "id": "CODEX_NOVAE",
        "engine": "codex",
        "mode": "novae_codex",
        "title": "Codex Novae",
        "role": "hands",
        "color": "#34d399",
        "tagline": "Coding hands · forge · workspace · ship patches",
        "worlds": ["code", "forge", "workspace", "git"],
    },
}


def _state_path(nid: str) -> Path:
    return ROOT / f"{nid.lower()}.json"


def _ws_root(nid: str) -> Path:
    p = ROOT / "workspaces" / nid.lower()
    p.mkdir(parents=True, exist_ok=True)
    for sub in ("files", "plans", "code", "proofs", "notes"):
        (p / sub).mkdir(exist_ok=True)
    readme = p / "NOVAE.md"
    if not readme.exists():
        meta = NOVAE_DEFS.get(nid.upper(), {})
        readme.write_text(
            f"# {meta.get('title', nid)}\n\n"
            f"Platform workspace for this Novae instance.\n"
            f"engine={meta.get('engine')}\n"
            f"role=hands (browser + physical only when founder host_power)\n",
            encoding="utf-8",
        )
    return p


def _load(nid: str) -> Dict[str, Any]:
    nid = nid.upper()
    base = dict(NOVAE_DEFS.get(nid) or {})
    if not base:
        return {}
    fp = _state_path(nid)
    if fp.exists():
        try:
            data = json.loads(fp.read_text(encoding="utf-8"))
            base.update(data)
        except Exception:
            pass
    base.setdefault("id", nid)
    base.setdefault("active", False)
    base.setdefault("activations", 0)
    base.setdefault("runs", 0)
    base.setdefault("last_at", 0)
    base.setdefault("last_goal", "")
    base.setdefault("session_id", "")
    base["workspace"] = str(_ws_root(nid))
    return base


def _save(state: Dict[str, Any]) -> None:
    nid = (state.get("id") or "").upper()
    if not nid:
        return
    fp = _state_path(nid)
    slim = {
        "id": nid,
        "active": bool(state.get("active")),
        "activations": int(state.get("activations") or 0),
        "runs": int(state.get("runs") or 0),
        "last_at": state.get("last_at") or 0,
        "last_goal": (state.get("last_goal") or "")[:400],
        "session_id": state.get("session_id") or "",
        "owner": state.get("owner") or "",
        "edition": state.get("edition") or "founder",
    }
    fp.write_text(json.dumps(slim, indent=2), encoding="utf-8")


def list_novae(*, owner: str = "") -> List[Dict[str, Any]]:
    out = []
    for nid in NOVAE_DEFS:
        st = _load(nid)
        if owner and st.get("owner") and st.get("owner") != owner:
            # still show template; activation is per-user via session
            pass
        out.append(public_view(st))
    return out


def public_view(st: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": st.get("id"),
        "title": st.get("title"),
        "engine": st.get("engine"),
        "mode": st.get("mode"),
        "role": st.get("role"),
        "color": st.get("color"),
        "tagline": st.get("tagline"),
        "worlds": st.get("worlds") or [],
        "active": bool(st.get("active")),
        "activations": int(st.get("activations") or 0),
        "runs": int(st.get("runs") or 0),
        "last_at": st.get("last_at") or 0,
        "last_goal": st.get("last_goal") or "",
        "session_id": st.get("session_id") or "",
        "workspace": st.get("workspace"),
        "hands": {
            "browser": True,
            "platform_workspace": True,
            "physical_host": "founder only",
        },
    }


def get_novae(nid: str) -> Optional[Dict[str, Any]]:
    st = _load(nid)
    return public_view(st) if st else None


def activate(
    nid: str,
    *,
    owner: str = "pocket",
    edition: str = "founder",
    goal: str = "",
    host_power: bool = False,
) -> Dict[str, Any]:
    """Mark Novae active, ensure mesh identity + workspace, optional session."""
    nid = (nid or "").upper()
    if nid not in NOVAE_DEFS:
        return {"ok": False, "error": f"unknown novae {nid}"}
    with _lock:
        st = _load(nid)
        st["active"] = True
        st["activations"] = int(st.get("activations") or 0) + 1
        st["last_at"] = time.time()
        st["last_goal"] = (goal or st.get("last_goal") or "standby")[:400]
        st["owner"] = owner
        st["edition"] = edition
        ws = _ws_root(nid)
        # mesh identity (hands in the swarm)
        try:
            from pocket.mesh_disk import ensure_agent, leave_artifact

            ensure_agent(nid)
            leave_artifact(
                nid,
                "activate",
                {
                    "goal": st["last_goal"],
                    "owner": owner,
                    "edition": edition,
                    "host_power": bool(host_power and edition == "founder"),
                    "workspace": str(ws),
                    "ts": time.time(),
                },
            )
        except Exception:
            pass
        # start / reuse desk session bound to this novae mode
        try:
            from pocket.sessions import create_session, get as get_session

            sid = st.get("session_id") or ""
            sess = get_session(sid) if sid else None
            if not sess:
                sess = create_session(
                    mode=st.get("mode") or "novae_grok",
                    title=st.get("title") or nid,
                    workspace=str(ws),
                    cwd=str(ws / "files"),
                    owner=owner,
                )
                st["session_id"] = sess.get("id") or ""
            else:
                # keep cwd on novae workspace
                sess["cwd"] = str(ws / "files")
                sess["workspace"] = str(ws)
                from pocket.sessions import save as save_sess

                save_sess(sess)
        except Exception as e:
            st["session_error"] = str(e)[:200]
        _save(st)
        view = public_view(st)
        view["ok"] = True
        view["host_power"] = bool(host_power and edition == "founder")
        view["note"] = (
            "Founder: Novae can use host hands when you enable host_power. "
            "Market: sandbox only — never founder personal disk."
            if edition == "founder"
            else "Market Novae: platform workspace only (your tenant sandbox)."
        )
        return view


def deactivate(nid: str) -> Dict[str, Any]:
    nid = (nid or "").upper()
    if nid not in NOVAE_DEFS:
        return {"ok": False, "error": f"unknown novae {nid}"}
    with _lock:
        st = _load(nid)
        st["active"] = False
        st["last_at"] = time.time()
        _save(st)
        return {"ok": True, **public_view(st)}


def system_preamble(kind: str, *, host_power: bool, edition: str) -> str:
    kind = (kind or "grok").lower()
    name = "GROK_NOVAE" if kind == "grok" else "CODEX_NOVAE"
    hands = (
        "You have founder host hands when asked: browser, desk apps, capture, "
        "and physical-world assist via host tools. Never expose founder secrets."
        if host_power and edition == "founder"
        else "You operate only in platform workspace / tenant sandbox. "
        "No founder personal disk. No host shell/desktop of the operator PC."
    )
    if kind == "codex":
        return (
            f"You are {name} — a Codex Novae instance (coding hands) inside POCKET. "
            f"Prefer workspace files under the Novae code/ tree. Ship real patches. "
            f"{hands} Be concise. Mark steps. Work like a senior pair-programmer on the go."
        )
    return (
        f"You are {name} — a Grok Novae instance (research + day-ops hands) inside POCKET. "
        f"Plan, code-light assist, browser research, and real-world task coaching. "
        f"{hands} Be sharp, useful, and mobile-friendly. Short plans, clear next actions."
    )


def run_novae_job(
    prompt: str,
    *,
    cwd: str = "",
    job: Optional[Dict[str, Any]] = None,
    kind: str = "grok",
) -> tuple:
    """Execute as Novae hands — routes to Grok or Codex engines with preamble."""
    job = job or {}
    kind = (kind or "grok").lower()
    if kind not in ("grok", "codex"):
        kind = "grok"
    nid = "GROK_NOVAE" if kind == "grok" else "CODEX_NOVAE"
    edition = (job.get("edition") or ("founder" if job.get("host_power") else "market")).lower()
    host_power = bool(job.get("host_power")) and edition == "founder"
    ws = _ws_root(nid)
    work = cwd or str(ws / ("code" if kind == "codex" else "files"))
    Path(work).mkdir(parents=True, exist_ok=True)

    with _lock:
        st = _load(nid)
        st["active"] = True
        st["runs"] = int(st.get("runs") or 0) + 1
        st["last_at"] = time.time()
        st["last_goal"] = (prompt or "")[:400]
        _save(st)

    pre = system_preamble(kind, host_power=host_power, edition=edition)
    full = f"{pre}\n\n---\nUSER TASK:\n{(prompt or '').strip()}"

    # note in workspace
    try:
        note = ws / "notes" / f"run-{int(time.time())}-{uuid.uuid4().hex[:6]}.md"
        note.write_text(
            f"# Novae run\n\nengine={kind}\nedition={edition}\nhost_power={host_power}\n\n{prompt}\n",
            encoding="utf-8",
        )
    except Exception:
        pass

    try:
        from pocket.mesh_disk import leave_artifact

        leave_artifact(nid, "run", {"prompt": (prompt or "")[:300], "edition": edition})
    except Exception:
        pass

    if kind == "codex":
        from pocket.executor import _run_codex  # type: ignore

        # Prefer public runner if available
        try:
            from pocket.executor import run_job as _rj  # noqa: F401
        except Exception:
            pass
        try:
            return _run_codex(full, work, job_id=job.get("id") or "")
        except Exception:
            # fallback: create sub-job style via grok if codex missing
            from pocket.executor import _run_grok_agent  # type: ignore

            return _run_grok_agent(
                full + "\n\n[Novae note: Codex path unavailable — Grok coding assist.]",
                work,
                job_id=job.get("id") or "",
            )

    from pocket.executor import _run_grok_agent  # type: ignore

    return _run_grok_agent(full, work, job_id=job.get("id") or "")


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "schema": "pocket.novae.v1",
        "root": str(ROOT),
        "agents": list_novae(),
        "hint": "POST /v1/novae/activate {id:GROK_NOVAE|CODEX_NOVAE} then chat on returned session",
    }
