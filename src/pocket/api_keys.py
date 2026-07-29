"""Sellable API keys for POCKET AI API — create, verify, meter usage."""

from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket"
KEYS_FILE = ROOT / "api_keys.json"
_lock = Lock()

PREFIX = "sk_pocket_"


def _load() -> Dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    if KEYS_FILE.exists():
        try:
            return json.loads(KEYS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    data = {"schema": "pocket.api_keys.v1", "keys": {}, "created_at": time.time()}
    _save(data)
    return data


def _save(data: Dict[str, Any]) -> None:
    KEYS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def create_key(
    *,
    name: str = "default",
    owner: str = "pocket",
    tier: str = "pro",
    monthly_quota: int = 10_000,
) -> Dict[str, Any]:
    """Create a new API key. Returns full secret once."""
    raw = PREFIX + secrets.token_urlsafe(32).replace("-", "").replace("_", "")[:40]
    kid = f"key-{secrets.token_hex(6)}"
    rec = {
        "id": kid,
        "name": (name or "default")[:60],
        "owner": (owner or "pocket")[:40],
        "tier": (tier or "pro")[:20],
        "hash": _hash_key(raw),
        "prefix": raw[:16] + "…",
        "created_at": time.time(),
        "last_used_at": None,
        "revoked": False,
        "monthly_quota": int(monthly_quota),
        "usage": {
            "calls": 0,
            "pock_burned": 0,
            "by_agent": {},
            "by_day": {},
        },
    }
    with _lock:
        data = _load()
        data.setdefault("keys", {})[kid] = rec
        _save(data)
    return {
        "ok": True,
        "id": kid,
        "name": rec["name"],
        "tier": rec["tier"],
        "owner": rec["owner"],
        "key": raw,  # shown once
        "prefix": rec["prefix"],
        "monthly_quota": rec["monthly_quota"],
        "note": "Store this key now — it will not be shown again.",
        "auth_header": f"Authorization: Bearer {raw}",
    }


def list_keys(*, owner: str = "") -> List[Dict[str, Any]]:
    with _lock:
        data = _load()
        out = []
        for rec in (data.get("keys") or {}).values():
            if owner and rec.get("owner") != owner:
                continue
            out.append(_public(rec))
        return sorted(out, key=lambda x: -(x.get("created_at") or 0))


def revoke_key(key_id: str) -> Dict[str, Any]:
    with _lock:
        data = _load()
        rec = (data.get("keys") or {}).get(key_id)
        if not rec:
            return {"ok": False, "error": "key not found"}
        rec["revoked"] = True
        rec["revoked_at"] = time.time()
        _save(data)
        return {"ok": True, "id": key_id, "revoked": True}


def verify_key(raw: str) -> Optional[Dict[str, Any]]:
    raw = (raw or "").strip()
    if not raw.startswith(PREFIX):
        return None
    h = _hash_key(raw)
    with _lock:
        data = _load()
        for rec in (data.get("keys") or {}).values():
            if rec.get("revoked"):
                continue
            if hmac.compare_digest(str(rec.get("hash") or ""), h):
                # Hard-stop monthly quota
                u = rec.get("usage") or {}
                calls = int(u.get("calls") or 0)
                quota = int(rec.get("monthly_quota") or 0)
                if quota > 0 and calls >= quota:
                    return None  # treated as unauthorized / exhausted
                rec["last_used_at"] = time.time()
                _save(data)
                pub = _public(rec)
                pub["_quota_ok"] = True
                return pub
    return None


def check_quota(key_id: str) -> Dict[str, Any]:
    with _lock:
        data = _load()
        rec = (data.get("keys") or {}).get(key_id)
        if not rec:
            return {"ok": False, "error": "key not found"}
        u = rec.get("usage") or {}
        calls = int(u.get("calls") or 0)
        quota = int(rec.get("monthly_quota") or 0)
        if quota > 0 and calls >= quota:
            return {
                "ok": False,
                "error": "monthly_quota_exceeded",
                "calls": calls,
                "quota": quota,
            }
        return {"ok": True, "calls": calls, "quota": quota, "remaining": max(0, quota - calls) if quota else None}


def record_usage(key_id: str, *, agent: str = "", pock: int = 0) -> None:
    if not key_id:
        return
    day = time.strftime("%Y-%m-%d")
    with _lock:
        data = _load()
        rec = (data.get("keys") or {}).get(key_id)
        if not rec:
            return
        u = rec.setdefault("usage", {"calls": 0, "pock_burned": 0, "by_agent": {}, "by_day": {}})
        u["calls"] = int(u.get("calls") or 0) + 1
        u["pock_burned"] = int(u.get("pock_burned") or 0) + int(pock or 0)
        if agent:
            ba = u.setdefault("by_agent", {})
            ba[agent] = int(ba.get(agent) or 0) + 1
        bd = u.setdefault("by_day", {})
        bd[day] = int(bd.get(day) or 0) + 1
        rec["last_used_at"] = time.time()
        _save(data)


def usage_for(key_id: str = "", *, owner: str = "") -> Dict[str, Any]:
    with _lock:
        data = _load()
        keys = data.get("keys") or {}
        if key_id:
            rec = keys.get(key_id)
            if not rec:
                return {"ok": False, "error": "not found"}
            return {"ok": True, "key": _public(rec), "usage": rec.get("usage") or {}}
        total_calls = 0
        total_pock = 0
        items = []
        own = (owner or "").strip().lower()
        for rec in keys.values():
            if own and (rec.get("owner") or "").lower() != own:
                continue
            u = rec.get("usage") or {}
            total_calls += int(u.get("calls") or 0)
            total_pock += int(u.get("pock_burned") or 0)
            items.append(_public(rec))
        return {
            "ok": True,
            "total_calls": total_calls,
            "total_pock_burned": total_pock,
            "keys": items,
        }


def extract_bearer(headers) -> str:
    """Pull API key from Authorization Bearer or X-API-Key."""
    try:
        x = headers.get("X-API-Key") or headers.get("x-api-key") or ""
        if x.strip().startswith(PREFIX):
            return x.strip()
    except Exception:
        pass
    try:
        auth = headers.get("Authorization") or headers.get("authorization") or ""
    except Exception:
        auth = ""
    if auth.lower().startswith("bearer "):
        tok = auth[7:].strip()
        if tok.startswith(PREFIX):
            return tok
    return ""


def _public(rec: Dict[str, Any]) -> Dict[str, Any]:
    u = rec.get("usage") or {}
    return {
        "id": rec.get("id"),
        "name": rec.get("name"),
        "owner": rec.get("owner"),
        "tier": rec.get("tier"),
        "prefix": rec.get("prefix"),
        "created_at": rec.get("created_at"),
        "last_used_at": rec.get("last_used_at"),
        "revoked": bool(rec.get("revoked")),
        "monthly_quota": rec.get("monthly_quota"),
        "usage": {
            "calls": u.get("calls") or 0,
            "pock_burned": u.get("pock_burned") or 0,
            "by_agent": u.get("by_agent") or {},
        },
    }
