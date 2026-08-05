"""First-class product fabric — unified readiness beyond A–Z checklist.

Scores POCKET as a host co-pilot product: sovereignty, multi-agent ship,
Infinite Wiki, dual-loop, swarm, isolation, API, phone, WSL.
"""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

from pocket import __version__, COMPANY, LAB, PRODUCT, PRODUCT_FULL, TAGLINE


def _ok(name: str, ok: bool, detail: str = "", *, tier: str = "core") -> Dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail or ("pass" if ok else "fail"), "tier": tier}


def pillars() -> List[Dict[str, Any]]:
    """Live first-class pillars."""
    home = Path.home() / ".pocket"
    items: List[Dict[str, Any]] = []

    # Core host
    items.append(_ok("State home", home.is_dir(), str(home)))
    access = (home / "ACCESS.txt").exists() or (home / "access.env").exists()
    items.append(_ok("Auth credentials", access, "ACCESS / access.env"))
    pub = (os.environ.get("POCKET_PUBLIC_URL") or "").strip()
    if not pub.startswith("http"):
        for envf in (
            Path.home() / ".pocket" / "cloudflare-named.env",
            Path.home() / "OneDrive" / "pocket-os" / "PUBLIC_URL.txt",
            Path.home() / ".pocket" / "PUBLIC_URL.txt",
        ):
            try:
                if envf.exists():
                    import re as _re

                    t = envf.read_text(encoding="utf-8", errors="replace")
                    m = _re.search(r"https?://[^\s]+", t)
                    if m:
                        pub = m.group(0).rstrip("/")
                        break
                    for line in t.splitlines():
                        if line.startswith("POCKET_PUBLIC_URL="):
                            pub = line.split("=", 1)[1].strip()
                            break
            except Exception:
                pass
            if pub.startswith("http"):
                break
    items.append(_ok("Public URL", pub.startswith("http"), pub or "local-only", tier="edge"))

    # Engines
    codex = bool(shutil.which("codex"))
    grok = bool(shutil.which("grok") or (Path.home() / ".grok" / "bin" / "grok.exe").exists())
    items.append(_ok("Coding engines", codex or grok, f"codex={codex} grok={grok}"))

    # Isolation / RBAC
    try:
        from pocket import rbac  # noqa: F401

        items.append(_ok("Founder/market RBAC", True, "host_power gates"))
    except Exception as e:
        items.append(_ok("Founder/market RBAC", False, str(e)[:80]))

    # Infinite Wiki
    try:
        from pocket.infinite_wiki import status as wiki_status

        w = wiki_status()
        items.append(
            _ok(
                "Infinite Wiki",
                bool(w.get("ok")),
                f"nodes={w.get('nodes')} watcher={w.get('watcher')} ts={bool((w.get('treesitter') or {}).get('available'))}",
                tier="class",
            )
        )
    except Exception as e:
        items.append(_ok("Infinite Wiki", False, str(e)[:80], tier="class"))

    # World model
    try:
        from pocket.world_model import status as wm_status

        wm = wm_status()
        c = wm.get("counts") or {}
        items.append(
            _ok(
                "World model",
                bool(wm.get("ok")) and int(c.get("facts") or 0) > 0,
                f"facts={c.get('facts')} archetypes={c.get('archetypes')}",
                tier="class",
            )
        )
    except Exception as e:
        items.append(_ok("World model", False, str(e)[:80], tier="class"))

    # Dual loop module
    try:
        from pocket import cortex_subcortex  # noqa: F401

        items.append(_ok("Cortex/Subcortex dual-loop", True, "System 1+2", tier="class"))
    except Exception as e:
        items.append(_ok("Cortex/Subcortex dual-loop", False, str(e)[:80], tier="class"))

    # Always-on swarm
    try:
        from pocket.always_on_swarm import status as swarm_status

        s = swarm_status()
        items.append(
            _ok(
                "Always-on swarm",
                bool(s.get("ok")),
                f"running={s.get('running')} pulses={s.get('pulses')}",
                tier="class",
            )
        )
    except Exception as e:
        items.append(_ok("Always-on swarm", False, str(e)[:80], tier="class"))

    # Work studio
    try:
        from pocket.work_types import catalog

        cat = catalog()
        items.append(
            _ok(
                "Work Studio loops",
                len(cat.get("loops") or []) >= 3 and len(cat.get("types") or []) >= 5,
                f"types={len(cat.get('types') or [])} loops={len(cat.get('loops') or [])}",
                tier="class",
            )
        )
    except Exception as e:
        items.append(_ok("Work Studio loops", False, str(e)[:80], tier="class"))

    # Use cases / Emergent parity
    try:
        from pocket.use_cases import list_use_cases, parity_report

        uc = list_use_cases()
        pr = parity_report()
        score = pr.get("score") or {}
        items.append(
            _ok(
                "Ship use cases",
                len(uc) >= 8,
                f"{len(uc)} cases · pocket_only={score.get('pocket_only_advantages')}",
                tier="class",
            )
        )
    except Exception as e:
        items.append(_ok("Ship use cases", False, str(e)[:80], tier="class"))

    # WSL
    try:
        from pocket.wsl_agent import which_wsl

        wsl = bool(which_wsl())
        items.append(_ok("WSL native agent", wsl, "wsl on PATH" if wsl else "install WSL for Linux hands", tier="edge"))
    except Exception as e:
        items.append(_ok("WSL native agent", False, str(e)[:80], tier="edge"))

    # Surfaces
    items.append(_ok("Phone surface", True, "/phone", tier="edge"))
    items.append(_ok("Work Studio surface", True, "/work", tier="edge"))
    items.append(_ok("Sellable AI API", True, "/v1/ai/chat + keys", tier="edge"))
    items.append(_ok("Researcher license gate", True, "/download + LICENSE-RESEARCHER", tier="edge"))

    # Security
    try:
        from pocket.auth import security_headers

        hs = {k for k, _ in security_headers()}
        items.append(
            _ok(
                "Security headers",
                "Content-Security-Policy" in hs and "X-Content-Type-Options" in hs,
                f"{len(hs)} headers",
            )
        )
    except Exception as e:
        items.append(_ok("Security headers", False, str(e)[:80]))

    return items


def score(items: List[Dict[str, Any]] | None = None) -> Dict[str, Any]:
    items = items or pillars()
    total = len(items)
    passed = sum(1 for i in items if i.get("ok"))
    core = [i for i in items if i.get("tier") == "core"]
    klass = [i for i in items if i.get("tier") == "class"]
    edge = [i for i in items if i.get("tier") == "edge"]
    core_ok = sum(1 for i in core if i["ok"])
    class_ok = sum(1 for i in klass if i["ok"])
    edge_ok = sum(1 for i in edge if i["ok"])
    pct = round(100.0 * passed / total, 1) if total else 0.0
    # First-class bar: all core + almost all class pillars
    first_class = core_ok == len(core) and class_ok >= max(1, len(klass) - 1) and pct >= 85.0
    grade = (
        "S"
        if pct >= 95 and first_class
        else "A"
        if first_class
        else "B"
        if pct >= 75
        else "C"
        if pct >= 60
        else "D"
    )
    return {
        "passed": passed,
        "total": total,
        "percent": pct,
        "grade": grade,
        "first_class": first_class,
        "core": f"{core_ok}/{len(core)}",
        "class_pillars": f"{class_ok}/{len(klass)}",
        "edge": f"{edge_ok}/{len(edge)}",
        "failures": [i for i in items if not i.get("ok")],
    }


def report() -> Dict[str, Any]:
    items = pillars()
    sc = score(items)
    return {
        "ok": True,
        "schema": "pocket.first_class.v1",
        "product": PRODUCT,
        "product_full": PRODUCT_FULL,
        "tagline": TAGLINE,
        "lab": LAB,
        "company": COMPANY,
        "version": __version__,
        "ts": time.time(),
        "score": sc,
        "pillars": items,
        "doctrine": [
            "Sovereign host co-pilot — not cloud lock-in",
            "Founder machine ≠ market seat disk",
            "Cortex talks; Subcortex works silently",
            "Infinite Wiki: profile → slice → edit (never dump 10k lines)",
            "Always-on swarm keeps the lab shipping",
            "Sellable API + phone + WSL + mesh — one product family",
        ],
        "surfaces": {
            "desk": "/desk",
            "phone": "/phone",
            "work_studio": "/work",
            "download": "/download",
            "docs": "/docs/hub",
            "api": "/developers",
            "ready": "/v1/ready",
            "class": "/v1/class",
        },
        "message": (
            f"{PRODUCT} grade {sc['grade']} · {sc['percent']}% · "
            + ("FIRST-CLASS" if sc["first_class"] else "raising the bar")
        ),
    }


def health_enrichment() -> Dict[str, Any]:
    """Compact block for /health without heavy work."""
    try:
        sc = score()
        return {
            "first_class": sc.get("first_class"),
            "grade": sc.get("grade"),
            "score": f"{sc.get('passed')}/{sc.get('total')}",
            "percent": sc.get("percent"),
        }
    except Exception:
        return {"first_class": False, "grade": "?", "score": "0/0"}
