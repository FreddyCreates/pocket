"""MEDINA-SUBAGENT-MESH/1.0 — formal protocol for POCKET mesh subagents.

Doctrine: agents coordinate on a virtual mesh disk (prefer E:) with SHA
identities, HMAC envelopes, optional body cipher, and frequency channels.
They do **not** require a shared chat transcript (Antigravity-style).

This module is the single source of truth for protocol constants, validation,
and status. The always-on hook is `pocket.agent_hook`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

PROTOCOL_ID = "MEDINA-SUBAGENT-MESH/1.0"
PROTOCOL_NAME = "Subagent Mesh Protocol"
ARCHIVAL = "INL-2026-POCKET.MESH.v1"

# Frequency lanes (logical → channel file stem)
FREQ_LANES: Dict[str, Dict[str, Any]] = {
    "user": {"channel": "freq-0", "hz": 0, "purpose": "user @dispatch"},
    "heartbeat": {"channel": "freq-1", "hz": 1, "purpose": "headless heartbeats"},
    "design": {"channel": "freq-2", "hz": 2, "purpose": "design bus"},
    "security": {"channel": "freq-3", "hz": 3, "purpose": "sentinel / audit"},
    "ship": {"channel": "freq-4", "hz": 4, "purpose": "release / beta"},
    "intel": {"channel": "freq-5", "hz": 5, "purpose": "research + BLE intel stubs"},
}

# Always-use agent packs
LATIN_CORE: List[str] = [
    "ARCHON",
    "HYDRA",
    "SCRUTATOR",
    "SCRIPTOR",
    "PORTARIUS",
    "OCULUS",
    "SPECULUM",
    "REPOSITOR",
    "CONSILIARIUS",
    "TABELLARIUS",
    "NAVIGATOR",
    "GUPPY",
]
DESIGN_PACK: List[str] = ["DESIGN", "AESTHETE", "LAYOUT", "MOTION"]
HEADLESS_PACK: List[str] = [
    "FORGE_HEADLESS",
    "SENTINEL_HEADLESS",
    "RESEARCH_HEADLESS",
    "SHIP_HEADLESS",
]

ENCRYPTION = {
    "identity": "SHA-256(salt || agent_id)",
    "envelope": "HMAC-SHA256 over sorted JSON core",
    "body": "hmac-sha256-xor-v1 (optional ciphertext field body_cipher)",
    "storage": "virtual mesh disk prefer E:/POCKET_MESH",
}

RELATED_PROTOCOLS = [
    "MEDINA-LOOM/0.1",
    "MEDINA-MCP-COLONY-DEPLOY/1.0",
    "MEDINA-COLONY-BRIDGE/1.0",
    "microsoft_protocol",
    "bluetooth_hz",
]

API_SURFACE = [
    "GET /v1/subagents",
    "GET /v1/subagents/running",
    "POST /v1/subagents/dispatch",
    "GET /v1/mesh",
    "GET /v1/mesh/inbox/{agent}",
    "GET /v1/mesh/channel",
    "POST /v1/mesh/send",
    "POST /v1/mesh/bootstrap",
    "POST /v1/headless/start",
    "POST /v1/headless/stop",
    "GET /v1/protocols/mesh",
    "POST /v1/hooks/mesh",
]

# Doctrine flags — host must honor these when ALWAYS_USE_MESH is on
DOCTRINE = {
    "always_use_mesh": True,
    "always_bootstrap_on_serve": True,
    "always_start_headless": True,
    "dispatch_on_at_mentions": True,
    "artifacts_without_shared_chat": True,
    "prefer_virtual_disk_e": True,
    "design_first_class": True,  # DESIGN is not SCRIPTOR
    "encrypt_bodies_default": True,
}


def manifest() -> Dict[str, Any]:
    return {
        "ok": True,
        "protocol_id": PROTOCOL_ID,
        "name": PROTOCOL_NAME,
        "archival": ARCHIVAL,
        "version": "1.0",
        "doctrine": dict(DOCTRINE),
        "encryption": dict(ENCRYPTION),
        "freq_lanes": dict(FREQ_LANES),
        "packs": {
            "latin": list(LATIN_CORE),
            "design": list(DESIGN_PACK),
            "headless": list(HEADLESS_PACK),
            "min_agents": len(LATIN_CORE) + len(DESIGN_PACK) + len(HEADLESS_PACK),
        },
        "related_protocols": list(RELATED_PROTOCOLS),
        "api": list(API_SURFACE),
        "modules": {
            "mesh": "pocket.mesh_disk",
            "dispatch": "pocket.subagent_dispatch",
            "design": "pocket.design_agents",
            "hook": "pocket.agent_hook",
            "hz": "pocket.hz_mesh",
            "microsoft": "pocket.protocols.microsoft_protocol",
            "bluetooth": "pocket.protocols.bluetooth_hz",
            "this": "pocket.protocols.subagent_mesh_protocol",
        },
        "research": "docs/research/POCKET_SUBAGENT_MESH_CLOUDCOLONY_PROTOCOL.md",
        "cloudcolony": "E:/repos/cloudcolony-sovereign (framework wrap, not product build)",
    }


def resolve_lane(lane_or_freq: str) -> str:
    key = (lane_or_freq or "user").lower().strip()
    if key in FREQ_LANES:
        return FREQ_LANES[key]["channel"]
    if key.startswith("freq-"):
        return key
    if key.isdigit():
        return f"freq-{key}"
    return "freq-0"


def validate_agent_name(name: str) -> Dict[str, Any]:
    n = (name or "").upper().strip()
    all_known = set(LATIN_CORE) | set(DESIGN_PACK) | set(HEADLESS_PACK) | {"USER", "ARCHON"}
    pack = None
    if n in DESIGN_PACK:
        pack = "design"
    elif n in HEADLESS_PACK or n.endswith("_HEADLESS"):
        pack = "headless"
    elif n in LATIN_CORE:
        pack = "latin"
    return {
        "ok": bool(n),
        "id": n,
        "known": n in all_known or bool(n),
        "pack": pack or "mesh",
        "protocol": PROTOCOL_ID,
    }


def status() -> Dict[str, Any]:
    """Live protocol status + mesh disk health."""
    out = manifest()
    try:
        from pocket.mesh_disk import status as mesh_status

        out["mesh"] = mesh_status()
        out["mesh_ok"] = bool(mesh_status().get("ok"))
    except Exception as e:
        out["mesh"] = {"ok": False, "error": str(e)}
        out["mesh_ok"] = False
    try:
        from pocket.agent_hook import hook_status

        out["hook"] = hook_status()
    except Exception as e:
        out["hook"] = {"ok": False, "error": str(e)}
    return out
