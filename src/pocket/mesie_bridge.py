"""MESIE product bridge inside POCKET — spectral / colony compute lane.

MESIE is the multi-element spectral engine monorepo + CloudColony compute path.
POCKET hosts the desk; MESIE supplies engines, match/embed, and colony edge.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _candidates() -> List[Path]:
    env = os.environ.get("MESIE_ROOT") or os.environ.get("POCKET_MESIE_ROOT")
    out: List[Path] = []
    if env:
        out.append(Path(env))
    home = Path.home()
    out.extend(
        [
            home / "Multi-Element-Spectral-Intelligence-Engine-MESIE-",
            Path("E:/repos/cloudcolony-sovereign"),  # wrap includes mesie/
            home / "OneDrive" / "CODING AI WORK HUB AGENTS ENTER FIRST" / "cloudcolony-sovereign",
        ]
    )
    return out


def mesie_root() -> Optional[Path]:
    for p in _candidates():
        try:
            if p.is_dir() and (
                (p / "mesie").is_dir()
                or (p / "pyproject.toml").exists()
                or (p / "mesie" / "engines").is_dir()
            ):
                return p.resolve()
        except Exception:
            continue
    return None


def mesie_available() -> Dict[str, Any]:
    root = mesie_root()
    engines: List[str] = []
    if root:
        eng = root / "mesie" / "engines"
        if eng.is_dir():
            engines = sorted(
                p.stem for p in eng.glob("*_engine.py")
            )[:20]
        elif (root / "engines").is_dir():
            engines = sorted(p.stem for p in (root / "engines").glob("*_engine.py"))[:20]
    return {
        "ok": root is not None,
        "product": "MESIE — Multi-Element Spectral Intelligence Engine",
        "root": str(root) if root else None,
        "engines": engines,
        "engine_count": len(engines),
        "cloudcolony_wrap": str(Path("E:/repos/cloudcolony-sovereign")),
        "roles": {
            "POCKET": "host co-pilot desk + mesh + sessions",
            "NEXUS": "MERIDIAN intelligence workers (MCP catalog)",
            "MESIE": "spectral engines, match/embed, colony compute lane",
            "CloudColony": "framework wrap (Triple Protocol + MCP colonies + ICP)",
        },
        "api_hooks": ["GET /v1/mesie", "POST /v1/mesie/run", "session mode=mesie"],
    }


def _ensure_path(root: Path) -> None:
    r = str(root)
    if r not in sys.path:
        sys.path.insert(0, r)


def status() -> Dict[str, Any]:
    info = mesie_available()
    if not info["ok"]:
        return {**info, "error": "MESIE root not found. Set MESIE_ROOT or install monorepo."}
    # light import probe
    try:
        root = Path(info["root"])
        _ensure_path(root)
        import mesie  # type: ignore  # noqa: F401

        info["import_ok"] = True
        info["version"] = getattr(mesie, "__version__", "present")
    except Exception as e:
        info["import_ok"] = False
        info["import_error"] = str(e)[:300]
    return info


def run_mesie_job(prompt: str) -> tuple:
    """Session job: status brief + optional cloudcolony/mesie real check."""
    st = status()
    lines = [
        f"# MESIE\n",
        f"**Root:** `{st.get('root')}`\n",
        f"**Engines:** {', '.join(st.get('engines') or []) or '—'}\n",
        f"**Import:** {st.get('import_ok')}\n",
        f"\n## Prompt\n{prompt or '(status)'}\n",
        "\n## Roles\n",
    ]
    for k, v in (st.get("roles") or {}).items():
        lines.append(f"- **{k}:** {v}\n")
    if not st.get("ok"):
        return "".join(lines), st.get("error") or "MESIE unavailable", "mesie"
    # Try CloudColony real verification if present
    try:
        sys.path.insert(0, r"E:\repos\cloudcolony-sovereign")
        from cloudcolony.api import smoke as cloudcolony_real

        sm = cloudcolony_real()
        lines.append(f"\n## CloudColony real\n```\n{sm}\n```\n")
    except Exception as e:
        lines.append(f"\n## CloudColony real\n_{e}_\n")
    return "".join(lines), "", "mesie"
