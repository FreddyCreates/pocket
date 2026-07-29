"""Multi-user accounts for POCKET (real login, not shared single password only)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket"
USERS_FILE = ROOT / "users.json"
_lock = Lock()

INVITE_ENV = "POCKET_INVITE_CODE"


def _hash(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()


def _load() -> Dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    if USERS_FILE.exists():
        try:
            return json.loads(USERS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    data = {
        "invite": os.environ.get(INVITE_ENV) or secrets.token_urlsafe(10),
        "users": {},
        "created_at": time.time(),
    }
    # seed admin from basic auth password if present
    try:
        from pocket.auth import expected_password, expected_user

        admin = expected_user() or "pocket"
        salt = secrets.token_hex(8)
        data["users"][admin] = {
            "user": admin,
            "salt": salt,
            "hash": _hash(expected_password(), salt),
            "role": "admin",
            "created_at": time.time(),
            "display": "Operator",
        }
    except Exception:
        pass
    _save(data)
    # write invite for operator
    try:
        (ROOT / "INVITE.txt").write_text(
            f"POCKET multi-user invite code:\n{data['invite']}\n\n"
            "Share with people you trust. They register in the app with this code.\n",
            encoding="utf-8",
        )
    except Exception:
        pass
    return data


def _save(data: Dict[str, Any]) -> None:
    USERS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def invite_code() -> str:
    with _lock:
        return str(_load().get("invite") or "")


def list_users() -> List[Dict[str, Any]]:
    with _lock:
        data = _load()
        out = []
        for u, rec in (data.get("users") or {}).items():
            out.append(
                {
                    "user": u,
                    "role": rec.get("role") or "member",
                    "display": rec.get("display") or u,
                    "created_at": rec.get("created_at"),
                }
            )
        return out


MAX_SEATS = int(os.environ.get("POCKET_MAX_SEATS") or "25")


def register(user: str, password: str, invite: str, display: str = "", *, accepted_terms: bool = False) -> Dict[str, Any]:
    user = (user or "").strip().lower()
    password = password or ""
    invite = (invite or "").strip()
    if len(user) < 2 or len(password) < 8:
        return {"ok": False, "error": "user min 2 chars, password min 8"}
    if not accepted_terms:
        return {"ok": False, "error": "you must accept the terms (docs/LEGAL.md)"}
    if user in ("admin", "root", "system"):
        return {"ok": False, "error": "reserved username"}
    with _lock:
        data = _load()
        if not hmac.compare_digest(invite, str(data.get("invite") or "")):
            return {"ok": False, "error": "invalid invite code"}
        n = len(data.get("users") or {})
        if n >= MAX_SEATS:
            return {"ok": False, "error": f"seat limit reached ({MAX_SEATS})"}
        if user in (data.get("users") or {}):
            return {"ok": False, "error": "user exists"}
        salt = secrets.token_hex(8)
        data.setdefault("users", {})[user] = {
            "user": user,
            "salt": salt,
            "hash": _hash(password, salt),
            "role": "member",
            "display": (display or user)[:40],
            "created_at": time.time(),
            "accepted_terms_at": time.time(),
        }
        _save(data)
    return {"ok": True, "user": user, "role": "member"}


def verify(user: str, password: str) -> Optional[Dict[str, Any]]:
    user = (user or "").strip().lower()
    with _lock:
        data = _load()
        rec = (data.get("users") or {}).get(user)
        if not rec:
            # fall back to legacy single admin password
            try:
                from pocket.auth import expected_password, expected_user

                if user == (expected_user() or "pocket").lower() and hmac.compare_digest(
                    password, expected_password()
                ):
                    return {"user": user, "role": "admin", "display": "Operator"}
            except Exception:
                pass
            return None
        if hmac.compare_digest(rec.get("hash") or "", _hash(password, rec.get("salt") or "")):
            return {
                "user": user,
                "role": rec.get("role") or "member",
                "display": rec.get("display") or user,
            }
    return None


TOKEN_TTL_SEC = 86400 * 7  # 7 days absolute
TOKEN_IDLE_SEC = 86400 * 2  # 2 days idle


def issue_token(user: str) -> str:
    """Opaque session token stored server-side."""
    tok = secrets.token_urlsafe(24)
    now = time.time()
    with _lock:
        data = _load()
        data.setdefault("tokens", {})[tok] = {
            "user": user,
            "at": now,
            "last": now,
        }
        cut = now - TOKEN_TTL_SEC
        data["tokens"] = {k: v for k, v in data["tokens"].items() if (v.get("at") or 0) > cut}
        _save(data)
    return tok


def revoke_token(token: str) -> bool:
    if not token:
        return False
    with _lock:
        data = _load()
        toks = data.setdefault("tokens", {})
        if token in toks:
            del toks[token]
            _save(data)
            return True
    return False


def revoke_all_for_user(user: str) -> int:
    user = (user or "").strip().lower()
    n = 0
    with _lock:
        data = _load()
        toks = data.setdefault("tokens", {})
        drop = [k for k, v in toks.items() if (v.get("user") or "").lower() == user]
        for k in drop:
            del toks[k]
            n += 1
        _save(data)
    return n


def change_password(user: str, old_password: str, new_password: str) -> Dict[str, Any]:
    user = (user or "").strip().lower()
    if len(new_password or "") < 8:
        return {"ok": False, "error": "new password min 8"}
    with _lock:
        data = _load()
        rec = (data.get("users") or {}).get(user)
        if not rec:
            # allow legacy admin via expected_password
            try:
                from pocket.auth import expected_password, expected_user

                if user == (expected_user() or "pocket").lower() and hmac.compare_digest(
                    old_password, expected_password()
                ):
                    salt = secrets.token_hex(8)
                    data.setdefault("users", {})[user] = {
                        "user": user,
                        "salt": salt,
                        "hash": _hash(new_password, salt),
                        "role": "admin",
                        "display": "Operator",
                        "created_at": time.time(),
                    }
                    _save(data)
                    return {"ok": True, "user": user}
            except Exception:
                pass
            return {"ok": False, "error": "user not found"}
        if not hmac.compare_digest(rec.get("hash") or "", _hash(old_password, rec.get("salt") or "")):
            return {"ok": False, "error": "old password incorrect"}
        salt = secrets.token_hex(8)
        rec["salt"] = salt
        rec["hash"] = _hash(new_password, salt)
        rec["password_changed_at"] = time.time()
        _save(data)
    revoke_all_for_user(user)
    return {"ok": True, "user": user, "note": "all sessions revoked — sign in again"}


def rotate_invite() -> Dict[str, Any]:
    """Admin: issue a new invite code."""
    with _lock:
        data = _load()
        code = secrets.token_urlsafe(12)
        data["invite"] = code
        data["invite_rotated_at"] = time.time()
        _save(data)
    try:
        (ROOT / "INVITE.txt").write_text(
            f"POCKET multi-user invite code:\n{code}\n\n"
            "Share with people you trust. They register in the app with this code.\n",
            encoding="utf-8",
        )
    except Exception:
        pass
    return {"ok": True, "invite": code}


def user_from_token(token: str) -> Optional[Dict[str, Any]]:
    if not token:
        return None
    now = time.time()
    with _lock:
        data = _load()
        rec = (data.get("tokens") or {}).get(token)
        if not rec:
            return None
        created = float(rec.get("at") or 0)
        last = float(rec.get("last") or created)
        if now - created > TOKEN_TTL_SEC or now - last > TOKEN_IDLE_SEC:
            try:
                del data["tokens"][token]
                _save(data)
            except Exception:
                pass
            return None
        rec["last"] = now
        _save(data)
        u = rec.get("user")
        urec = (data.get("users") or {}).get(u) or {}
        role = urec.get("role") or "member"
        # legacy operator token without users entry
        if not urec:
            try:
                from pocket.auth import expected_user

                if (u or "").lower() == (expected_user() or "pocket").lower():
                    role = "admin"
            except Exception:
                pass
        return {
            "user": u,
            "role": role,
            "display": urec.get("display") or u,
        }
