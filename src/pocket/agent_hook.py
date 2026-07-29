"""Always-use Subagent Mesh hook — MEDINA-SUBAGENT-MESH/1.0

When the host starts (or any code path calls `ensure_mesh_hook`), POCKET:

1. Bootstraps Latin + design + headless identities on E: virtual mesh disk
2. Starts the 4 powerful headless workers (daemon threads)
3. Registers design agents
4. Publishes a protocol heartbeat on freq-1

Optional: route user text through @dispatch when mentions present
(`route_message`). Set env POCKET_ALWAYS_MESH=0 to disable auto-start of
headless only; bootstrap still runs unless POCKET_MESH_HOOK=0.
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Dict, List, Optional

_lock = threading.Lock()
_state: Dict[str, Any] = {
    "armed": False,
    "armed_at": None,
    "bootstrap": None,
    "headless": None,
    "design": None,
    "ship": None,
    "protocol": "MEDINA-SUBAGENT-MESH/1.0",
    "errors": [],
}


def _env_truthy(name: str, default: bool = True) -> bool:
    v = os.environ.get(name)
    if v is None:
        return default
    return str(v).strip().lower() not in ("0", "false", "no", "off")


def always_use_enabled() -> bool:
    """Master switch — default ON for beta doctrine."""
    return _env_truthy("POCKET_MESH_HOOK", True) and _env_truthy("POCKET_ALWAYS_MESH", True)


def headless_auto_enabled() -> bool:
    return always_use_enabled() and _env_truthy("POCKET_HEADLESS_AUTO", True)


def hook_status() -> Dict[str, Any]:
    with _lock:
        st = dict(_state)
    st["always_use"] = always_use_enabled()
    st["headless_auto"] = headless_auto_enabled()
    st["env"] = {
        "POCKET_MESH_HOOK": os.environ.get("POCKET_MESH_HOOK", "1"),
        "POCKET_ALWAYS_MESH": os.environ.get("POCKET_ALWAYS_MESH", "1"),
        "POCKET_HEADLESS_AUTO": os.environ.get("POCKET_HEADLESS_AUTO", "1"),
        "POCKET_MESH_ROOT": os.environ.get("POCKET_MESH_ROOT", ""),
    }
    try:
        from pocket.protocols.subagent_mesh_protocol import PROTOCOL_ID, DOCTRINE

        st["protocol_id"] = PROTOCOL_ID
        st["doctrine"] = DOCTRINE
    except Exception:
        pass
    return st


def ensure_mesh_hook(*, force: bool = False, interval_sec: float = 120.0) -> Dict[str, Any]:
    """Idempotent arm: bootstrap mesh + design + headless. Call on serve()."""
    if not always_use_enabled() and not force:
        return {"ok": True, "skipped": True, "reason": "POCKET_MESH_HOOK/ALWAYS_MESH disabled", **hook_status()}

    with _lock:
        if _state.get("armed") and not force:
            return {"ok": True, "already": True, **hook_status()}

    errors: List[str] = []
    bootstrap = design = headless = None

    try:
        from pocket.mesh_disk import bootstrap_core_agents

        bootstrap = bootstrap_core_agents()
    except Exception as e:
        errors.append(f"bootstrap: {e}")

    try:
        from pocket.design_agents import bootstrap_design_agents

        design = bootstrap_design_agents()
    except Exception as e:
        errors.append(f"design: {e}")

    ship = None
    try:
        from pocket.ship_agents import bootstrap_ship_agents

        ship = bootstrap_ship_agents()
    except Exception as e:
        errors.append(f"ship: {e}")

    if headless_auto_enabled() or force:
        try:
            from pocket.subagent_dispatch import start_headless_pack

            headless = start_headless_pack(interval_sec=interval_sec)
        except Exception as e:
            errors.append(f"headless: {e}")

    # Protocol heartbeat artifact + channel
    try:
        from pocket.mesh_disk import leave_artifact, send_message
        from pocket.protocols.subagent_mesh_protocol import PROTOCOL_ID, manifest

        body = (
            f"# {PROTOCOL_ID} armed\n\n"
            f"at={time.time()}\n"
            f"bootstrap={bool(bootstrap and bootstrap.get('ok'))}\n"
            f"headless={bool(headless and headless.get('ok'))}\n"
        )
        leave_artifact("ARCHON", "mesh_hook_armed.md", body, notify=["SHIP_HEADLESS"])
        send_message(
            "ARCHON",
            "SHIP_HEADLESS",
            f"hook armed {PROTOCOL_ID}",
            channel="freq-1",
            kind="hook",
        )
        _ = manifest()
    except Exception as e:
        errors.append(f"heartbeat: {e}")

    with _lock:
        _state["armed"] = True
        _state["armed_at"] = time.time()
        _state["bootstrap"] = bootstrap
        _state["design"] = design
        _state["ship"] = ship
        _state["headless"] = headless
        _state["errors"] = errors

    return {
        "ok": len(errors) == 0,
        "armed": True,
        "bootstrap": bootstrap,
        "design": design,
        "ship": ship,
        "headless": headless,
        "errors": errors,
        "protocol": "MEDINA-SUBAGENT-MESH/1.0",
    }


def route_message(
    text: str,
    *,
    from_agent: str = "USER",
    force_dispatch: bool = False,
) -> Dict[str, Any]:
    """If text has @mentions (or force), dispatch via mesh protocol.

    Call this from chat/session paths so agents always use the mesh bus.
    """
    ensure_mesh_hook()
    from pocket.subagent_dispatch import dispatch, parse_mentions

    mentions = parse_mentions(text or "")
    if not mentions and not force_dispatch:
        return {
            "ok": True,
            "dispatched": 0,
            "mentions": [],
            "skipped": True,
            "reason": "no @mentions",
            "protocol": "MEDINA-SUBAGENT-MESH/1.0",
        }
    return dispatch(text or "", from_agent=from_agent)


def dispatch_named(agent: str, message: str, *, from_agent: str = "USER") -> Dict[str, Any]:
    """Always-use path for explicit agent targets (no chat required)."""
    ensure_mesh_hook()
    from pocket.subagent_dispatch import dispatch

    return dispatch(message, from_agent=from_agent, agents=[(agent or "ARCHON").upper()])


def protocol_report() -> Dict[str, Any]:
    """Research/ops snapshot for /v1/protocols/mesh and doctor."""
    from pocket.protocols.subagent_mesh_protocol import status as proto_status

    ensure_mesh_hook()
    return {
        "ok": True,
        "hook": hook_status(),
        "protocol": proto_status(),
        "research": "docs/research/POCKET_SUBAGENT_MESH_CLOUDCOLONY_PROTOCOL.md",
        "archival": "INL-2026-POCKET.MESH.v1",
    }
