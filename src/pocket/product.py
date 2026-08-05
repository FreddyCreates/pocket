"""POCKET product catalog — features that actually ship (not scaffold claims)."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Any, Dict, List

VERSION = "2.0.1-alpha"
PRODUCT_NAME = "POCKET"
PRODUCT_LINE = "Desktop (host) + Cloud API · Fusion Sense · RFE · agents · NEXUS"


def feature_matrix() -> List[Dict[str, Any]]:
    """Every feature with status and how to use it."""
    return [
        {
            "id": "auth",
            "name": "Secure sign-in",
            "status": "product",
            "use": "Login / register with invite",
            "api": ["POST /v1/auth/login", "POST /v1/auth/register"],
        },
        {
            "id": "codex",
            "name": "Codex coding agent",
            "status": "product",
            "use": "Session → Codex → task",
            "requires": "codex CLI on PATH",
        },
        {
            "id": "grok",
            "name": "Grok coding agent",
            "status": "product",
            "use": "Session → Grok → task",
            "requires": "grok CLI (~/.grok/bin)",
        },
        {
            "id": "plan",
            "name": "Planning AI chat",
            "status": "product",
            "use": "Session → Plan → plan-only prompt",
        },
        {
            "id": "desktop",
            "name": "Desktop app control",
            "status": "product",
            "use": "open notepad | open edge https://… | list apps",
            "apps": 14,
        },
        {
            "id": "web",
            "name": "Web research",
            "status": "product",
            "use": "search / fetch / research",
        },
        {
            "id": "nexus",
            "name": "NEXUS intelligence",
            "status": "product",
            "use": "Session → NEXUS · MERIDIAN workers · Bridge catalog",
            "api": ["GET /v1/nexus", "POST /v1/nexus/run", "GET /v1/stack"],
            "monetize": "POCK / NEXUS credits per tool call",
        },
        {
            "id": "mesie",
            "name": "MESIE spectral / colony compute",
            "status": "product",
            "use": "Session → MESIE · engines · CloudColony real",
            "api": ["GET /v1/mesie", "GET /v1/stack"],
            "root_hint": "MESIE_ROOT or ~/Multi-Element-Spectral-Intelligence-Engine-MESIE-",
        },
        {
            "id": "fusion_rfe",
            "name": "Fusion Sense + RFE-v1",
            "status": "product",
            "use": "Full page symbols → signed packet → HTML/3D/GLSL",
            "api": ["GET /v1/vision/page", "POST /v1/rfe/synthesize"],
        },
        {
            "id": "subagent_mesh",
            "name": "Subagent Mesh Protocol (MEDINA-SUBAGENT-MESH/1.0)",
            "status": "product",
            "use": "Always-use hook: E: virtual disk, @dispatch, design+headless packs, encrypted mesh mail",
            "api": [
                "GET /v1/protocols/mesh",
                "POST /v1/hooks/mesh",
                "POST /v1/subagents/dispatch",
                "GET /v1/mesh",
            ],
            "protocol": "MEDINA-SUBAGENT-MESH/1.0",
            "research": "docs/research/POCKET_SUBAGENT_MESH_CLOUDCOLONY_PROTOCOL.md",
        },
        {
            "id": "vcomp",
            "name": "Virtual computer + missions",
            "status": "product",
            "use": "Workspace, terminals, multi-hour queue",
            "api": ["POST /v1/vcomp/open", "POST /v1/missions/start"],
        },
        {
            "id": "product_studio",
            "name": "Product phone/web remake",
            "status": "product",
            "use": "Lifelike iPhone + web stages (not desktop crop)",
            "api": ["POST /v1/studio/product_phone", "POST /v1/studio/product_web"],
        },
        {
            "id": "video_watch",
            "name": "Video watch for agents",
            "status": "product",
            "use": "YouTube meta + frame OCR from local/download",
            "api": ["POST /v1/video/watch"],
        },
        {
            "id": "tour",
            "name": "Product tour",
            "status": "product",
            "use": "High-end presentation at /tour",
            "api": ["GET /tour", "GET /v1/product/presentation"],
        },
        {
            "id": "term",
            "name": "Live terminal",
            "status": "product",
            "use": "Session → Terminal → interactive commands",
        },
        {
            "id": "deploy",
            "name": "Local deploys",
            "status": "product",
            "use": "Static / npm / python + logs",
        },
        {
            "id": "upload",
            "name": "File & zip upload",
            "status": "product",
            "use": "+ Upload into workspace/uploads",
        },
        {
            "id": "stream",
            "name": "Live token/stream",
            "status": "product",
            "use": "Poll session while jobs run",
        },
        {
            "id": "phone",
            "name": "Remote phone desk",
            "status": "product",
            "use": "https://pocket.medinatechlabs.net/",
        },
        {
            "id": "safety",
            "name": "Safety layer",
            "status": "product",
            "use": "Auth, allowlists, audit log, rate limits",
        },
        {
            "id": "credits",
            "name": "POCK / NEXUS metering",
            "status": "product",
            "use": "Burn on jobs; refill = subscription hook",
        },
        {
            "id": "headless_agents",
            "name": "Headless agent fleet",
            "status": "product",
            "use": "15 agents: researcher, planner, coder, squad, security…",
            "api": ["GET /v1/ai/agents", "POST /v1/ai/agents/{id}/run"],
        },
        {
            "id": "ai_api",
            "name": "POCKET AI API (sellable)",
            "status": "product",
            "use": "API keys + chat + jobs + metering for third parties",
            "api": [
                "GET /v1/ai",
                "POST /v1/ai/chat",
                "POST /v1/ai/keys",
                "POST /v1/ai/jobs",
            ],
            "sell": {"starter_usd": 29, "pro_usd": 99, "enterprise_usd": 299},
        },
    ]


def doctor() -> Dict[str, Any]:
    """Product readiness report."""
    from pocket.auth import ACCESS_NOTE, expected_user
    from pocket.nexus_bridge import nexus_available
    from pocket.safety import policy_summary

    checks = []

    def add(name: str, ok: bool, detail: str = ""):
        checks.append({"name": name, "ok": ok, "detail": detail})

    py = os.environ.get("POCKET_PYTHON") or shutil.which("python") or ""
    add("python", bool(py), py)
    add("codex_cli", bool(shutil.which("codex")), shutil.which("codex") or "missing")
    g = shutil.which("grok") or ""
    if not g:
        gp = Path.home() / ".grok" / "bin" / "grok.exe"
        g = str(gp) if gp.exists() else ""
    add("grok_cli", bool(g), g or "missing")
    add("access_file", ACCESS_NOTE.exists(), str(ACCESS_NOTE))
    nx = nexus_available()
    add("nexus", bool(nx.get("ok")), nx.get("root") or "")
    add("cloudflared", bool(shutil.which("cloudflared") or Path(r"C:\Program Files (x86)\cloudflared\cloudflared.exe").exists()), "service or CLI")
    pub = (os.environ.get("POCKET_PUBLIC_URL") or "").strip()
    add("public_url_env", pub.startswith("http"), pub or "unset")

    ok_n = sum(1 for c in checks if c["ok"])
    return {
        "ok": ok_n >= 4,
        "product": PRODUCT_NAME,
        "version": VERSION,
        "line": PRODUCT_LINE,
        "ready_score": f"{ok_n}/{len(checks)}",
        "checks": checks,
        "features": feature_matrix(),
        "safety": policy_summary(),
        "auth_user": expected_user(),
        "start": "python -m pocket runtime   OR   Start-POCKET.ps1",
        "phone": pub or "https://pocket.medinatechlabs.net/",
    }
