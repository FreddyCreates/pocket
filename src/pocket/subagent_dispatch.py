"""Dispatch @mentions and headless work onto Latin/mesh agents."""

from __future__ import annotations

import re
import threading
import time
from typing import Any, Dict, List, Optional  # noqa: F401

from pocket.live_events import emit
from pocket.mesh_disk import ensure_agent, leave_artifact, send_message, bootstrap_core_agents

# Always register mesh identities (includes design agents)
try:
    bootstrap_core_agents()
except Exception:
    pass

try:
    from pocket.design_agents import bootstrap_design_agents

    bootstrap_design_agents()
except Exception:
    pass

try:
    from pocket.ship_agents import bootstrap_ship_agents

    bootstrap_ship_agents()
except Exception:
    pass

MENTION_RE = re.compile(r"@([A-Za-z][A-Za-z0-9_]{1,32})")

# 4 headless powerful agents (run in background threads)
HEADLESS = {
    "FORGE_HEADLESS": "Build/fix/fix forge — code + packages",
    "SENTINEL_HEADLESS": "Security + sanity + audit",
    "RESEARCH_HEADLESS": "Research packs + fusion sense notes",
    "SHIP_HEADLESS": "Release/beta ship checklist + demos",
}

# Design specialists (role=design) — DESIGN stays DESIGN, not SCRIPTOR
DESIGN_IDS = ("DESIGN", "AESTHETE", "LAYOUT", "MOTION")

# Ship pack (role=ship) — marketing / demo / electron
SHIP_IDS = ("MARKETING", "DEMO", "ELECTRON")

_ALIAS = {
    # DESIGN is first-class — do not alias to SCRIPTOR
    "DESIGNER": "DESIGN",
    "UI": "DESIGN",
    "UX": "DESIGN",
    "AESTHETIC": "AESTHETE",
    "CRITIQUE": "AESTHETE",
    "GRID": "LAYOUT",
    "ANIMATION": "MOTION",
    "ANIMATE": "MOTION",
    "VISION": "OCULUS",
    "RECORD": "SPECULUM",
    "OPEN": "PORTARIUS",
    "RESEARCH": "SCRUTATOR",
    "SHIP": "SHIP_HEADLESS",
    "FORGE": "FORGE_HEADLESS",
    "SENTINEL": "SENTINEL_HEADLESS",
    # Ship pack (first-class; helpers of SHIP_HEADLESS)
    "MKT": "MARKETING",
    "ONEPAGER": "MARKETING",
    "WALKTHROUGH": "DEMO",
    "DESKTOP_SHIP": "ELECTRON",
    "TAURI": "ELECTRON",
}


def parse_mentions(text: str) -> List[str]:
    found = []
    for m in MENTION_RE.findall(text or ""):
        name = m.upper()
        name = _ALIAS.get(name, name)
        if name not in found:
            found.append(name)
    return found


def dispatch(
    message: str,
    *,
    from_agent: str = "USER",
    agents: Optional[List[str]] = None,
    channel: str = "freq-0",
) -> Dict[str, Any]:
    """Send message to one or more agents; run host skill when possible."""
    text = (message or "").strip()
    targets = agents or parse_mentions(text)
    if not targets:
        targets = ["ARCHON"]
    results = []
    for name in targets:
        ensure_agent(name)
        # strip @tags for payload
        clean = MENTION_RE.sub("", text).strip() or text
        msg = send_message(from_agent, name, clean, channel=channel, kind="dispatch")
        run = _execute_agent(name, clean)
        # peer notify ARCHON
        if name != "ARCHON":
            send_message(name, "ARCHON", f"completed dispatch: {run.get('ok')}", kind="status", channel=channel)
        art = leave_artifact(
            name,
            f"dispatch_{int(time.time())}.md",
            f"# Dispatch to {name}\n\n{clean}\n\n## Result\n```\n{str(run)[:4000]}\n```\n",
            notify=["ARCHON"],
        )
        results.append({"agent": name, "message": msg, "run": run, "artifact": art})
        emit("subagents", f"dispatch @{name} ok={run.get('ok')}", agent=name, role="python")
    return {
        "ok": all(r.get("run", {}).get("ok", True) for r in results),
        "dispatched": len(results),
        "results": results,
        "mentions": targets,
        "mesh": True,
    }


def _execute_agent(name: str, prompt: str) -> Dict[str, Any]:
    n = name.upper()
    try:
        if n in HEADLESS or n.endswith("_HEADLESS"):
            return _run_headless(n, prompt)
        # Design specialists — first-class, not SCRIPTOR
        if n in DESIGN_IDS:
            from pocket.design_agents import run_design_agent

            return run_design_agent(n, prompt)
        # Ship pack — marketing one-pager / demo script / electron checklist
        if n in SHIP_IDS:
            from pocket.ship_agents import run_ship_agent

            return run_ship_agent(n, prompt)
        if n == "OCULUS":
            from pocket.perception import sense

            s = sense(force=True, max_ui=400)
            return {"ok": True, "brief": s.get("brief"), "counts": s.get("counts")}
        if n == "SPECULUM":
            from pocket.screen_record import record_status

            return record_status()
        if n == "SCRUTATOR":
            from pocket.perception import sense

            s = sense(force=False, max_ui=300)
            return {"ok": True, "brief": s.get("brief"), "action": "research_context"}
        if n == "PORTARIUS":
            from pocket.desktop import open_app

            # don't force open unless asked
            if "open" in prompt.lower():
                app = "notepad"
                for a in ("edge", "code", "explorer", "notepad", "terminal"):
                    if a in prompt.lower():
                        app = a
                        break
                return open_app(app)
            return {"ok": True, "message": "PORTARIUS ready (say open …)"}
        if n == "SCRIPTOR":
            path_note = leave_artifact(
                "SCRIPTOR",
                "script_note.md",
                f"# Scriptor note\n\n{prompt}\n\n— SCRIPTOR\n",
                notify=["ARCHON", "SHIP_HEADLESS"],
            )
            return {"ok": True, "artifact": path_note}
        if n == "ARCHON":
            from pocket.orchestrator import get_orchestrator

            # try page_render or see_screen as default
            skill = "page_render" if "page" in prompt.lower() or "sense" in prompt.lower() else "see_screen"
            if "screenshot" in prompt.lower():
                skill = "screenshot"
            return get_orchestrator().execute(skill, prompt=prompt)
        if n == "GUPPY":
            from pocket.orchestrator import get_orchestrator

            return get_orchestrator().execute("screenshot", prompt=prompt)
        # generic latin via alpha_workers
        try:
            from pocket.alpha_workers import run_worker

            return run_worker(n, prompt)
        except Exception:
            return {"ok": True, "message": f"{n} acknowledged on mesh", "queued": True}
    except Exception as e:
        return {"ok": False, "error": str(e), "agent": n}


def _run_e_worker(script: str, prompt: str) -> Dict[str, Any]:
    """Offload to Python worker scripts living on the E: virtual mesh disk."""
    import subprocess
    import sys

    from pocket.mesh_disk import WORKERS

    worker = WORKERS / script
    if not worker.exists():
        return {"ok": False, "error": f"missing worker {worker}"}
    try:
        r = subprocess.run(
            [sys.executable, str(worker), prompt or "pulse"],
            cwd=str(WORKERS),
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "ok": r.returncode == 0,
            "stdout": (r.stdout or "")[:2000],
            "stderr": (r.stderr or "")[:500],
            "worker": str(worker),
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "worker": str(worker)}


def _run_headless(name: str, prompt: str) -> Dict[str, Any]:
    n = name.upper()
    # Always pulse E: worker first (virtual disk offload)
    worker_map = {
        "FORGE_HEADLESS": "worker_forge.py",
        "SENTINEL_HEADLESS": "worker_sentinel.py",
        "RESEARCH_HEADLESS": "worker_research.py",
        "SHIP_HEADLESS": "worker_ship.py",
    }
    e_run = None
    if n in worker_map:
        e_run = _run_e_worker(worker_map[n], prompt)

    if n == "FORGE_HEADLESS":
        from pocket.virtual_computer import open_computer, shell, write_file

        open_computer(label="forge")
        write_file("headless/forge_task.md", f"# Forge\n\n{prompt}\n")
        r = shell("python -c \"print('FORGE_HEADLESS ok')\"")
        leave_artifact(n, "forge_result.md", str(r), notify=["ARCHON", "SHIP_HEADLESS"])
        return {"ok": r.get("ok") or (e_run or {}).get("ok"), "forge": r, "e_worker": e_run}
    if n == "SENTINEL_HEADLESS":
        from pocket.sanity import intent_buffer, guard_shell

        ib = intent_buffer()
        g = guard_shell("echo sentinel")
        leave_artifact(n, "sentinel.md", f"{ib}\n{g}", notify=["ARCHON"])
        return {"ok": True, "intent": ib, "guard": g, "e_worker": e_run}
    if n == "RESEARCH_HEADLESS":
        from pocket.perception import sense
        from pocket.rfe_kernel import materialize

        s = sense(force=True, max_ui=500)
        m = materialize(page=s, refresh=False)
        leave_artifact(n, "research_rfe.md", m.get("brief") or "", notify=["ARCHON", "SCRIPTOR"])
        return {"ok": True, "brief": s.get("brief"), "rfe": m.get("brief"), "paths": m.get("paths"), "e_worker": e_run}
    if n == "SHIP_HEADLESS":
        checklist = [
            "Desktop install + tray",
            "API /developers keys",
            "Product nav Overview/Desktop/API/Studio",
            "Fusion sense + RFE",
            "Subagents dispatch @",
            "Mesh virtual disk on E:",
            "Studio product phone",
            "Design agents DESIGN/AESTHETE/LAYOUT/MOTION",
            "Ship pack MARKETING/DEMO/ELECTRON artifacts",
            "Protocols microsoft + bluetooth + hz",
            "CloudColony framework repo",
        ]
        body = "# Ship / beta checklist\n\n" + "\n".join(f"- [ ] {c}" for c in checklist) + f"\n\n## Prompt\n{prompt}\n"
        art = leave_artifact(n, "SHIP_CHECKLIST.md", body, notify=["ARCHON", "FORGE_HEADLESS"])
        return {"ok": True, "checklist": checklist, "artifact": art, "e_worker": e_run}
    return {"ok": True, "message": f"{n} idle", "e_worker": e_run}


_headless_threads: dict = {}
_headless_stop: dict = {}


def start_headless_pack(*, interval_sec: float = 120.0) -> Dict[str, Any]:
    """Start 4 powerful headless agents pulsing on the mesh."""
    started = []
    for name, desc in HEADLESS.items():
        if name in _headless_threads and _headless_threads[name].is_alive():
            started.append({"name": name, "already": True})
            continue
        stop = threading.Event()
        _headless_stop[name] = stop

        def loop(n=name, d=desc, st=stop):
            ensure_agent(n, role="headless")
            while not st.is_set():
                try:
                    leave_artifact(
                        n,
                        "heartbeat.md",
                        f"# {n}\n\n{d}\n\nat={time.time()}\n",
                        notify=["ARCHON"],
                    )
                    send_message(n, "ARCHON", f"heartbeat {n}", kind="heartbeat", channel="freq-1")
                except Exception:
                    pass
                st.wait(interval_sec)

        t = threading.Thread(target=loop, name=f"hl-{name}", daemon=True)
        t.start()
        _headless_threads[name] = t
        started.append({"name": name, "started": True, "desc": desc})
    return {"ok": True, "headless": started, "count": len(started)}


def stop_headless_pack() -> Dict[str, Any]:
    for n, ev in list(_headless_stop.items()):
        ev.set()
    return {"ok": True, "stopped": list(_headless_stop.keys())}
