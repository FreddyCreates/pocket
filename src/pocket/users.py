"""Multi-user seats for POCKET.

Owner (admin) stays owner. Invited people create THEIR OWN accounts —
they never log into the operator account.

Seat invites are single-use (or limited-use) cryptographic keys.
We store only SHA-256 hashes of invite keys; the raw key is shown once when minted.
"""

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
MAX_SEATS = int(os.environ.get("POCKET_MAX_SEATS") or "25")
TOKEN_TTL_SEC = 86400 * 7
TOKEN_IDLE_SEC = 86400 * 2


def _hash(pw: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode("utf-8"), salt.encode("utf-8"), 120_000).hex()


def _sha_key(raw: str) -> str:
    return hashlib.sha256((raw or "").encode("utf-8")).hexdigest()


def _load() -> Dict[str, Any]:
    ROOT.mkdir(parents=True, exist_ok=True)
    if USERS_FILE.exists():
        try:
            data = json.loads(USERS_FILE.read_text(encoding="utf-8"))
            return _migrate(data)
        except Exception:
            pass
    data = _bootstrap()
    _save(data)
    _write_invite_readme(data)
    return data


def _bootstrap() -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "schema": "pocket.users.v2",
        "users": {},
        "seat_invites": [],
        "tokens": {},
        "created_at": time.time(),
    }
    # seed owner/admin from host ACCESS — never overwritten on later loads
    try:
        from pocket.auth import expected_password, expected_user

        admin = (expected_user() or "pocket").strip().lower()
        salt = secrets.token_hex(8)
        data["users"][admin] = {
            "user": admin,
            "salt": salt,
            "hash": _hash(expected_password(), salt),
            "role": "admin",
            "created_at": time.time(),
            "display": "Owner",
            "is_owner": True,
        }
    except Exception:
        pass
    # one open seat invite for first ship (raw written to file once)
    raw = os.environ.get(INVITE_ENV) or ("pk_seat_" + secrets.token_urlsafe(18))
    data["seat_invites"].append(
        {
            "id": "inv_" + secrets.token_hex(6),
            "hash": _sha_key(raw),
            "prefix": raw[:12] + "…",
            "label": "bootstrap",
            "max_uses": 10,
            "uses": 0,
            "created_at": time.time(),
            "expires_at": time.time() + 86400 * 90,
            "created_by": "system",
            "_bootstrap_raw": raw,  # stripped after first write
        }
    )
    return data


def _migrate(data: Dict[str, Any]) -> Dict[str, Any]:
    """Upgrade v1 single shared invite → seat_invites without logging anyone out."""
    changed = False
    if "seat_invites" not in data:
        data["seat_invites"] = []
        changed = True
    # legacy single invite string → one multi-use seat key (hash only; raw unknown if already shared)
    legacy = (data.get("invite") or "").strip()
    if legacy and not data["seat_invites"]:
        data["seat_invites"].append(
            {
                "id": "inv_legacy",
                "hash": _sha_key(legacy),
                "prefix": legacy[:12] + "…",
                "label": "legacy-shared",
                "max_uses": 25,
                "uses": 0,
                "created_at": time.time(),
                "expires_at": time.time() + 86400 * 90,
                "created_by": "migrate",
                "note": "Migrated from old single invite. Prefer mint_seat_invite for new users.",
            }
        )
        changed = True
    # mark first admin as owner
    users = data.get("users") or {}
    for u, rec in users.items():
        if (rec.get("role") or "") == "admin" and "is_owner" not in rec:
            rec["is_owner"] = True
            changed = True
            break
    data["schema"] = "pocket.users.v2"
    if changed:
        _save(data)
        _write_invite_readme(data)
    return data


def _save(data: Dict[str, Any]) -> None:
    # never persist bootstrap raw keys
    for inv in data.get("seat_invites") or []:
        inv.pop("_bootstrap_raw", None)
    USERS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_invite_readme(data: Dict[str, Any], *, last_raw: str = "") -> None:
    """Operator-facing instructions — not a shared login password."""
    lines = [
        "POCKET multi-user (OWNER stays owner)",
        "====================================",
        "",
        "Users do NOT log into your operator account.",
        "They create THEIR OWN username + password with a seat invite key.",
        "",
        "Mint new single-use keys (admin API or desk later):",
        "  POST /v1/admin/invites  { \"label\": \"alice\", \"max_uses\": 1 }",
        "",
    ]
    if last_raw:
        lines += [
            "NEW SEAT KEY (show once — store SHA only on server):",
            last_raw,
            "",
            "Give this key to ONE person. They open Register and create their account.",
            "",
        ]
    # bootstrap raw if present in memory before strip
    for inv in data.get("seat_invites") or []:
        raw = inv.get("_bootstrap_raw")
        if raw:
            lines += [
                "Bootstrap seat key (rotate after first users):",
                raw,
                f"  uses {inv.get('uses')}/{inv.get('max_uses')}  id={inv.get('id')}",
                "",
            ]
    lines += [
        "Your owner login remains ACCESS.txt / admin user — separate from member seats.",
        f"Max seats: {MAX_SEATS}",
    ]
    try:
        (ROOT / "INVITE.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    except Exception:
        pass


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
                    "is_owner": bool(rec.get("is_owner")),
                    "created_at": rec.get("created_at"),
                }
            )
        return out


def mint_seat_invite(
    *,
    label: str = "",
    max_uses: int = 1,
    expires_days: int = 30,
    created_by: str = "admin",
) -> Dict[str, Any]:
    """Create a cryptographic seat key. Raw key returned once; server stores SHA-256 only."""
    max_uses = max(1, min(50, int(max_uses or 1)))
    expires_days = max(1, min(365, int(expires_days or 30)))
    raw = "pk_seat_" + secrets.token_urlsafe(24)
    rec = {
        "id": "inv_" + secrets.token_hex(8),
        "hash": _sha_key(raw),
        "prefix": raw[:14] + "…",
        "label": (label or "seat")[:40],
        "max_uses": max_uses,
        "uses": 0,
        "created_at": time.time(),
        "expires_at": time.time() + 86400 * expires_days,
        "created_by": (created_by or "admin")[:40],
    }
    with _lock:
        data = _load()
        data.setdefault("seat_invites", []).append(rec)
        _save(data)
        _write_invite_readme(data, last_raw=raw)
    return {
        "ok": True,
        "invite_key": raw,
        "id": rec["id"],
        "label": rec["label"],
        "max_uses": max_uses,
        "expires_at": rec["expires_at"],
        "message": "Give invite_key to the new user. They register THEIR own account. You stay owner.",
    }


def list_invites() -> List[Dict[str, Any]]:
    """Admin view — never returns raw keys or hashes."""
    with _lock:
        data = _load()
        out = []
        now = time.time()
        for inv in data.get("seat_invites") or []:
            out.append(
                {
                    "id": inv.get("id"),
                    "prefix": inv.get("prefix"),
                    "label": inv.get("label"),
                    "max_uses": inv.get("max_uses"),
                    "uses": inv.get("uses"),
                    "remaining": max(0, int(inv.get("max_uses") or 0) - int(inv.get("uses") or 0)),
                    "expired": now > float(inv.get("expires_at") or 0),
                    "created_at": inv.get("created_at"),
                    "expires_at": inv.get("expires_at"),
                    "created_by": inv.get("created_by"),
                }
            )
        return out


def _consume_invite(data: Dict[str, Any], raw_invite: str) -> Optional[str]:
    """Validate seat key by SHA-256; increment uses. Returns invite id or None."""
    raw = (raw_invite or "").strip()
    if not raw:
        return None
    h = _sha_key(raw)
    now = time.time()
    for inv in data.get("seat_invites") or []:
        stored = str(inv.get("hash") or "")
        if not stored or not hmac.compare_digest(stored, h):
            continue
        if now > float(inv.get("expires_at") or 0):
            return None
        uses = int(inv.get("uses") or 0)
        max_u = int(inv.get("max_uses") or 1)
        if uses >= max_u:
            return None
        inv["uses"] = uses + 1
        inv["last_used_at"] = now
        return str(inv.get("id") or "")
    # legacy v1 plaintext invite field
    legacy = (data.get("invite") or "").strip()
    if legacy and hmac.compare_digest(raw, legacy):
        return "legacy"
    return None


def register(
    user: str,
    password: str,
    invite: str,
    display: str = "",
    *,
    accepted_terms: bool = False,
) -> Dict[str, Any]:
    """Create a NEW member seat. Never becomes owner. Never touches owner password."""
    user = (user or "").strip().lower()
    password = password or ""
    invite = (invite or "").strip()
    if len(user) < 2 or len(password) < 8:
        return {"ok": False, "error": "user min 2 chars, password min 8"}
    if not accepted_terms:
        return {"ok": False, "error": "you must accept the terms (docs/LEGAL.md)"}
    if user in ("admin", "root", "system", "owner"):
        return {"ok": False, "error": "reserved username"}
    with _lock:
        data = _load()
        # block registering as existing owner username
        existing = (data.get("users") or {}).get(user)
        if existing:
            return {"ok": False, "error": "user exists — sign in with YOUR password, do not use owner login"}
        n_members = sum(
            1
            for rec in (data.get("users") or {}).values()
            if (rec.get("role") or "member") != "admin" or not rec.get("is_owner")
        )
        # count all seats except we allow max total users
        n = len(data.get("users") or {})
        if n >= MAX_SEATS:
            return {"ok": False, "error": f"seat limit reached ({MAX_SEATS})"}
        inv_id = _consume_invite(data, invite)
        if not inv_id:
            return {"ok": False, "error": "invalid or exhausted seat invite key"}
        salt = secrets.token_hex(8)
        data.setdefault("users", {})[user] = {
            "user": user,
            "salt": salt,
            "hash": _hash(password, salt),
            "role": "member",
            "is_owner": False,
            "display": (display or user)[:40],
            "created_at": time.time(),
            "accepted_terms_at": time.time(),
            "seat_invite_id": inv_id,
        }
        _save(data)
    return {
        "ok": True,
        "user": user,
        "role": "member",
        "message": "Your own seat is ready. You are not the owner account.",
    }


def verify(user: str, password: str) -> Optional[Dict[str, Any]]:
    user = (user or "").strip().lower()
    with _lock:
        data = _load()
        rec = (data.get("users") or {}).get(user)
        if not rec:
            try:
                from pocket.auth import expected_password, expected_user

                if user == (expected_user() or "pocket").lower() and hmac.compare_digest(
                    password, expected_password()
                ):
                    return {
                        "user": user,
                        "role": "admin",
                        "display": "Owner",
                        "is_owner": True,
                    }
            except Exception:
                pass
            return None
        if hmac.compare_digest(rec.get("hash") or "", _hash(password, rec.get("salt") or "")):
            return {
                "user": user,
                "role": rec.get("role") or "member",
                "display": rec.get("display") or user,
                "is_owner": bool(rec.get("is_owner")),
            }
    return None


def issue_token(user: str) -> str:
    tok = secrets.token_urlsafe(24)
    now = time.time()
    with _lock:
        data = _load()
        data.setdefault("tokens", {})[tok] = {"user": user, "at": now, "last": now}
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
                        "display": "Owner",
                        "is_owner": True,
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
    return {"ok": True, "user": user, "note": "your sessions revoked — sign in again with new password"}


def rotate_invite() -> Dict[str, Any]:
    """Mint a fresh multi-use operator invite (legacy alias → mint_seat_invite)."""
    return mint_seat_invite(label="rotated", max_uses=10, expires_days=60, created_by="rotate")


def invite_code() -> str:
    """Deprecated: do not expose raw keys via API. Returns empty; use list_invites."""
    return ""


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
        if not urec:
            try:
                from pocket.auth import expected_user

                if (u or "").lower() == (expected_user() or "pocket").lower():
                    role = "admin"
                    return {"user": u, "role": role, "display": "Owner", "is_owner": True}
            except Exception:
                pass
        return {
            "user": u,
            "role": role,
            "display": urec.get("display") or u,
            "is_owner": bool(urec.get("is_owner")),
        }
