"""Bluetooth / Hz frequency channel abstraction for POCKET mesh.

Maps BLE-style MHz frequencies onto mesh jsonl channels (`freq-0` … `freq-N`).
Physical BLE radio is optional; default transport is the mesh file-bus
(leave_artifact + send_message).
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

# BLE advertising band center-ish markers → mesh channel slots.
# Classic BLE 2.4 GHz advertising channels 37/38/39 ≈ 2402/2426/2480 MHz.
_BLE_HZ_MAP: Dict[int, str] = {
    2402: "freq-0",
    2426: "freq-1",
    2480: "freq-2",
}

# Extended mesh lanes (software-only, not real RF)
_DEFAULT_CHANNELS = ["freq-0", "freq-1", "freq-2", "freq-3", "freq-4", "freq-5"]
_MAX_SLOT = 15


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "protocol": "bluetooth_hz",
        "transport": "mesh_file_bus",
        "ble_map": dict(_BLE_HZ_MAP),
        "channels": list_channels(),
        "note": "Hz → freq-N; physical BLE optional",
    }


def list_channels() -> List[str]:
    """Known mesh frequency lanes (default set + any existing channel files)."""
    chans = list(_DEFAULT_CHANNELS)
    try:
        from pocket.mesh_disk import CHANNELS

        for p in sorted(CHANNELS.glob("freq-*.jsonl")):
            if p.stem not in chans:
                chans.append(p.stem)
    except Exception:
        pass
    return chans


def channel_for_hz(hz: float | int, *, band: str = "ble") -> str:
    """Map a frequency (MHz) to a mesh channel name.

    Exact BLE advertising markers hit freq-0/1/2. Other values quantize into
    slots freq-0..freq-N via (hz % span) bucketing.
    """
    try:
        h = int(round(float(hz)))
    except (TypeError, ValueError):
        return "freq-0"

    if band == "ble" and h in _BLE_HZ_MAP:
        return _BLE_HZ_MAP[h]

    # Quantize into N software slots (stable, deterministic)
    # Prefer 2.4 GHz neighborhood; fall back to modular slot.
    if 2400 <= h <= 2500:
        # 100 MHz band → up to 6 default lanes
        slot = min(5, max(0, (h - 2400) // 20))
        return f"freq-{slot}"

    slot = abs(h) % (_MAX_SLOT + 1)
    return f"freq-{slot}"


def hz_for_channel(channel: str) -> int:
    """Inverse: representative MHz for a mesh channel (for docs/artifacts)."""
    ch = (channel or "freq-0").strip().lower()
    if not ch.startswith("freq-"):
        ch = f"freq-{ch}" if ch.isdigit() else "freq-0"
    # Prefer reverse of BLE map
    for mhz, name in _BLE_HZ_MAP.items():
        if name == ch:
            return mhz
    try:
        slot = int(ch.split("-", 1)[1])
    except (IndexError, ValueError):
        slot = 0
    if 0 <= slot <= 5:
        return 2400 + slot * 20
    return 2400 + (slot % (_MAX_SLOT + 1)) * 5


def normalize_channel(channel: Optional[str] = None, *, hz: Optional[float] = None) -> str:
    if hz is not None:
        return channel_for_hz(hz)
    ch = (channel or "freq-0").strip().lower()
    if ch.startswith("freq-"):
        return ch
    if ch.isdigit():
        return f"freq-{int(ch)}"
    # treat as raw hz string
    try:
        return channel_for_hz(float(ch))
    except (TypeError, ValueError):
        return "freq-0"


def mesh_broadcast(
    from_agent: str,
    body: str,
    *,
    to_agent: str = "ARCHON",
    channel: Optional[str] = None,
    hz: Optional[float] = None,
    kind: str = "hz",
) -> Dict[str, Any]:
    """Send a signed mesh message on a frequency lane."""
    from pocket.mesh_disk import send_message

    ch = normalize_channel(channel, hz=hz)
    msg = send_message(from_agent, to_agent, body, channel=ch, kind=kind)
    return {
        "ok": msg.get("ok"),
        "channel": ch,
        "hz_mhz": hz_for_channel(ch),
        "message": msg,
    }


def mesh_leave(
    agent_id: str,
    name: str,
    content: str,
    *,
    notify: Optional[List[str]] = None,
    channel: Optional[str] = None,
    hz: Optional[float] = None,
    announce: bool = True,
) -> Dict[str, Any]:
    """Leave an artifact and optionally announce on a frequency channel."""
    from pocket.mesh_disk import leave_artifact, send_message

    art = leave_artifact(agent_id, name, content, notify=notify)
    ch = normalize_channel(channel, hz=hz)
    announce_msg = None
    if announce:
        announce_msg = send_message(
            agent_id,
            (notify or ["ARCHON"])[0],
            f"hz_artifact:{name}@{ch}",
            channel=ch,
            kind="artifact",
            artifact=art.get("path"),
        )
    return {
        "ok": art.get("ok"),
        "artifact": art,
        "channel": ch,
        "hz_mhz": hz_for_channel(ch),
        "announce": announce_msg,
        "at": time.time(),
    }


def tune(agent_id: str, hz: float | int, *, note: str = "") -> Dict[str, Any]:
    """Register agent interest on a frequency lane (artifact + channel note)."""
    ch = channel_for_hz(hz)
    body = (
        f"# Tune\n\n"
        f"- agent: `{agent_id}`\n"
        f"- hz_mhz: {hz}\n"
        f"- channel: `{ch}`\n"
        f"- note: {note or '—'}\n"
        f"- at: {time.time()}\n"
    )
    return mesh_leave(
        agent_id,
        f"tune_{ch}.md",
        body,
        notify=["ARCHON"],
        channel=ch,
        hz=float(hz),
    )
