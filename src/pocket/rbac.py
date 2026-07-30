"""Founder POCKET vs Market POCKET.

  founder (admin / is_owner / legacy ACCESS)
    → full local on this machine + virtual + host embodiment
  market seat (member)
    → their local sandbox + virtual under tenants/<user>
    → NEVER founder files, never host shell/desktop of the operator PC

Invites are marketing + seat mint. Invite ≠ browse founder disk.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Set

# Market modes: agents + local/virtual space work on THEIR sandbox
MEMBER_MODES: Set[str] = {
    "plan",
    "web",
    "ask",
    "handoff",
    "grok",
    "codex",
    "claude",
    "nexus",
    "agent",
    "doer",
    "guppy",
    "repos",
    "copilot",
    "archon",
    "alpha",
    "workers",
    "git",
    "forge",
    "sovereign-git",
    "ghost",
    "ghost-math",
    "math",
    "mesie",
    "auro",
    "woa",
    "wrapped-orch",
    "wrapped_orch",
    "cowork",
    "work",
    "demo",
}

# Operator-machine control — founder edition only on THIS host
FOUNDER_HOST_MODES: Set[str] = {
    "shell",
    "wsl",
    "term",
    "desktop",
    "browser",
    "capture",
    "offload",
    "embody",
    "embodiment",
    "realworld",
}

ADMIN_ONLY_MODES: Set[str] = set(FOUNDER_HOST_MODES)
HOST_PC_MODES = FOUNDER_HOST_MODES  # alias for older imports

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
    "repos",
    "copilot_intro",
}

ADMIN_ONLY_AGENTS: Set[str] = {
    "ops",
    "desktop_bot",
    "browser",
    "capture",
}

ADMIN_ONLY_PATH_PREFIXES = (
    "/v1/tokenomics/mint",
    "/v1/deploy",
    "/v1/terminals",
    "/v1/desktop",
)

FOUNDER_ONLY_PATH_PREFIXES = (
    "/v1/desktop",
    "/v1/terminals",
    "/v1/deploy",
    "/v1/embodiment",
    "/v1/capture",
    "/v1/screen",
    "/v1/offload",
)


def is_admin(user: Optional[Dict[str, Any]]) -> bool:
    if not user:
        return False
    return (user.get("role") or "").lower() == "admin"


def is_founder(user: Optional[Dict[str, Any]]) -> bool:
    """True for operator of THIS host install (your POCKET)."""
    if not user:
        return False
    if user.get("is_owner"):
        return True
    if is_admin(user):
        return True
    if user.get("principal") == "legacy":
        return True
    if (user.get("edition") or "").lower() == "founder":
        return True
    return False


# Back-compat name used by server patches
def is_host_power(user: Optional[Dict[str, Any]]) -> bool:
    return is_founder(user)


def principal(headers) -> Dict[str, Any]:
    try:
        from pocket.auth import current_user

        u = current_user(headers)
        if u:
            edition = "founder" if (u.get("is_owner") or (u.get("role") or "") == "admin") else "market"
            return {**u, "principal": "user", "edition": edition}
    except Exception:
        pass
    try:
        from pocket.api_keys import extract_bearer, verify_key

        raw = extract_bearer(headers)
        if raw:
            rec = verify_key(raw)
            if rec:
                role = "member" if (rec.get("tier") or "") != "enterprise" else "admin"
                return {
                    "user": rec.get("owner") or "api",
                    "role": role,
                    "display": rec.get("name") or "API",
                    "principal": "api_key",
                    "api_key_id": rec.get("id"),
                    "tier": rec.get("tier"),
                    "key": rec,
                    "edition": "founder" if role == "admin" else "market",
                }
    except Exception:
        pass
    try:
        from pocket.auth import expected_password

        tok = headers.get("X-Pocket-Access") or headers.get("x-pocket-access") or ""
        if tok and tok.strip() == expected_password():
            return {
                "user": "pocket",
                "role": "admin",
                "display": "Operator",
                "principal": "legacy",
                "is_owner": True,
                "edition": "founder",
            }
    except Exception:
        pass
    return {
        "user": "anonymous",
        "role": "none",
        "display": "",
        "principal": "none",
        "edition": "none",
    }


def allow_mode(user: Optional[Dict[str, Any]], mode: str) -> tuple[bool, str]:
    mode = (mode or "").lower()
    if is_founder(user):
        return True, "ok"
    if mode in FOUNDER_HOST_MODES:
        return (
            False,
            f"mode '{mode}' is founder-host control on the operator machine. "
            "Market POCKET uses your own local sandbox + virtual files — never founder disk.",
        )
    if mode in MEMBER_MODES or mode in ("plan", "web"):
        return True, "ok"
    return False, f"mode '{mode}' not allowed for market seats"


def allow_agent(user: Optional[Dict[str, Any]], agent_id: str) -> tuple[bool, str]:
    aid = (agent_id or "").lower()
    if is_founder(user):
        return True, "ok"
    if aid in ADMIN_ONLY_AGENTS:
        return False, f"agent '{aid}' is founder-host only"
    if aid in MEMBER_AGENTS:
        return True, "ok"
    return False, f"agent '{aid}' not allowed"


def allow_admin_action(user: Optional[Dict[str, Any]], action: str) -> tuple[bool, str]:
    if is_founder(user):
        return True, "ok"
    return False, f"'{action}' requires founder/admin on this host"


def can_access_owned(user: Optional[Dict[str, Any]], owner: str) -> bool:
    if not user:
        return False
    if is_founder(user):
        return True
    return (user.get("user") or "").lower() == (owner or "").lower()


def allow_host_path(user: Optional[Dict[str, Any]], path: str) -> tuple[bool, str]:
    if is_founder(user):
        return True, "ok"
    p = path or ""
    for pref in FOUNDER_ONLY_PATH_PREFIXES:
        if p == pref or p.startswith(pref + "/"):
            return (
                False,
                "Founder-host APIs only. Market seats use /v1/space (your local + virtual).",
            )
    return True, "ok"
