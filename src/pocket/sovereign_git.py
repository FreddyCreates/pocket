"""Sovereign Git vault — create/list/export repos *inside* POCKET.

Not GitHub-the-company: local-first git with optional download paths.
Repos live under ~/.pocket/git_vault (or E:/POCKET_MESH/vdisk/git when mesh up).
Each project gets pocket.toml + standard git so `git clone` / zip download works.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit


def _vault_root() -> Path:
    try:
        from pocket.mesh_disk import vdisk_path

        p = vdisk_path("git")
        p.mkdir(parents=True, exist_ok=True)
        return p
    except Exception:
        p = Path.home() / ".pocket" / "git_vault"
        p.mkdir(parents=True, exist_ok=True)
        return p


def _safe(name: str) -> str:
    n = re.sub(r"[^\w.\-]+", "-", (name or "repo").strip())[:64].strip("-.")
    return n or "repo"


def _run_git(args: List[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        timeout=60,
    )


def create_repo(
    name: str,
    *,
    description: str = "",
    private: bool = True,
    bare: bool = False,
    seed_readme: bool = True,
) -> Dict[str, Any]:
    """Create a git repository in the vault (working tree or bare)."""
    emit("git", f"create {name}", agent="GIT", role="python")
    root = _vault_root()
    safe = _safe(name)
    path = root / safe
    if path.exists():
        return {"ok": True, "already": True, "path": str(path), "name": safe, "message": f"Exists: {path}"}

    if bare:
        path.mkdir(parents=True, exist_ok=True)
        r = _run_git(["init", "--bare"], path)
        if r.returncode != 0:
            return {"ok": False, "error": (r.stderr or r.stdout or "git init bare failed")[:500]}
        # bare has no working tree readme
        meta = {
            "name": safe,
            "description": description,
            "private": private,
            "bare": True,
            "created_at": time.time(),
            "clone_path": str(path),
        }
        (path / "pocket.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    else:
        path.mkdir(parents=True, exist_ok=True)
        r = _run_git(["init"], path)
        if r.returncode != 0:
            return {"ok": False, "error": (r.stderr or r.stdout or "git init failed")[:500]}
        toml = (
            f'name = "{safe}"\n'
            f'description = "{(description or "POCKET sovereign repo").replace(chr(34), "")}"\n'
            f'private = {"true" if private else "false"}\n'
            f'host = "pocket-sovereign-git"\n'
            f'created = "{time.strftime("%Y-%m-%d")}"\n'
        )
        (path / "pocket.toml").write_text(toml, encoding="utf-8")
        if seed_readme:
            (path / "README.md").write_text(
                f"# {safe}\n\n{(description or 'Sovereign repo inside POCKET.')}\n\n"
                f"Clone path: `{path}`\n\n"
                f"```bash\ngit clone \"{path}\"\n```\n",
                encoding="utf-8",
            )
        _run_git(["add", "."], path)
        _run_git(["-c", "user.email=pocket@local", "-c", "user.name=POCKET", "commit", "-m", "chore: init sovereign repo"], path)
        meta = {
            "name": safe,
            "description": description,
            "private": private,
            "bare": False,
            "created_at": time.time(),
            "clone_path": str(path),
            "toml": str(path / "pocket.toml"),
        }
        (path / ".pocket-repo.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    # registry
    reg = _vault_root() / "REGISTRY.json"
    try:
        data = json.loads(reg.read_text(encoding="utf-8")) if reg.exists() else {"repos": []}
    except Exception:
        data = {"repos": []}
    data["repos"] = [x for x in data.get("repos") or [] if x.get("name") != safe]
    data["repos"].append(meta)
    data["updated"] = time.time()
    reg.write_text(json.dumps(data, indent=2), encoding="utf-8")

    return {
        "ok": True,
        "name": safe,
        "path": str(path),
        "clone": f'git clone "{path}"',
        "download_zip": f"/v1/git/repos/{safe}/zip",
        "message": f"Sovereign git repo ready at {path}",
        "meta": meta,
    }


def list_repos() -> Dict[str, Any]:
    root = _vault_root()
    repos = []
    for p in sorted(root.iterdir() if root.is_dir() else []):
        if not p.is_dir() or p.name.startswith("."):
            continue
        if p.name in ("REGISTRY.json",):
            continue
        is_git = (p / ".git").exists() or (p / "HEAD").exists()  # bare has HEAD
        if not is_git and not (p / "pocket.toml").exists():
            continue
        repos.append(
            {
                "name": p.name,
                "path": str(p),
                "bare": (p / "HEAD").exists() and not (p / ".git").exists(),
                "has_toml": (p / "pocket.toml").exists(),
                "mtime": p.stat().st_mtime,
            }
        )
    return {"ok": True, "vault": str(root), "repos": repos, "count": len(repos)}


def get_repo(name: str) -> Dict[str, Any]:
    path = _vault_root() / _safe(name)
    if not path.exists():
        return {"ok": False, "error": "not found"}
    return {
        "ok": True,
        "name": path.name,
        "path": str(path),
        "clone": f'git clone "{path}"',
        "files": [x.name for x in list(path.iterdir())[:40] if x.name != ".git"],
    }


def export_zip(name: str) -> Dict[str, Any]:
    """Zip working tree (or bare as archive of objects) for download to user files."""
    path = _vault_root() / _safe(name)
    if not path.is_dir():
        return {"ok": False, "error": "not found"}
    out_dir = Path.home() / ".pocket" / "git_exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    zpath = out_dir / f"{path.name}-{int(time.time())}.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in path.rglob("*"):
            if f.is_file():
                # skip huge packs optional — keep simple
                if f.stat().st_size > 80_000_000:
                    continue
                zf.write(f, f.relative_to(path).as_posix())
    return {
        "ok": True,
        "path": str(zpath),
        "name": zpath.name,
        "bytes": zpath.stat().st_size,
        "message": f"Export ready: {zpath}",
        "download_url": f"/v1/git/exports/{zpath.name}",
    }


def run_git_job(prompt: str) -> tuple:
    """Natural language → sovereign git actions (deterministic)."""
    low = (prompt or "").lower().strip()
    if low.startswith("list") or "list repo" in low:
        j = list_repos()
        lines = [f"## Sovereign git vault (`{j['vault']}`)\n"]
        for r in j.get("repos") or []:
            lines.append(f"- **{r['name']}** — `{r['path']}`")
        if not j.get("repos"):
            lines.append("_No repos yet. Try: `create repo my-app`_")
        return "\n".join(lines), "", "sovereign-git"

    m = re.search(r"(?:create|new|init)\s+(?:repo|repository|git)?\s*([a-zA-Z0-9._\-]+)", low)
    if not m and low.startswith("create "):
        m = re.search(r"create\s+([a-zA-Z0-9._\-]+)", low)
    if m or "create repo" in low or "new repo" in low:
        name = m.group(1) if m else "project"
        if name in ("repo", "repository", "git"):
            name = "project"
        r = create_repo(name, description=prompt[:200])
        if not r.get("ok"):
            return r.get("error") or "failed", "error", "sovereign-git"
        body = (
            f"## Repo created\n\n"
            f"**Name:** {r['name']}\n"
            f"**Path:** `{r['path']}`\n"
            f"**Clone:** `{r['clone']}`\n"
            f"**Zip:** `{r.get('download_zip')}`\n\n"
            f"This is **sovereign git** inside POCKET — same `git` tool, your vault, not GitHub.com.\n"
        )
        return body, "", "sovereign-git"

    m2 = re.search(r"(?:zip|export|download)\s+([a-zA-Z0-9._\-]+)", low)
    if m2 or "export" in low:
        name = m2.group(1) if m2 else ""
        if not name:
            repos = list_repos().get("repos") or []
            name = repos[0]["name"] if repos else ""
        if not name:
            return "No repo name to export.", "error", "sovereign-git"
        r = export_zip(name)
        return (r.get("message") or json.dumps(r)), ("" if r.get("ok") else r.get("error") or "fail"), "sovereign-git"

    help_ = (
        "## Sovereign Git (POCKET)\n\n"
        "- `create repo my-app` — init vault repo + pocket.toml\n"
        "- `list repos` — show vault\n"
        "- `export my-app` — zip to ~/.pocket/git_exports (downloadable)\n"
        "- Clone with normal git: `git clone \"<path>\"`\n\n"
        "Companion vision: next-gen sovereign forge (not commercial GitHub lock-in).\n"
    )
    return help_, "", "sovereign-git"
