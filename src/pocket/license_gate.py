"""Researcher License acceptance gate for public downloads."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

ROOT = Path.home() / ".pocket"
ACCEPT_LOG = ROOT / "license_accepts.jsonl"
SECRET_PATH = ROOT / "license_hmac.key"
_lock = Lock()

LICENSE_ID = "POCKET-Researcher-1.0"
LICENSE_TITLE = "POCKET Researcher License (Non-Commercial Research)"
COOKIE_NAME = "pocket_researcher_ok"
TOKEN_TTL_SEC = 60 * 60 * 24 * 30  # 30 days


def _secret() -> bytes:
    ROOT.mkdir(parents=True, exist_ok=True)
    if SECRET_PATH.exists():
        return SECRET_PATH.read_bytes()
    key = secrets.token_bytes(32)
    SECRET_PATH.write_bytes(key)
    try:
        os.chmod(SECRET_PATH, 0o600)
    except Exception:
        pass
    return key


def license_meta() -> Dict[str, Any]:
    return {
        "ok": True,
        "id": LICENSE_ID,
        "title": LICENSE_TITLE,
        "version": "1.0",
        "spdx": "LicenseRef-POCKET-Researcher-1.0",
        "url": "/license",
        "text_url": "/license/text",
        "download_requires_accept": True,
        "commercial": False,
        "summary": (
            "Downloads are for research and evaluation only. "
            "No commercial production, resale, or marketplace redistribution "
            "without a separate written license from ItsNotAI Labs."
        ),
    }


def issue_token(*, ip: str = "", user_agent: str = "") -> str:
    """HMAC token proving license accept."""
    ts = int(time.time())
    nonce = secrets.token_hex(8)
    payload = f"{LICENSE_ID}|{ts}|{nonce}|{(ip or '')[:64]}"
    sig = hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    tok = f"{ts}.{nonce}.{sig}"
    _log_accept(ip=ip, user_agent=user_agent, token_prefix=tok[:20])
    return tok


def verify_token(token: str) -> bool:
    if not token or token.count(".") != 2:
        return False
    try:
        ts_s, nonce, sig = token.split(".", 2)
        ts = int(ts_s)
        if abs(time.time() - ts) > TOKEN_TTL_SEC:
            return False
        payload = f"{LICENSE_ID}|{ts}|{nonce}|"
        # IP not rebound on verify (mobile networks change); accept any IP component
        # Recompute with empty IP suffix match by checking hmac of known form is hard —
        # store only time+nonce in sig material without IP for verify:
        # Re-issue format: sign without IP for portable cookies
        payload2 = f"{LICENSE_ID}|{ts}|{nonce}"
        expect = hmac.new(_secret(), payload2.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        # Also try old form with empty IP for forward compat
        if hmac.compare_digest(expect, sig):
            return True
        payload3 = f"{LICENSE_ID}|{ts}|{nonce}|"
        expect3 = hmac.new(_secret(), payload3.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
        return hmac.compare_digest(expect3, sig)
    except Exception:
        return False


def issue_token_v2(*, ip: str = "", user_agent: str = "") -> str:
    ts = int(time.time())
    nonce = secrets.token_hex(8)
    payload = f"{LICENSE_ID}|{ts}|{nonce}"
    sig = hmac.new(_secret(), payload.encode("utf-8"), hashlib.sha256).hexdigest()[:32]
    tok = f"{ts}.{nonce}.{sig}"
    _log_accept(ip=ip, user_agent=user_agent, token_prefix=tok[:20])
    return tok


def _log_accept(*, ip: str, user_agent: str, token_prefix: str) -> None:
    try:
        ROOT.mkdir(parents=True, exist_ok=True)
        rec = {
            "at": time.time(),
            "license": LICENSE_ID,
            "ip": (ip or "")[:80],
            "ua": (user_agent or "")[:160],
            "token_prefix": token_prefix,
        }
        with _lock:
            with ACCEPT_LOG.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec) + "\n")
    except Exception:
        pass


def token_from_headers(headers) -> str:
    # Cookie
    cookie = headers.get("Cookie") or headers.get("cookie") or ""
    for part in cookie.split(";"):
        part = part.strip()
        if part.startswith(COOKIE_NAME + "="):
            return part.split("=", 1)[-1].strip()
    # Explicit header
    return (
        headers.get("X-Pocket-License")
        or headers.get("x-pocket-license")
        or ""
    ).strip()


def download_allowed(headers, query_token: str = "") -> bool:
    tok = query_token or token_from_headers(headers)
    return verify_token(tok)


def accept_response(*, ip: str = "", user_agent: str = "") -> Dict[str, Any]:
    tok = issue_token_v2(ip=ip, user_agent=user_agent)
    return {
        "ok": True,
        "license_id": LICENSE_ID,
        "token": tok,
        "cookie": f"{COOKIE_NAME}={tok}; Path=/; Max-Age={TOKEN_TTL_SEC}; SameSite=Lax; HttpOnly",
        "message": "Researcher License accepted. Downloads unlocked for this browser.",
        "ttl_sec": TOKEN_TTL_SEC,
    }
