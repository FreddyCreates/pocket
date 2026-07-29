"""Client device awareness — phone vs computer (and tablet)."""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

PHONE_UA = re.compile(
    r"Mobile|Android.*Mobile|iPhone|iPod|webOS|BlackBerry|IEMobile|Opera Mini|Windows Phone",
    re.I,
)
TABLET_UA = re.compile(r"iPad|Android(?!.*Mobile)|Tablet|Kindle|Silk", re.I)


def normalize_device(raw: Any = None, *, user_agent: str = "", header: str = "") -> Dict[str, Any]:
    """Normalize client-reported or UA-derived device profile."""
    d: Dict[str, Any] = {}
    if isinstance(raw, dict):
        d = dict(raw)
    elif isinstance(raw, str) and raw.strip():
        kind = raw.strip().lower()
        d = {"kind": kind}

    # Header shortcut: phone | tablet | computer
    h = (header or "").strip().lower()
    if h in ("phone", "mobile", "tablet", "computer", "desktop"):
        d.setdefault("kind", "phone" if h in ("phone", "mobile") else ("tablet" if h == "tablet" else "computer"))

    kind = (d.get("kind") or "").strip().lower()
    if kind in ("mobile",):
        kind = "phone"
    if kind in ("desktop", "pc", "laptop"):
        kind = "computer"

    ua = (d.get("ua") or user_agent or "")[:300]
    if kind not in ("phone", "tablet", "computer"):
        if PHONE_UA.search(ua):
            kind = "phone"
        elif TABLET_UA.search(ua):
            kind = "tablet"
        else:
            kind = "computer"

    w = int(d.get("width") or 0) or None
    hgt = int(d.get("height") or 0) or None
    touch = bool(d.get("touch")) if "touch" in d else None
    coarse = bool(d.get("coarse")) if "coarse" in d else None
    standalone = bool(d.get("standalone")) if "standalone" in d else None

    # Width can refine UA misses (desktop browser narrow window stays computer unless UA mobile)
    if kind == "computer" and w and w <= 720 and (touch or coarse):
        kind = "phone"
    if kind == "phone" and w and w >= 1024 and not PHONE_UA.search(ua):
        kind = "tablet" if (touch or coarse) else "computer"

    label = {"phone": "Phone", "tablet": "Tablet", "computer": "Computer"}.get(kind, "Computer")
    remote = kind in ("phone", "tablet")

    return {
        "kind": kind,
        "label": label,
        "remote": remote,
        "width": w,
        "height": hgt,
        "touch": touch,
        "coarse": coarse,
        "standalone": standalone,
        "ua": ua[:200] if ua else None,
        "platform": (d.get("platform") or "")[:80] or None,
        "source": d.get("source") or ("client" if raw else ("header" if h else "ua")),
    }


def device_from_request(headers, body: Optional[dict] = None) -> Dict[str, Any]:
    body = body or {}
    raw = body.get("device") or body.get("client_device")
    header = ""
    try:
        header = headers.get("X-Pocket-Device") or headers.get("x-pocket-device") or ""
    except Exception:
        header = ""
    try:
        ua = headers.get("User-Agent") or headers.get("user-agent") or ""
    except Exception:
        ua = ""
    return normalize_device(raw, user_agent=ua, header=header)


def agent_context_line(device: Optional[Dict[str, Any]]) -> str:
    """Short prefix so coding/plan agents know where the human is."""
    if not device:
        return ""
    kind = device.get("kind") or "computer"
    if kind == "phone":
        return (
            "[Client device: PHONE — user is remote (mobile UI). "
            "Prefer concise results; do not assume they can see this PC screen unless using Desktop mode. "
            "Jobs still run on the POCKET host computer.]\n\n"
        )
    if kind == "tablet":
        return (
            "[Client device: TABLET — touch remote UI. Jobs run on the POCKET host computer.]\n\n"
        )
    return (
        "[Client device: COMPUTER — user is likely on a desktop/laptop browser. "
        "Jobs run on the POCKET host.]\n\n"
    )


def should_inject_context(mode: str) -> bool:
    return (mode or "").lower() in {
        "codex",
        "claude",
        "grok",
        "plan",
        "handoff",
        "ask",
        "browser",
    }
