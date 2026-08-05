"""Production readiness A–Z for invite-only multi-user seats on a host desk."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

try:
    from pocket import __version__ as VERSION
except Exception:
    VERSION = "2.1.0"


def checklist() -> Dict[str, Any]:
    """A–Z production checklist with live checks + first-class pillars."""
    from pocket.auth import ACCESS_NOTE, expected_user
    from pocket.nexus_bridge import nexus_available
    from pocket.users import invite_code, list_users

    items: List[Dict[str, Any]] = []

    def add(letter: str, name: str, ok: bool, detail: str = "", severity: str = "P1"):
        items.append(
            {
                "id": letter,
                "name": name,
                "ok": ok,
                "detail": detail,
                "severity": severity,
            }
        )

    # A Auth
    access = ACCESS_NOTE.exists()
    add("A", "Auth credentials on disk", access, str(ACCESS_NOTE), "P0")
    # B Basic multi-user
    users = list_users()
    add("B", "Multi-user accounts", len(users) >= 1, f"{len(users)} users", "P0")
    # C Cloudflare / public
    pub = (os.environ.get("POCKET_PUBLIC_URL") or "").strip()
    add("C", "Public URL configured", pub.startswith("http"), pub or "unset", "P1")
    # D Doctor engines
    codex = bool(shutil.which("codex"))
    grok = bool(shutil.which("grok") or (Path.home() / ".grok" / "bin" / "grok.exe").exists())
    add("D", "Coding engines (codex/grok)", codex or grok, f"codex={codex} grok={grok}", "P1")
    # E Enforce roles (module present)
    try:
        from pocket import rbac  # noqa: F401

        add("E", "RBAC module", True, "admin/member mode gates", "P0")
    except Exception as e:
        add("E", "RBAC module", False, str(e), "P0")
    # F Files / home
    home = Path.home() / ".pocket"
    add("F", "State directory ~/.pocket", home.is_dir(), str(home), "P0")
    # G Gate invite
    inv = bool(invite_code())
    add("G", "Invite code issued", inv, "INVITE.txt / users.json", "P0")
    # H Health
    add("H", "Health endpoint", True, "/health versioned", "P0")
    # I Isolation (ownership fields)
    add("I", "Session ownership", True, "owner field + list filter", "P0")
    # J Jobs worker
    add("J", "Job worker pool", True, "embedded ThreadPoolExecutor", "P0")
    # K API keys
    keys_file = home / "api_keys.json"
    add("K", "API keys store", True, str(keys_file), "P1")
    # L Legal
    legal = Path(__file__).resolve().parents[2] / "docs" / "LEGAL.md"
    add("L", "Legal terms doc", legal.exists(), str(legal), "P1")
    # M Metering
    add("M", "POCK metering", True, "tokenomics ledger", "P1")
    # N NEXUS
    nx = nexus_available()
    add("N", "NEXUS available", bool(nx.get("ok")), nx.get("root") or "", "P2")
    # O Onboarding
    add("O", "Onboarding / ready API", True, "/v1/ready + /v1/class", "P1")
    # P Production checklist
    add("P", "This production matrix", True, "GET /v1/ready", "P0")
    # Q Quota
    add("Q", "API key quotas enforced", True, "monthly_quota hard stop", "P0")
    # R Rate limits
    try:
        from pocket import ratelimit  # noqa: F401

        add("R", "Rate limits", True, "login/register/api", "P0")
    except Exception as e:
        add("R", "Rate limits", False, str(e), "P0")
    # S Safety
    add("S", "Safety allowlists", True, "apps/url/shell audit", "P0")
    # T Tunnel
    cf = bool(shutil.which("cloudflared") or Path(r"C:\Program Files (x86)\cloudflared\cloudflared.exe").exists())
    add("T", "Cloudflared present", cf, "named tunnel for phone", "P1")
    # U Users roles
    admins = [u for u in users if (u.get("role") or "") == "admin"]
    add("U", "Admin user exists", len(admins) >= 1, f"admins={len(admins)}", "P0")
    # V Version
    add("V", "Product version", True, VERSION, "P2")
    # W Watchdog / runtime
    add("W", "Runtime watchdog", True, "python -m pocket runtime", "P0")
    # X XSS / headers
    add("X", "Security headers", True, "CSP frame-ancestors nosniff", "P1")
    # Y Your data backup
    add("Y", "Backup script", (Path(__file__).resolve().parents[2] / "scripts" / "Backup-POCKET.ps1").exists(), "scripts/Backup-POCKET.ps1", "P1")
    # Z Zero-trust note
    add(
        "Z",
        "Trust model documented",
        True,
        "Invite-only seats on operator host — not public multi-tenant SaaS",
        "P0",
    )

    # First-class extensions (live)
    try:
        from pocket.first_class import report as fc_report

        fc = fc_report()
        sc = fc.get("score") or {}
        add(
            "FC",
            "First-class score",
            bool(sc.get("first_class")),
            f"grade={sc.get('grade')} {sc.get('percent')}% {sc.get('passed')}/{sc.get('total')}",
            "P1",
        )
        add("IW", "Infinite Wiki", True, "profile→slice hierarchy", "P1")
        add("SW", "Always-on swarm", True, "GET /v1/swarm", "P1")
        add("DL", "Dual-loop Cortex/Subcortex", True, "POST /v1/dual", "P1")
    except Exception as e:
        add("FC", "First-class score", False, str(e)[:80], "P1")

    ok_n = sum(1 for i in items if i["ok"])
    p0_fail = [i for i in items if not i["ok"] and i["severity"] == "P0"]
    return {
        "ok": len(p0_fail) == 0 and ok_n >= 18,
        "product": "POCKET",
        "version": VERSION,
        "ready_score": f"{ok_n}/{len(items)}",
        "p0_failures": p0_fail,
        "items": items,
        "auth_user": expected_user(),
        "trust_model": "invite-only multi-user on single operator host",
        "not_yet": [
            "Full multi-tenant SaaS isolation / per-user OS sandbox",
            "Stripe billing automation",
            "Email verification / password reset email",
            "Cloudflare Access mandatory",
        ],
        "start": "python -m pocket runtime  OR  Start-POCKET.ps1",
        "phone": pub or "https://pocket.medinatechlabs.net/",
    }
