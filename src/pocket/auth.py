"""Access control for POCKET — required password when exposed to the internet."""

from __future__ import annotations

import base64
import hmac
import os
import secrets
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Mapping, Optional, Tuple

# Prefer user home (survives repo moves); fall back to repo .pocket
HOME_AUTH = Path.home() / ".pocket"
REPO_AUTH = Path(__file__).resolve().parents[2] / ".pocket"
AUTH_DIR = HOME_AUTH
AUTH_FILE = AUTH_DIR / "access.env"
ACCESS_NOTE = AUTH_DIR / "ACCESS.txt"
AUTH_USER_ENV = "POCKET_BASIC_AUTH_USER"
AUTH_PASS_ENV = "POCKET_BASIC_AUTH_PASSWORD"
DEFAULT_USER = "pocket"

# Public paths (minimal surface). App UI is public shell; APIs require auth.
# /v1/ai catalog is public so buyers can discover the sellable API product.
PUBLIC_PATHS = frozenset({
    "/tour",
    "/product",
    "/present",
    "/landing",
    "/home",
    "/developers",
    "/api",
    "/docs/api",
    "/studio",
    "/get",
    "/start",
    "/install",
    "/health",
    "/v1/health",
    "/v1/runtime/heartbeat",
    "/v1/heartbeat",
    "/v1/status",
    "/",
    # Desk shell is public HTML; APIs still require session/token after login
    "/desk",
    "/app",
    "/desktop",
    "/chat",
    "/v1/auth/login",
    "/v1/auth/register",
    "/v1/auth/desktop",
    "/v1/auth/local",
    "/v1/ai",
    "/v1/ai/agents",
    "/v1/ai/pricing",
    "/v1/ready",
    "/v1/legal",
    "/v1/ai/openapi",
    # Desktop Electron package downloads (public — same as marketing landing)
    "/download",
    "/download/desktop",
    "/download/windows",
    "/v1/desktop/releases",
    "/v1/product/channels",
    "/v1/channels",
})

# Prefixes that remain public (file downloads under /download/files/…)
PUBLIC_PREFIXES = (
    "/download/files/",
    "/download/desktop/",
)

# Rate limit failed logins: max N failures per IP per window
_fail_lock = Lock()
_fail_log: dict[str, list[float]] = defaultdict(list)
MAX_FAILS = 12
FAIL_WINDOW = 300.0  # 5 minutes


@dataclass(frozen=True)
class BasicAuth:
    user: str
    password: str
    source: Path


def _random_password() -> str:
    return secrets.token_urlsafe(24).rstrip("=")


def _parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _write_env_file(path: Path, user: str, password: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# POCKET access — do not commit or share\n"
        f"{AUTH_USER_ENV}={user}\n"
        f"{AUTH_PASS_ENV}={password}\n",
        encoding="utf-8",
    )
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


def load_basic_auth() -> BasicAuth:
    user = (os.environ.get(AUTH_USER_ENV) or DEFAULT_USER).strip() or DEFAULT_USER
    password = (os.environ.get(AUTH_PASS_ENV) or "").strip()
    source = AUTH_FILE

    # Load from home, then repo
    for candidate in (HOME_AUTH / "access.env", REPO_AUTH / "access.env"):
        if password:
            break
        if candidate.exists():
            try:
                data = _parse_env_file(candidate)
                user = (data.get(AUTH_USER_ENV) or user).strip() or DEFAULT_USER
                password = (data.get(AUTH_PASS_ENV) or "").strip()
                if password:
                    source = candidate
            except Exception:
                pass

    created = False
    if not password:
        password = _random_password()
        created = True
        source = AUTH_FILE
        _write_env_file(AUTH_FILE, user, password)
        # mirror to repo .pocket for discoverability
        try:
            _write_env_file(REPO_AUTH / "access.env", user, password)
        except Exception:
            pass

    os.environ[AUTH_USER_ENV] = user
    os.environ[AUTH_PASS_ENV] = password

    if created or not ACCESS_NOTE.exists():
        try:
            ACCESS_NOTE.parent.mkdir(parents=True, exist_ok=True)
            ACCESS_NOTE.write_text(
                "POCKET ACCESS (required on phone / public URL)\n"
                "================================================\n"
                f"Username: {user}\n"
                f"Password: {password}\n"
                "\n"
                "Phone: open https://pocket.medinatechlabs.net/\n"
                "Browser will prompt for login, or use the in-app password field.\n"
                "\n"
                f"Stored in: {source}\n"
                "Do not post this password publicly.\n"
                "================================================\n",
                encoding="utf-8",
            )
        except Exception:
            pass

    return BasicAuth(user=user, password=password, source=source)


_AUTH = load_basic_auth()


def reload_auth() -> BasicAuth:
    global _AUTH
    _AUTH = load_basic_auth()
    return _AUTH


def auth_summary() -> dict:
    return {
        "enabled": True,
        "user": _AUTH.user,
        "file": str(_AUTH.source),
        "note_file": str(ACCESS_NOTE),
        "public_paths": list(PUBLIC_PATHS),
        "hint": "Send Authorization: Basic … or header X-Pocket-Access: <password>",
    }


def expected_user() -> str:
    return _AUTH.user


def expected_password() -> str:
    return _AUTH.password


def path_is_public(path: str) -> bool:
    raw = (path or "/").split("?")[0] or "/"
    p = raw.rstrip("/") or "/"
    if p in PUBLIC_PATHS:
        return True
    # Keep trailing slash form for prefix checks
    check = raw if raw.startswith("/") else f"/{raw}"
    for pref in PUBLIC_PREFIXES:
        if check.startswith(pref):
            return True
    return False


def _client_ip(headers: Mapping[str, str], client_address: Optional[Tuple] = None) -> str:
    # Prefer CF / proxy headers only for rate-limit keying (not trust for auth)
    xff = headers.get("CF-Connecting-IP") or headers.get("cf-connecting-ip")
    if xff:
        return xff.strip()
    xff2 = headers.get("X-Forwarded-For") or headers.get("x-forwarded-for")
    if xff2:
        return xff2.split(",")[0].strip()
    if client_address:
        return str(client_address[0])
    return "unknown"


def is_rate_limited(ip: str) -> bool:
    now = time.time()
    with _fail_lock:
        hits = [t for t in _fail_log.get(ip, []) if now - t < FAIL_WINDOW]
        _fail_log[ip] = hits
        return len(hits) >= MAX_FAILS


def record_auth_failure(ip: str) -> None:
    with _fail_lock:
        _fail_log[ip].append(time.time())


def clear_auth_failures(ip: str) -> None:
    with _fail_lock:
        _fail_log.pop(ip, None)


def is_authorized(headers: Mapping[str, str]) -> bool:
    # Multi-user session token first (X-Pocket-Token or Bearer that is not an API key)
    sess = headers.get("X-Pocket-Token") or headers.get("x-pocket-token") or ""
    if not sess:
        try:
            from pocket.api_keys import extract_bearer

            raw = extract_bearer(headers) or ""
            # session tokens are opaque; API keys use sk_pocket_ prefix
            if raw and not raw.startswith("sk_pocket_"):
                sess = raw
        except Exception:
            pass
    if sess:
        try:
            from pocket.users import user_from_token

            if user_from_token(sess.strip()):
                return True
        except Exception:
            pass

    # Sellable AI API keys (Bearer sk_pocket_… or X-API-Key)
    try:
        from pocket.api_keys import extract_bearer, verify_key

        raw_key = extract_bearer(headers)
        if raw_key and raw_key.startswith("sk_pocket_") and verify_key(raw_key):
            return True
    except Exception:
        pass

    candidate = headers.get("Authorization") or headers.get("authorization") or ""
    if candidate.startswith("Basic "):
        try:
            raw = base64.b64decode(candidate[6:].strip()).decode("utf-8")
            user, password = raw.split(":", 1)
        except Exception:
            return False
        # multi-user table OR legacy single password
        try:
            from pocket.users import verify

            if verify(user, password):
                return True
        except Exception:
            pass
        return hmac.compare_digest(user, _AUTH.user) and hmac.compare_digest(
            password, _AUTH.password
        )

    token = headers.get("X-Pocket-Access") or headers.get("x-pocket-access") or ""
    if token:
        if hmac.compare_digest(token.strip(), _AUTH.password):
            return True
        # treat access header as session token fallback
        try:
            from pocket.users import user_from_token

            if user_from_token(token.strip()):
                return True
        except Exception:
            pass

    return False


def current_user(headers: Mapping[str, str]) -> Optional[dict]:
    """Return logged-in user record if any."""
    sess = headers.get("X-Pocket-Token") or headers.get("x-pocket-token") or ""
    if sess:
        try:
            from pocket.users import user_from_token

            u = user_from_token(sess.strip())
            if u:
                return u
        except Exception:
            pass
    candidate = headers.get("Authorization") or headers.get("authorization") or ""
    if candidate.startswith("Basic "):
        try:
            raw = base64.b64decode(candidate[6:].strip()).decode("utf-8")
            user, password = raw.split(":", 1)
            from pocket.users import verify

            return verify(user, password)
        except Exception:
            return {"user": _AUTH.user, "role": "admin", "display": "Operator"}
    return None


def security_headers() -> list[tuple[str, str]]:
    return [
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "DENY"),
        ("Referrer-Policy", "no-referrer"),
        ("Cache-Control", "no-store"),
        # CSP for the app UI
        (
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
            "script-src 'self' 'unsafe-inline'; connect-src 'self'; "
            "media-src 'self'; frame-ancestors 'none'",
        ),
        # mic allowed for voice-to-text in desk UI
        ("Permissions-Policy", "camera=(), microphone=(self), geolocation=()"),
    ]
