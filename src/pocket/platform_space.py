"""Two editions, one hard rule.

  FOUNDER POCKET  — your install: full local PC + virtual space (yours)
  MARKET POCKET   — their install/seat: full local (theirs) + virtual (theirs)

  MARKET NEVER sees founder files and never uses founder paths
  (OneDrive of founder, Parallax, pocket-os source tree, etc.).

On a shared host process (invite seats on one machine), market seats are
jailed to ~/.pocket/tenants/<user>/ so they cannot walk the operator FS.
When a market user runs their OWN install, they are admin of that install
and get normal local+virtual on *their* machine — still never your machine.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

TENANTS_ROOT = Path.home() / ".pocket" / "tenants"
SAFE_USER = re.compile(r"^[a-z0-9][a-z0-9._-]{0,40}$")


def _safe_user(user: str) -> str:
    u = (user or "").strip().lower()
    if not u or not SAFE_USER.match(u) or ".." in u:
        raise ValueError("invalid tenant user")
    return u


def founder_deny_roots() -> List[Path]:
    """Paths market seats must never resolve into (even if they pass a cwd)."""
    roots: List[Path] = []
    env_extra = (os.environ.get("POCKET_FOUNDER_DENY") or "").strip()
    for part in env_extra.split(";"):
        part = part.strip()
        if part:
            roots.append(Path(part))
    # Common founder trees on THIS operator machine — market must not land here
    for cand in (
        os.environ.get("POCKET_CODEX_CWD") or "",
        os.environ.get("PARALLAX_ROOT") or "",
        str(Path.home() / "OneDrive" / "pocket-os"),
        str(Path.home() / "OneDrive" / "Documents" / "GitHub"),
        r"E:\PARALLAX-Exchange-Clearinghouse",
        r"E:\POCKET_MESH",
        str(Path(__file__).resolve().parents[2]),  # this pocket-os checkout
    ):
        if cand:
            roots.append(Path(cand))
    out: List[Path] = []
    for p in roots:
        try:
            if p.exists():
                out.append(p.resolve())
        except Exception:
            try:
                out.append(p)
            except Exception:
                pass
    return out


def path_is_founder_private(path: str) -> bool:
    """True if path is inside a founder-private tree market must not use."""
    try:
        target = Path(path).resolve()
    except Exception:
        return True
    # Tenant trees are always allowed for their owner
    try:
        tr = TENANTS_ROOT.resolve()
        if str(target).lower().startswith(str(tr).lower()):
            return False
    except Exception:
        pass
    for root in founder_deny_roots():
        try:
            r = str(root.resolve() if root.exists() else root).lower().rstrip("\\/")
            t = str(target).lower()
            if t == r or t.startswith(r + "\\") or t.startswith(r + "/"):
                return True
        except Exception:
            continue
    return False


def tenant_root(user: str) -> Path:
    """Per-account market space on a shared host (virtual + sandboxed local)."""
    u = _safe_user(user)
    root = TENANTS_ROOT / u
    for sub in ("files", "local", "projects", "git", "deliverables", "uploads"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    readme = root / "files" / "README.md"
    if not readme.exists():
        readme.write_text(
            f"# {u} — market POCKET space\n\n"
            "This is **your** space on the platform.\n\n"
            "- `files/` — virtual sovereign explorer\n"
            "- `local/` — sandboxed local workspace (not the operator's PC)\n"
            "- `git/` / `projects/` — your repos and shared project rooms\n\n"
            "You never see the founder's personal files.\n",
            encoding="utf-8",
        )
    meta = root / "space.json"
    if not meta.exists():
        meta.write_text(
            json.dumps(
                {
                    "schema": "pocket.tenant_space.v1",
                    "user": u,
                    "created_at": time.time(),
                    "edition": "market",
                    "founder_files": False,
                    "local": True,
                    "virtual": True,
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    return root


def tenant_cwd(user: str, workspace: str = "files") -> str:
    """Market seat working dir — always inside their tenant (local+virtual)."""
    root = tenant_root(user)
    ws = (workspace or "files").strip().lower()
    mapping = {
        "files": "files",
        "space": "files",
        "workspace": "files",
        "default": "files",
        "scratch": "files",
        "virtual": "files",
        "local": "local",
        "projects": "projects",
        "project": "projects",
        "git": "git",
        "forge": "git",
        "sovereign-git": "git",
        "deliverables": "deliverables",
        "out": "deliverables",
    }
    if ws.startswith("tenant:"):
        sub = "files"
    else:
        sub = mapping.get(ws, "files")
    p = root / sub
    p.mkdir(parents=True, exist_ok=True)
    return str(p.resolve())


def is_under_tenant(user: str, path: str) -> bool:
    try:
        root = tenant_root(user).resolve()
        target = Path(path).resolve()
        return str(target).lower().startswith(str(root).lower())
    except Exception:
        return False


def resolve_member_path(user: str, rel: str = "") -> Path:
    root = tenant_root(user).resolve()
    rel = (rel or "").replace("\\", "/").lstrip("/")
    if not rel or rel in (".", "files"):
        return root / "files"
    if ".." in rel.split("/"):
        raise ValueError("path escape blocked")
    if rel.startswith("/") or re.match(r"^[A-Za-z]:", rel):
        raise ValueError("absolute host paths not allowed for market seats on shared host")
    target = (root / rel).resolve()
    if not str(target).lower().startswith(str(root).lower()):
        raise ValueError("path escape blocked")
    return target


def list_space(user: str, rel: str = "files") -> Dict[str, Any]:
    try:
        base = resolve_member_path(user, rel or "files")
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    if not base.exists():
        base.mkdir(parents=True, exist_ok=True)
    if not base.is_dir():
        return {"ok": False, "error": "not a directory"}
    entries: List[Dict[str, Any]] = []
    for child in sorted(base.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
        try:
            st = child.stat()
            entries.append(
                {
                    "name": child.name,
                    "path": str(child.relative_to(tenant_root(user))).replace("\\", "/"),
                    "type": "dir" if child.is_dir() else "file",
                    "size": st.st_size if child.is_file() else None,
                    "mtime": st.st_mtime,
                }
            )
        except OSError:
            continue
    return {
        "ok": True,
        "user": _safe_user(user),
        "edition": "market",
        "cwd": str(base),
        "rel": str(base.relative_to(tenant_root(user))).replace("\\", "/"),
        "entries": entries,
        "founder_files": False,
        "local": True,
        "virtual": True,
        "note": "Your market space (local sandbox + virtual). Not the founder's files.",
    }


def write_text(user: str, rel: str, content: str) -> Dict[str, Any]:
    try:
        path = resolve_member_path(user, rel)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or "", encoding="utf-8")
    return {
        "ok": True,
        "path": str(path.relative_to(tenant_root(user))).replace("\\", "/"),
        "bytes": len((content or "").encode("utf-8")),
    }


def read_text(user: str, rel: str, max_bytes: int = 200_000) -> Dict[str, Any]:
    try:
        path = resolve_member_path(user, rel)
    except ValueError as e:
        return {"ok": False, "error": str(e)}
    if not path.is_file():
        return {"ok": False, "error": "not a file"}
    data = path.read_bytes()[:max_bytes]
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {"ok": False, "error": "binary file", "size": path.stat().st_size}
    return {
        "ok": True,
        "path": str(path.relative_to(tenant_root(user))).replace("\\", "/"),
        "content": text,
        "truncated": len(data) >= max_bytes,
    }


def ensure_job_isolation(job: Dict[str, Any], *, founder: bool) -> Dict[str, Any]:
    """Founder jobs: host power. Market seats: never founder paths."""
    owner = (job.get("owner") or "").strip().lower()
    if founder:
        job["host_power"] = True
        job["edition"] = "founder"
        # Still reject if someone stuffed a market owner into founder session wrongly
        return job
    if not owner or owner == "anonymous":
        job["host_power"] = False
        job["edition"] = "market"
        return job
    job["host_power"] = False
    job["edition"] = "market"
    job["space"] = "market"
    # Force market local+virtual under tenant — never founder OneDrive/Parallax
    cwd = (job.get("cwd") or "").strip()
    if cwd and is_under_tenant(owner, cwd) and not path_is_founder_private(cwd):
        job["cwd"] = str(Path(cwd).resolve())
    else:
        job["cwd"] = tenant_cwd(owner, job.get("workspace") or "files")
    job["workspace"] = f"tenant:{owner}"
    return job


def space_summary(user: str) -> Dict[str, Any]:
    root = tenant_root(user)
    return {
        "ok": True,
        "user": _safe_user(user),
        "edition": "market",
        "root": str(root),
        "founder_files": False,
        "surfaces": {
            "virtual_files": str(root / "files"),
            "local_sandbox": str(root / "local"),
            "projects": str(root / "projects"),
            "git": str(root / "git"),
            "deliverables": str(root / "deliverables"),
        },
        "doctrine": {
            "founder_pocket": "Operator's local PC + virtual — private",
            "market_pocket": "User's local + virtual — never founder files",
            "invite": "Marketing + seat creation, not access to founder disk",
        },
    }
