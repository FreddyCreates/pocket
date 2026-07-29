"""POCKET Virtual Mesh Disk — agent workspace on high-capacity volume (E:).

Antigravity-style: subagents leave signed + encrypted artifacts/messages for
each other without sharing a chat transcript.

- Identity = SHA-256(salt || agent_id)
- Envelopes = HMAC-SHA256 signed; body optionally Fernet-style XOR stream (stdlib)
- Channels = frequency lanes (freq-N.jsonl) for real-time coordination
- Virtual disk = logical workspace tree under E:/POCKET_MESH/vdisk (not a OS VHD)
  so workers offload files onto the multi-TB volume without polluting C:.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

# Prefer E: (5TB class). Fallback D: then ~/.pocket/mesh
def _pick_root() -> Path:
    env = os.environ.get("POCKET_MESH_ROOT")
    if env:
        return Path(env)
    for letter in ("E", "D"):
        root = Path(f"{letter}:/POCKET_MESH")
        try:
            root.mkdir(parents=True, exist_ok=True)
            probe = root / ".write_probe"
            probe.write_text("ok", encoding="utf-8")
            probe.unlink(missing_ok=True)
            return root
        except Exception:
            continue
    root = Path.home() / ".pocket" / "mesh"
    root.mkdir(parents=True, exist_ok=True)
    return root


MESH = _pick_root()
AGENTS = MESH / "agents"
CHANNELS = MESH / "channels"
PROTOCOLS = MESH / "protocols"
HEADLESS = MESH / "headless"
ARTIFACTS = MESH / "artifacts"
WORKERS = MESH / "workers"
VDISK = MESH / "vdisk"
for d in (
    AGENTS,
    CHANNELS,
    PROTOCOLS,
    HEADLESS,
    ARTIFACTS,
    WORKERS,
    VDISK,
    VDISK / "workspaces",
    VDISK / "shared",
    PROTOCOLS / "microsoft",
    PROTOCOLS / "bluetooth",
    PROTOCOLS / "hz",
):
    d.mkdir(parents=True, exist_ok=True)

SALT_PATH = MESH / ".mesh_salt"
if not SALT_PATH.exists():
    SALT_PATH.write_bytes(secrets.token_bytes(32))

# Virtual disk meta (logical — prefer E: over carving a .vhd for agent mail)
_vmeta = VDISK / "VIRTUAL_DISK.md"
if not _vmeta.exists():
    _vmeta.write_text(
        f"# POCKET Virtual Mesh Disk\n\n"
        f"root={MESH}\n"
        f"kind=virtual_workspace\n"
        f"prefer=E: high-capacity volume\n"
        f"identity=SHA-256(salt||agent_id)\n"
        f"envelopes=HMAC-SHA256 + body_cipher\n"
        f"channels=freq-N jsonl\n"
        f"workers={WORKERS}\n",
        encoding="utf-8",
    )


def mesh_root() -> Path:
    return MESH


def agent_sha(agent_id: str) -> str:
    salt = SALT_PATH.read_bytes()
    return hashlib.sha256(salt + (agent_id or "").encode("utf-8")).hexdigest()


def _hmac_key() -> bytes:
    return SALT_PATH.read_bytes()


def ensure_agent(agent_id: str, *, role: str = "worker") -> Dict[str, Any]:
    aid = (agent_id or "ANON").upper().strip()
    home = AGENTS / aid
    for sub in ("inbox", "outbox", "artifacts", "keys"):
        (home / sub).mkdir(parents=True, exist_ok=True)
    sha = agent_sha(aid)
    ident = {
        "id": aid,
        "sha256": sha,
        "role": role,
        "created_at": time.time(),
        "home": str(home),
        "mesh": str(MESH),
    }
    (home / "id.json").write_text(json.dumps(ident, indent=2), encoding="utf-8")
    return ident


def sign_payload(payload: Dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hmac.new(_hmac_key(), body, hashlib.sha256).hexdigest()


def verify_payload(payload: Dict[str, Any], sig: str) -> bool:
    try:
        return hmac.compare_digest(sign_payload(payload), sig or "")
    except Exception:
        return False


def _cipher_keystream(n: int, *, nonce: bytes) -> bytes:
    """HMAC-SHA256 keystream (stdlib-only body cipher for mesh privacy)."""
    out = bytearray()
    i = 0
    key = _hmac_key()
    while len(out) < n:
        block = hmac.new(key, nonce + i.to_bytes(4, "big"), hashlib.sha256).digest()
        out.extend(block)
        i += 1
    return bytes(out[:n])


def encrypt_body(plaintext: str) -> Dict[str, str]:
    raw = (plaintext or "").encode("utf-8")
    nonce = secrets.token_bytes(16)
    ks = _cipher_keystream(len(raw), nonce=nonce)
    ct = bytes(a ^ b for a, b in zip(raw, ks))
    return {
        "alg": "hmac-sha256-xor-v1",
        "nonce_b64": base64.b64encode(nonce).decode("ascii"),
        "ct_b64": base64.b64encode(ct).decode("ascii"),
    }


def decrypt_body(blob: Dict[str, Any]) -> str:
    try:
        nonce = base64.b64decode(blob.get("nonce_b64") or "")
        ct = base64.b64decode(blob.get("ct_b64") or "")
        ks = _cipher_keystream(len(ct), nonce=nonce)
        return bytes(a ^ b for a, b in zip(ct, ks)).decode("utf-8", errors="replace")
    except Exception:
        return ""


def send_message(
    from_agent: str,
    to_agent: str,
    body: str,
    *,
    channel: str = "freq-0",
    kind: str = "note",
    artifact: Optional[str] = None,
    encrypt: bool = True,
) -> Dict[str, Any]:
    """Encrypted-channel message: signed envelope in recipient inbox + channel log."""
    fr = ensure_agent(from_agent)
    to = ensure_agent(to_agent)
    msg_id = uuid.uuid4().hex
    plain = (body or "")[:20000]
    body_field: Any = plain
    body_cipher: Optional[Dict[str, str]] = None
    if encrypt:
        body_cipher = encrypt_body(plain)
        body_field = "[encrypted]"
    envelope_core = {
        "id": msg_id,
        "from": fr["id"],
        "from_sha": fr["sha256"],
        "to": to["id"],
        "to_sha": to["sha256"],
        "kind": kind,
        "body": body_field,
        "body_cipher": body_cipher,
        "artifact": artifact,
        "channel": channel,
        "at": time.time(),
    }
    sig = sign_payload(envelope_core)
    envelope = {**envelope_core, "hmac_sha256": sig}
    # recipient inbox
    dest = AGENTS / to["id"] / "inbox" / f"{int(time.time())}_{msg_id}.json"
    dest.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    # sender outbox
    out = AGENTS / fr["id"] / "outbox" / f"{int(time.time())}_{msg_id}.json"
    out.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
    # frequency channel (shared bus) — ciphertext only when encrypt
    ch = CHANNELS / f"{channel}.jsonl"
    with ch.open("a", encoding="utf-8") as f:
        f.write(json.dumps(envelope, default=str) + "\n")
    return {
        "ok": True,
        "message_id": msg_id,
        "path": str(dest),
        "channel": channel,
        "hmac_sha256": sig,
        "encrypted": bool(encrypt),
        "from_sha": fr["sha256"][:16],
        "to_sha": to["sha256"][:16],
    }


def read_inbox(agent_id: str, *, limit: int = 50) -> Dict[str, Any]:
    aid = (agent_id or "").upper()
    ensure_agent(aid)
    inbox = AGENTS / aid / "inbox"
    files = sorted(inbox.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    msgs = []
    for p in files:
        try:
            m = json.loads(p.read_text(encoding="utf-8"))
            m["valid_hmac"] = verify_payload(
                {k: v for k, v in m.items() if k != "hmac_sha256"},
                m.get("hmac_sha256") or "",
            )
            if m.get("body_cipher"):
                m["body_plain"] = decrypt_body(m["body_cipher"])
            m["_path"] = str(p)
            msgs.append(m)
        except Exception:
            continue
    return {"ok": True, "agent": aid, "messages": msgs, "count": len(msgs)}


def vdisk_path(*parts: str) -> Path:
    """Path under the virtual mesh disk (prefer E: workspaces)."""
    p = VDISK.joinpath(*[str(x).lstrip("/\\") for x in parts if x is not None])
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def write_vdisk(rel: str, content: str, *, agent_id: str = "USER") -> Dict[str, Any]:
    path = vdisk_path("workspaces", (agent_id or "USER").upper(), rel)
    path.write_text(content or "", encoding="utf-8")
    return {
        "ok": True,
        "path": str(path),
        "sha256": hashlib.sha256((content or "").encode("utf-8")).hexdigest(),
        "mesh_root": str(MESH),
    }


def leave_artifact(agent_id: str, name: str, content: str, *, notify: Optional[List[str]] = None) -> Dict[str, Any]:
    aid = ensure_agent(agent_id)["id"]
    safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in (name or "artifact"))[:80]
    path = AGENTS / aid / "artifacts" / f"{int(time.time())}_{safe}"
    path.write_text(content or "", encoding="utf-8")
    # global index
    idx = ARTIFACTS / f"{aid}_{path.name}"
    try:
        if not idx.exists():
            idx.write_text(content or "", encoding="utf-8")
    except Exception:
        pass
    for peer in notify or []:
        send_message(aid, peer, f"artifact:{path.name}", kind="artifact", artifact=str(path))
    return {"ok": True, "path": str(path), "agent": aid, "sha256": hashlib.sha256((content or "").encode()).hexdigest()}


def channel_tail(channel: str = "freq-0", *, limit: int = 40) -> Dict[str, Any]:
    ch = CHANNELS / f"{channel}.jsonl"
    if not ch.exists():
        return {"ok": True, "channel": channel, "messages": []}
    lines = ch.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
    msgs = []
    for ln in lines:
        try:
            msgs.append(json.loads(ln))
        except Exception:
            continue
    return {"ok": True, "channel": channel, "messages": msgs}


def status() -> Dict[str, Any]:
    agents = [p.name for p in AGENTS.iterdir() if p.is_dir()] if AGENTS.exists() else []
    headless = [a for a in agents if "HEADLESS" in a]
    return {
        "ok": True,
        "mesh_root": str(MESH),
        "drive": str(MESH)[:2],
        "virtual_disk": str(VDISK),
        "workers_dir": str(WORKERS),
        "agents": agents,
        "agent_count": len(agents),
        "headless": headless,
        "headless_count": len(headless),
        "channels": [p.stem for p in CHANNELS.glob("*.jsonl")],
        "protocols": ["microsoft", "bluetooth", "hz"],
        "encryption": "hmac-sha256 + body_cipher xor-v1",
        "note": "Virtual mesh disk for subagent messaging + artifacts (prefer E:)",
    }


# Design specialists + Latin core + 4 powerful headless
CORE_AGENTS = [
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
    "DESIGN",
    "AESTHETE",
    "LAYOUT",
    "MOTION",
    "MARKETING",
    "DEMO",
    "ELECTRON",
    "FORGE_HEADLESS",
    "SENTINEL_HEADLESS",
    "RESEARCH_HEADLESS",
    "SHIP_HEADLESS",
]

HEADLESS_AGENTS = [
    "FORGE_HEADLESS",
    "SENTINEL_HEADLESS",
    "RESEARCH_HEADLESS",
    "SHIP_HEADLESS",
]


def bootstrap_core_agents() -> Dict[str, Any]:
    """Register platform Latin + design + headless agents on the mesh."""
    ids = []
    for a in CORE_AGENTS:
        if a in HEADLESS_AGENTS:
            role = "headless"
        elif a in ("DESIGN", "AESTHETE", "LAYOUT", "MOTION"):
            role = "design"
        elif a in ("MARKETING", "DEMO", "ELECTRON"):
            role = "ship"
        elif a in ("ARCHON", "HYDRA", "GUPPY"):
            role = "alpha"
        else:
            role = "core"
        ids.append(ensure_agent(a, role=role))
    # protocol docs (impl lives under pocket.protocols)
    (PROTOCOLS / "microsoft" / "README.md").write_text(
        "# Microsoft system protocol hooks\n\n"
        "Thin safe hooks: UIA click, Win32 maximize, allow-listed apps, page render.\n"
        "Used by PORTARIUS / OCULUS / SPECULUM / design agents on host.\n"
        "Python: `pocket.protocols.microsoft_protocol`\n",
        encoding="utf-8",
    )
    (PROTOCOLS / "bluetooth" / "README.md").write_text(
        "# Bluetooth / Hz mesh protocol\n\n"
        "BLE-style MHz → mesh `channels/freq-*.jsonl`.\n"
        "Physical BLE optional; file-bus via leave_artifact + send_message.\n"
        "Map: 2402→freq-0, 2426→freq-1, 2480→freq-2; others quantize to freq-N.\n"
        "Python: `pocket.protocols.bluetooth_hz`\n",
        encoding="utf-8",
    )
    (PROTOCOLS / "hz" / "README.md").write_text(
        "# Hz frequency mesh\n\n"
        "| Lane | Purpose |\n|------|----------|\n"
        "| freq-0 | user dispatches |\n"
        "| freq-1 | headless heartbeats |\n"
        "| freq-2 | design bus |\n"
        "| freq-3 | security/sentinel |\n"
        "| freq-4 | ship/release |\n",
        encoding="utf-8",
    )
    return {
        "ok": True,
        "mesh": str(MESH),
        "virtual_disk": str(VDISK),
        "registered": len(ids),
        "agents": [i["id"] for i in ids],
        "headless": HEADLESS_AGENTS,
        "design": ["DESIGN", "AESTHETE", "LAYOUT", "MOTION"],
        "ship": ["MARKETING", "DEMO", "ELECTRON"],
    }
