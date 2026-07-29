"""Role-based access for production multi-user seats.

Roles:
  admin  — operator: full host power, mint, keys for others, all sessions
  member — invite seat: own sessions, limited modes, own API keys only
  api    — API key principal (not a human role; used for scoping)
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Set

# Modes members may use from the desk (no raw host shell by default)
MEMBER_MODES: Set[str] = {
    "plan",
    "web",
    "ask",
    "handoff",
    "grok",
    "codex",
    "claude",
    "nexus",
    "desktop",  # still allowlisted apps only
    "agent",  # headless multi-step doer
    "doer",
    "guppy",  # local commercial fish agent
    "browser",  # real-world Edge/X/Copilot + Codex/Grok
    "capture",
    "repos",
    "copilot",
    "archon",
    "alpha",
    "workers",
}

# Modes that require admin (host RCE surface)
ADMIN_ONLY_MODES: Set[str] = {"shell", "wsl", "term"}

# API / agent ids members may call (no ops/shell host control via API)
MEMBER_AGENTS: Set[str] = {
    "router",
    "scout",
    "researcher",
    "planner",
    "writer",
    "data",
    "reviewer",
    "architect",
    "coder",
    "grok_coder",
    "security",
    "nexus_bridge",
    "squad",
    "doer",
    "guppy",
    "browser",
    "capture",
    "repos",
    "copilot_intro",
}

ADMIN_ONLY_AGENTS: Set[str] = {"ops", "desktop_bot"}

ADMIN_ONLY_PATH_PREFIXES = (
    "/v1/tokenomics/mint",
    "/v1/deploy",
    "/v1/terminals",
)


def is_admin(user: Optional[Dict[str, Any]]) -> bool:
    if not user:
        return False
    return (user.get("role") or "").lower() == "admin"


def principal(headers) -> Dict[str, Any]:
    """Resolve human user or API key principal."""
    try:
        from pocket.auth import current_user

        u = current_user(headers)
        if u:
            return {**u, "principal": "user"}
    except Exception:
        pass
    try:
        from pocket.api_keys import extract_bearer, verify_key

        raw = extract_bearer(headers)
        if raw:
            rec = verify_key(raw)
            if rec:
                return {
                    "user": rec.get("owner") or "api",
                    "role": "member" if (rec.get("tier") or "") != "enterprise" else "admin",
                    "display": rec.get("name") or "API",
                    "principal": "api_key",
                    "api_key_id": rec.get("id"),
                    "tier": rec.get("tier"),
                    "key": rec,
                }
    except Exception:
        pass
    # Legacy single-password access → treat as admin operator
    try:
        from pocket.auth import expected_password

        tok = headers.get("X-Pocket-Access") or headers.get("x-pocket-access") or ""
        if tok and tok.strip() == expected_password():
            return {"user": "pocket", "role": "admin", "display": "Operator", "principal": "legacy"}
    except Exception:
        pass
    return {"user": "anonymous", "role": "none", "display": "", "principal": "none"}


def allow_mode(user: Optional[Dict[str, Any]], mode: str) -> tuple[bool, str]:
    mode = (mode or "").lower()
    if is_admin(user) or (user or {}).get("principal") == "legacy":
        return True, "ok"
    if mode in ADMIN_ONLY_MODES:
        return False, f"mode '{mode}' requires admin (host shell surface)"
    if mode in MEMBER_MODES or mode in ("plan", "web"):
        return True, "ok"
    return False, f"mode '{mode}' not allowed for your role"


def allow_agent(user: Optional[Dict[str, Any]], agent_id: str) -> tuple[bool, str]:
    aid = (agent_id or "").lower()
    if is_admin(user) or (user or {}).get("principal") == "legacy":
        return True, "ok"
    if aid in ADMIN_ONLY_AGENTS:
        return False, f"agent '{aid}' requires admin"
    if aid in MEMBER_AGENTS:
        return True, "ok"
    return False, f"agent '{aid}' not allowed"


def allow_admin_action(user: Optional[Dict[str, Any]], action: str) -> tuple[bool, str]:
    if is_admin(user) or (user or {}).get("principal") == "legacy":
        return True, "ok"
    return False, f"'{action}' requires admin role"


def can_access_owned(user: Optional[Dict[str, Any]], owner: str) -> bool:
    if not user:
        return False
    if is_admin(user) or user.get("principal") == "legacy":
        return True
    return (user.get("user") or "").lower() == (owner or "").lower()
