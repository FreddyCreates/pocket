"""How POCKET is sold and used — Desktop (host) vs Cloud API.

This is the product packaging for *you* (founder) and for users.
Research papers specify engines. Channels specify how humans buy and open them.
"""

from __future__ import annotations

from typing import Any, Dict, List

from pocket import __version__, PRODUCT, LAB


def channels() -> Dict[str, Any]:
    """Canonical product channels — single source of truth."""
    return {
        "ok": True,
        "product": PRODUCT,
        "version": __version__,
        "lab": LAB,
        "decision": {
            "for_you_now": "Desktop is primary (Fusion Sense needs the host). Cloud API is the sellable remote surface.",
            "for_users": [
                "Desktop app on the operator PC — sees screen, clicks, records, remakes",
                "Cloud/API — Grok, Codex, Claude, phone, integrations hit the same host via tunnel + keys",
            ],
            "not": "A research landing page is not the product. The desk + API + desktop window are.",
        },
        "channels": [
            {
                "id": "desktop",
                "name": "POCKET Desktop",
                "who": "You (operator) and power users on a Windows host",
                "what": "Electron / native window over local runtime. Full Fusion Sense, RFE, record, studio, agents, NEXUS.",
                "how_start": [
                    "Download Windows .exe from /download (portable or NSIS installer)",
                    "Start-POCKET-Desktop.ps1",
                    "python -m pocket desktop",
                    "Desktop shortcut: POCKET Desktop",
                ],
                "url": "http://127.0.0.1:8787/",
                "download": {
                    "page": "/download",
                    "windows": "/download/desktop",
                    "catalog": "/v1/desktop/releases",
                },
                "engines": [
                    "perception / page_renderer",
                    "rfe_kernel",
                    "virtual_computer",
                    "missions",
                    "device_remake / video_studio",
                    "orchestrator + agents",
                    "nexus_bridge",
                ],
                "status": "shipping",
            },
            {
                "id": "web_edge",
                "name": "POCKET Web edge desk",
                "who": "Anyone with browser access to the host or tunnel",
                "what": "Most stable product surface — same desk UI the Electron shell packages. Prefer this when packaging is unavailable.",
                "how_start": [
                    "Open http://127.0.0.1:8787/desk",
                    "Public: https://pocket.medinatechlabs.net/desk (tunnel when up)",
                ],
                "url": "http://127.0.0.1:8787/desk",
                "url_public_hint": "https://pocket.medinatechlabs.net/desk",
                "status": "shipping",
            },
            {
                "id": "api",
                "name": "POCKET Cloud API",
                "who": "Grok Build, Codex, Claude, phone, external apps",
                "what": "Same host engines via HTTP. Auth keys. Cloudflare tunnel optional for public URL.",
                "how_start": [
                    "Runtime always-on (Start-POCKET.ps1 / AlwaysOn)",
                    "GET /v1/api catalog",
                    "Bearer sk_pocket_… or Basic / X-Pocket-Access",
                    "scripts/pocket-api.ps1",
                ],
                "url_local": "http://127.0.0.1:8787/v1/api",
                "url_public_hint": "https://pocket.medinatechlabs.net/ (tunnel when configured)",
                "docs": ["docs/AI_API.md", "docs/PLATFORM_V8.md"],
                "status": "shipping",
            },
            {
                "id": "phone",
                "name": "POCKET Phone (remote desk)",
                "who": "You on mobile, same Wi‑Fi or public tunnel",
                "what": "Responsive desk UI against the host API — not a separate product brain",
                "how_start": ["Open public URL or LAN :8787", "Sign in with ACCESS.txt"],
                "status": "shipping",
            },
        ],
        "presentation_for_users": {
            "primary": "Web edge desk (stable) + downloadable Windows Electron .exe from /download",
            "secondary": "API keys for other AIs and automation",
            "avoid": "Leading with research journals or manifesto landing pages as the app",
            "demo_path": "Web desk → Download .exe → open local shell → Fusion Sense workflow",
        },
        "api": {
            "channels": "GET /v1/product/channels",
            "catalog": "GET /v1/api",
            "health": "GET /health",
            "desktop_releases": "GET /v1/desktop/releases",
            "download_page": "GET /download",
            "download_windows": "GET /download/desktop",
        },
    }


def user_home_brief() -> Dict[str, Any]:
    """Short home card for the desk UI / desktop shell."""
    ch = channels()
    return {
        "ok": True,
        "headline": "POCKET Desktop + API",
        "for_you": ch["decision"]["for_you_now"],
        "open": {
            "desk": "/",
            "studio": "/studio",
            "api": "/v1/api",
            "channels": "/v1/product/channels",
        },
        "engines_ok": True,
        "version": __version__,
    }
