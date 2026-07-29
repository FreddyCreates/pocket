"""Hz mesh — frequency channels for subagent coordination.

Maps logical Hz lanes + BLE-style MHz to mesh disk channels (freq-N.jsonl).
Optional BLE later; file-bus is the default real-time transport.

Canonical BLE/Hz mapping also in `pocket.protocols.bluetooth_hz`.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pocket.mesh_disk import channel_tail, leave_artifact, send_message, CHANNELS, PROTOCOLS
from pocket.protocols import bluetooth_hz as _bt

# Logical frequency → channel file
HZ_LANES: Dict[str, Dict[str, Any]] = {
    "user": {"channel": "freq-0", "hz": 0, "purpose": "user @dispatch"},
    "heartbeat": {"channel": "freq-1", "hz": 1, "purpose": "headless heartbeats"},
    "design": {"channel": "freq-2", "hz": 2, "purpose": "design bus"},
    "security": {"channel": "freq-3", "hz": 3, "purpose": "sentinel / audit"},
    "ship": {"channel": "freq-4", "hz": 4, "purpose": "release / beta"},
    "intel": {"channel": "freq-5", "hz": 5, "purpose": "research + bluetooth intel stubs"},
}


def list_lanes() -> Dict[str, Any]:
    return {
        "ok": True,
        "lanes": HZ_LANES,
        "channels_dir": str(CHANNELS),
        "protocols": str(PROTOCOLS / "hz"),
        "transport": "file-bus",
        "ble": "optional-future",
        "ble_map": _bt.status().get("ble_map"),
        "channels": _bt.list_channels(),
    }


def resolve_channel(lane_or_freq: str) -> str:
    key = (lane_or_freq or "user").lower().strip()
    if key in HZ_LANES:
        return HZ_LANES[key]["channel"]
    if key.startswith("freq-"):
        return key
    if key.isdigit():
        return f"freq-{key}"
    # treat numeric MHz
    try:
        return _bt.channel_for_hz(float(key))
    except (TypeError, ValueError):
        return "freq-0"


def publish(
    from_agent: str,
    body: str,
    *,
    lane: str = "user",
    to_agent: str = "ARCHON",
    kind: str = "hz",
    hz: Optional[float] = None,
) -> Dict[str, Any]:
    if hz is not None:
        ch = _bt.channel_for_hz(hz)
    else:
        ch = resolve_channel(lane)
    return send_message(from_agent, to_agent, body, channel=ch, kind=kind, encrypt=True)


def listen(lane: str = "user", *, limit: int = 40) -> Dict[str, Any]:
    ch = resolve_channel(lane)
    return channel_tail(ch, limit=limit)


def bluetooth_stub_scan() -> Dict[str, Any]:
    """Placeholder for BLE device discovery — leaves mesh artifact for intel lane."""
    note = (
        "# Bluetooth / Hz scan stub\n\n"
        "Physical BLE not required for mesh messaging.\n"
        "Agents coordinate via encrypted file-bus frequencies.\n"
        "When BLE is enabled, map device IDs → agent SHA + lane.\n"
        f"BLE map: {_bt.status().get('ble_map')}\n"
    )
    art = leave_artifact("TABELLARIUS", "bt_scan_stub.md", note, notify=["ARCHON", "RESEARCH_HEADLESS"])
    publish("TABELLARIUS", "bt scan stub complete", lane="intel", kind="bluetooth")
    return {"ok": True, "artifact": art, "devices": [], "note": "file-bus only", "ble_map": _bt.status().get("ble_map")}


# Re-exports from protocols.bluetooth_hz
channel_for_hz = _bt.channel_for_hz
hz_for_channel = _bt.hz_for_channel
mesh_broadcast = _bt.mesh_broadcast
mesh_leave = _bt.mesh_leave
tune = _bt.tune
