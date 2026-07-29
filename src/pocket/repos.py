"""Local folders, zips, git repos + GitHub (signed-in `gh` / browser).

Creates under ~/.pocket/workspaces or user OneDrive/Documents when asked.
GitHub: uses `gh` CLI when authenticated (no password in POCKET).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "workspaces"
ROOT.mkdir(parents=True, exist_ok=True)


def _safe_name(name: str) -> str:
    n = re.sub(r"[^\w\-.]+", "-", (name or "project").strip())[:60].strip("-")
    return n or "project"


def create_folder(name: str, *, under: str = "") -> Dict[str, Any]:
    emit("repo", f"Creating folder {name}", agent="repos", role="python")
    base = Path(under) if under and Path(under).is_dir() else ROOT
    path = base / _safe_name(name)
    path.mkdir(parents=True, exist_ok=True)
    readme = path / "README.md"
    if not readme.exists():
        readme.write_text(f"# {name}\n\nCreated by POCKET repos agent.\n", encoding="utf-8")
    emit("repo", f"Folder ready: {path}", agent="repos", role="python")
    return {"ok": True, "kind": "folder", "path": str(path), "message": f"Created {path}"}


def zip_folder(path: str, *, out_name: str = "") -> Dict[str, Any]:
    emit("repo", f"Zipping {path}", agent="repos", role="python")
    p = Path(path)
    if not p.is_dir():
        return {"ok": False, "error": f"not a directory: {path}"}
    # only allow under home
    home = Path.home().resolve()
    try:
        p.resolve().relative_to(home)
    except Exception:
        return {"ok": False, "error": "zip path must be under home"}
    zname = out_name or (p.name + ".zip")
    zpath = p.parent / _safe_name(zname.replace(".zip", "")) 
    if not str(zpath).endswith(".zip"):
        zpath = Path(str(zpath) + ".zip")
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in p.rglob("*"):
            if f.is_file():
                zf.write(f, f.relative_to(p).as_posix())
    emit("repo", f"Zip ready: {zpath}", agent="repos", role="python")
    return {"ok": True, "kind": "zip", "path": str(zpath), "message": f"Zipped → {zpath}"}


def init_git_repo(name: str, *, under: str = "") -> Dict[str, Any]:
    emit("repo", f"git init {name}", agent="repos", role="python")
    folder = create_folder(name, under=under)
    if not folder.get("ok"):
        return folder
    path = folder["path"]
    try:
        r = subprocess.run(
            ["git", "init"],
            cwd=path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        subprocess.run(["git", "add", "."], cwd=path, capture_output=True, timeout=30)
        subprocess.run(
            ["git", "commit", "-m", "chore: init from POCKET"],
            cwd=path,
            capture_output=True,
            timeout=30,
        )
        emit("repo", f"git repo at {path} rc={r.returncode}", agent="repos", role="python")
        return {
            "ok": True,
            "kind": "git_init",
            "path": path,
            "message": f"Local git repo: {path}",
            "git_out": (r.stdout or r.stderr or "")[:500],
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "path": path}


def gh_available() -> Dict[str, Any]:
    exe = shutil.which("gh") or ""
    if not exe:
        return {"ok": False, "gh": False, "error": "gh CLI not installed"}
    try:
        r = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        out = (r.stdout or "") + (r.stderr or "")
        authed = r.returncode == 0 or "Logged in" in out
        return {"ok": authed, "gh": True, "path": exe, "status": out[:800], "authenticated": authed}
    except Exception as e:
        return {"ok": False, "gh": True, "error": str(e)}


def list_github_repos(limit: int = 5) -> Dict[str, Any]:
    emit("github", f"Listing up to {limit} repos via gh", agent="github", role="python")
    st = gh_available()
    if not st.get("gh"):
        return {"ok": False, "error": "gh not found", "status": st}
    try:
        r = subprocess.run(
            ["gh", "repo", "list", "--limit", str(limit), "--json", "name,url,description,isPrivate,updatedAt"],
            capture_output=True,
            text=True,
            timeout=45,
        )
        if r.returncode != 0:
            return {"ok": False, "error": (r.stderr or r.stdout or "gh failed")[:800], "status": st}
        repos = json.loads(r.stdout or "[]")
        emit("github", f"Found {len(repos)} repos", agent="github", role="python", meta={"n": len(repos)})
        return {"ok": True, "repos": repos, "count": len(repos), "auth": st}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def open_github_repos(limit: int = 5) -> Dict[str, Any]:
    """Open first N GitHub repos in signed-in Edge (browser session)."""
    from pocket.browser_mode import open_edge_url

    listed = list_github_repos(limit=limit)
    if not listed.get("ok"):
        return listed
    opened = []
    for repo in listed.get("repos") or []:
        url = repo.get("url") or ""
        if not url:
            continue
        emit("github", f"Opening {url}", agent="github", role="python")
        opened.append({"repo": repo.get("name"), "url": url, **open_edge_url(url)})
        time.sleep(0.35)
    return {
        "ok": True,
        "kind": "github_open",
        "count": len(opened),
        "repos": listed.get("repos"),
        "opened": opened,
        "message": f"Opened {len(opened)} GitHub repo pages in Edge (signed-in browser profile)",
    }


def create_github_repo(name: str, *, public: bool = True, source_path: str = "") -> Dict[str, Any]:
    emit("github", f"Creating GitHub repo {name}", agent="github", role="python")
    st = gh_available()
    if not st.get("authenticated"):
        return {"ok": False, "error": "gh not authenticated — run `gh auth login` once on the host", "status": st}
    path = source_path
    if not path:
        local = init_git_repo(name)
        if not local.get("ok"):
            return local
        path = local["path"]
    vis = "public" if public else "private"
    try:
        r = subprocess.run(
            ["gh", "repo", "create", _safe_name(name), f"--{vis}", "--source", path, "--remote", "origin", "--push"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=path,
        )
        out = (r.stdout or "") + (r.stderr or "")
        emit("github", f"gh repo create rc={r.returncode}", agent="github", role="python")
        return {
            "ok": r.returncode == 0,
            "kind": "github_create",
            "path": path,
            "out": out[:2000],
            "message": "GitHub repo created" if r.returncode == 0 else "gh create failed",
            "error": "" if r.returncode == 0 else out[:800],
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def clone_repo(url_or_name: str) -> Dict[str, Any]:
    """Clone into ~/.pocket/workspaces (shallow). Uses gh or git."""
    raw = (url_or_name or "").strip()
    emit("github", f"Clone {raw}", agent="REPOSITOR", role="python")
    if not raw:
        return {"ok": False, "error": "url required"}
    name = _safe_name(raw.rstrip("/").split("/")[-1].replace(".git", ""))
    dest = ROOT / name
    if dest.exists():
        return {"ok": True, "path": str(dest), "already": True, "message": f"Already cloned: {dest}"}
    try:
        # Prefer HTTPS so we don't need SSH keys (gh auth login handles HTTPS)
        if raw.startswith("http"):
            url = raw if raw.endswith(".git") else raw.rstrip("/") + ".git"
            if "github.com" in url and not url.endswith(".git"):
                url = url + ".git"
        elif raw.count("/") >= 1 and "github.com" not in raw:
            # owner/name
            url = f"https://github.com/{raw.strip('/')}.git"
        else:
            url = raw

        env = os.environ.copy()
        # Use gh as git credential helper when available
        if shutil.which("gh"):
            try:
                subprocess.run(
                    ["gh", "auth", "setup-git"],
                    capture_output=True,
                    timeout=20,
                )
            except Exception:
                pass

        r = subprocess.run(
            ["git", "clone", "--depth", "1", url, str(dest)],
            capture_output=True,
            text=True,
            timeout=180,
            env=env,
        )
        # Fallback: gh repo clone with https protocol
        if r.returncode != 0 and shutil.which("gh"):
            repo = raw.replace("https://github.com/", "").replace(".git", "").strip("/")
            r = subprocess.run(
                ["gh", "repo", "clone", repo, str(dest), "--", "--depth", "1", "--config", "core.sshCommand=true"],
                capture_output=True,
                text=True,
                timeout=180,
                env={**env, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "url.https://github.com/.insteadOf", "GIT_CONFIG_VALUE_0": "ssh://git@github.com/"},
            )
            if r.returncode != 0:
                # last resort: gh api tarball
                try:
                    tar = dest.with_suffix(".tar.gz")
                    r2 = subprocess.run(
                        ["gh", "api", f"repos/{repo}/tarball", "-H", "Accept: application/vnd.github+json"],
                        capture_output=True,
                        timeout=180,
                    )
                    if r2.returncode == 0 and r2.stdout:
                        tar.write_bytes(r2.stdout)
                        dest.mkdir(parents=True, exist_ok=True)
                        subprocess.run(
                            ["tar", "-xzf", str(tar), "-C", str(dest), "--strip-components=1"],
                            capture_output=True,
                            timeout=60,
                        )
                        tar.unlink(missing_ok=True)
                        if any(dest.iterdir()):
                            return {
                                "ok": True,
                                "path": str(dest),
                                "message": f"Fetched tarball to {dest}",
                                "method": "gh_tarball",
                                "agent": "REPOSITOR",
                            }
                except Exception as te:
                    pass

        ok = r.returncode == 0 and dest.exists() and any(dest.iterdir()) if dest.exists() else False
        return {
            "ok": ok,
            "path": str(dest) if dest.exists() else "",
            "out": ((r.stdout or "") + (r.stderr or ""))[:1500],
            "url": url,
            "message": f"Cloned to {dest}" if ok else "clone failed",
            "error": "" if ok else ((r.stderr or r.stdout or "")[:500]),
            "agent": "REPOSITOR",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def analyze_github_repo(target: str, *, useful_for: str = "POCKET") -> Dict[str, Any]:
    """Inspect a repo without requiring full local WASM — prefer gh API / shallow clone + README.

    Resolves 'brain ai', 'imagine', neuroemergence, imagiEngine by name search.
    """
    t = (target or "").strip()
    emit("github", f"Analyze {t[:80]} for {useful_for[:40]}", agent="SCRUTATOR", role="python")

    # Resolve friendly names
    aliases = {
        "brain ai": "neuroemergence-core",
        "brain": "neuroemergence-core",
        "brainai": "neuroemergence-core",
        "imagine": "imagiEngine",
        "imagi": "imagiEngine",
        "imagiengine": "imagiEngine",
        "mesie": "Multi-Element-Spectral-Intelligence-Engine-MESIE-",
        "guppy": "pocket",
    }
    key = t.lower().replace("analyze", "").replace("repo", "").strip()
    for a, name in aliases.items():
        if a in key:
            t = name
            break

    repo_full = t
    # If bare name, try owner/FreddyCreates or gh repo view
    files_meta = []
    readme = ""
    desc = ""
    url = ""
    try:
        # search user repos
        if "/" not in t and "github.com" not in t:
            listed = list_github_repos(30)
            match = None
            for r in listed.get("repos") or []:
                n = (r.get("name") or "").lower()
                if t.lower() in n or n in t.lower():
                    match = r
                    break
            # also search more via gh
            if not match and shutil.which("gh"):
                r = subprocess.run(
                    ["gh", "repo", "list", "--limit", "50", "--json", "name,url,description"],
                    capture_output=True,
                    text=True,
                    timeout=40,
                )
                if r.returncode == 0:
                    for row in json.loads(r.stdout or "[]"):
                        if t.lower() in (row.get("name") or "").lower():
                            match = row
                            break
            if match:
                url = match.get("url") or ""
                desc = match.get("description") or ""
                repo_full = url.replace("https://github.com/", "") if url else match.get("name")
            else:
                repo_full = f"FreddyCreates/{t}" if "/" not in t else t
        else:
            repo_full = t.replace("https://github.com/", "").strip("/")

        if shutil.which("gh"):
            # view
            r = subprocess.run(
                ["gh", "repo", "view", repo_full, "--json", "name,url,description,defaultBranchRef"],
                capture_output=True,
                text=True,
                timeout=40,
            )
            if r.returncode == 0:
                meta = json.loads(r.stdout or "{}")
                url = meta.get("url") or url
                desc = meta.get("description") or desc
            # README
            r2 = subprocess.run(
                ["gh", "api", f"repos/{repo_full}/readme", "-H", "Accept: application/vnd.github.raw"],
                capture_output=True,
                text=True,
                timeout=40,
            )
            if r2.returncode == 0:
                readme = (r2.stdout or "")[:12000]
            # tree top-level
            r3 = subprocess.run(
                ["gh", "api", f"repos/{repo_full}/contents/"],
                capture_output=True,
                text=True,
                timeout=40,
            )
            if r3.returncode == 0:
                try:
                    arr = json.loads(r3.stdout or "[]")
                    files_meta = [x.get("name") for x in arr if isinstance(x, dict) and x.get("name")][:40]
                except Exception:
                    files_meta = []
    except Exception as e:
        return {"ok": False, "error": str(e), "target": t}

    # Optional shallow clone for deeper scan
    local_path = ""
    useful = []
    if url or repo_full:
        cl = clone_repo(repo_full if "/" in repo_full else url)
        if cl.get("ok"):
            local_path = cl.get("path") or ""
            # scan for keywords useful to POCKET
            keywords = (
                "agent", "mcp", "orchestr", "desktop", "browser", "worker", "session",
                "memory", "spectral", "neuro", "copilot", "api", "token", "protocol",
            )
            root = Path(local_path) if local_path else None
            if root and root.is_dir():
                for f in list(root.rglob("*.md"))[:30] + list(root.rglob("*.py"))[:40] + list(root.rglob("*.ts"))[:20]:
                    try:
                        if f.stat().st_size > 200_000:
                            continue
                        txt = f.read_text(encoding="utf-8", errors="replace")[:8000].lower()
                        hits = [k for k in keywords if k in txt]
                        if hits:
                            useful.append(
                                {
                                    "file": str(f.relative_to(root)).replace("\\", "/"),
                                    "hits": hits[:8],
                                    "snippet": txt[:200].replace("\n", " "),
                                }
                            )
                    except Exception:
                        continue
                useful = useful[:25]

    # Open in Edge for human
    if url:
        try:
            from pocket.browser_mode import open_edge_url

            open_edge_url(url)
        except Exception:
            pass

    analysis = {
        "ok": True,
        "agent": "SCRUTATOR+REPOSITOR",
        "target": t,
        "repo": repo_full,
        "url": url,
        "description": desc,
        "top_files": files_meta,
        "readme_excerpt": readme[:4000],
        "local_clone": local_path,
        "useful_for": useful_for,
        "useful_files": useful,
        "recommendations": _recommendations(readme, useful, useful_for),
        "message": f"Analyzed {repo_full or t} — opened on GitHub + local notes for POCKET",
    }
    emit("github", f"Analysis done {repo_full}", agent="SCRUTATOR", role="python", meta={"files": len(useful)})
    return analysis


def _recommendations(readme: str, useful: List[Dict], useful_for: str) -> List[str]:
    rec = []
    blob = (readme or "").lower() + " " + " ".join(
        (u.get("file", "") + " " + " ".join(u.get("hits") or [])) for u in useful
    )
    hit_counts: Dict[str, int] = {}
    for u in useful:
        for h in u.get("hits") or []:
            hit_counts[h] = hit_counts.get(h, 0) + 1
    if hit_counts.get("agent") or hit_counts.get("orchestr") or "agent" in blob:
        rec.append("Agent/orchestration code present — map roles onto ARCHON / HYDRA / GUPPY")
    if hit_counts.get("memory") or hit_counts.get("neuro") or "neuro" in blob:
        rec.append("Memory/neuro patterns — session memory packs for SCRUTATOR + desk context")
    if hit_counts.get("mcp") or "mcp" in blob:
        rec.append("MCP surfaces — wire into POCKET NEXUS / agent tools")
    if hit_counts.get("api") or "api" in blob:
        rec.append("API shapes — mirror in easy desk API POST /v1/desk")
    if hit_counts.get("desktop") or hit_counts.get("browser"):
        rec.append("Desktop/browser concepts — align with PORTARIUS / NAVIGATOR")
    if hit_counts.get("protocol") or hit_counts.get("token"):
        rec.append("Protocol/token ideas — POCK + safety policy parallels")
    if "caffeine" in blob:
        rec.append("Caffeine export — treat as external deploy target, not host password store")
    if "AGENTS.md" in " ".join(u.get("file", "") for u in useful) or "agents.md" in blob:
        rec.append("AGENTS.md found — import skill doctrine into POCKET worker docs")
    if not rec:
        rec.append(f"Skim README + useful_files for hooks into {useful_for}")
    rec.append("Clone path: ~/.pocket/workspaces (HTTPS + gh auth — no SSH required)")
    return rec


def run_repos_job(prompt: str) -> Tuple[str, str, str]:
    text = (prompt or "").strip()
    low = text.lower()
    if low in ("help", "", "repos help"):
        return (
            "## REPOSITOR · GitHub agent\n\n"
            "- `list repos` / `open my 5 repos`\n"
            "- `analyze brain ai` · `analyze imagine` · `analyze neuroemergence-core`\n"
            "- `clone owner/repo` — shallow into ~/.pocket/workspaces\n"
            "- `new folder` · `new repo` · `zip` · `github create` · `gh status`\n",
            "",
            "repositor",
        )
    if low.startswith("analyze ") or low.startswith("inspect "):
        r = analyze_github_repo(text.split(None, 1)[-1] if " " in text else text)
        if not r.get("ok"):
            return "", r.get("error") or "analyze failed", "repositor"
        lines = [
            f"## REPOSITOR + SCRUTATOR · {r.get('repo')}",
            "",
            f"**{r.get('description') or ''}**",
            f"URL: {r.get('url')}",
            f"Local: `{r.get('local_clone') or '—'}`",
            "",
            "### Recommendations for POCKET",
        ]
        for rec in r.get("recommendations") or []:
            lines.append(f"- {rec}")
        lines.append("\n### Top files")
        for f in (r.get("top_files") or [])[:20]:
            lines.append(f"- `{f}`")
        lines.append("\n### Useful hits")
        for u in (r.get("useful_files") or [])[:12]:
            lines.append(f"- `{u.get('file')}` · {', '.join(u.get('hits') or [])}")
        lines.append("\n### README excerpt\n```\n" + (r.get("readme_excerpt") or "")[:2500] + "\n```")
        return "\n".join(lines), "", "repositor"
    if low.startswith("clone "):
        r = clone_repo(text[6:].strip())
        return f"## Clone\n\n{r.get('message') or r}\n", "" if r.get("ok") else r.get("error", ""), "repositor"
    if low in ("gh status", "github status", "auth"):
        st = gh_available()
        return f"## gh status\n\n```json\n{json.dumps(st, indent=2)}\n```", "", "repos"
    if low in ("list repos", "github list", "list github", "my repos"):
        r = list_github_repos(5)
        if not r.get("ok"):
            return "", r.get("error") or "list failed", "repos"
        lines = ["## Your GitHub repos (top 5)\n"]
        for repo in r.get("repos") or []:
            lines.append(f"- **{repo.get('name')}** — {repo.get('url')}\n  _{repo.get('description') or ''}_")
        return "\n".join(lines), "", "repos"
    if low in ("open github", "open my 5 repos", "open repos", "open first 5 repos", "open my repos"):
        r = open_github_repos(5)
        if not r.get("ok"):
            return "", r.get("error") or "open failed", "repos"
        lines = [f"## Opened {r.get('count')} repos in Edge\n", r.get("message", "")]
        for o in r.get("opened") or []:
            lines.append(f"- {o.get('repo')}: {o.get('url')} · ok={o.get('ok')}")
        return "\n".join(lines), "", "repos"
    if low.startswith("new folder "):
        r = create_folder(text[11:].strip())
        return f"## Folder\n\n{r.get('message') or r}\n", "" if r.get("ok") else r.get("error", ""), "repos"
    if low.startswith("new repo ") or low.startswith("git init "):
        name = re.sub(r"^(new repo|git init)\s+", "", text, flags=re.I).strip()
        r = init_git_repo(name)
        return f"## Git repo\n\n{r.get('message') or r}\n", "" if r.get("ok") else r.get("error", ""), "repos"
    if low.startswith("zip "):
        r = zip_folder(text[4:].strip().strip('"'))
        return f"## Zip\n\n{r.get('message') or r}\n", "" if r.get("ok") else r.get("error", ""), "repos"
    if low.startswith("github create ") or low.startswith("gh create "):
        name = re.sub(r"^(github create|gh create)\s+", "", text, flags=re.I).strip()
        r = create_github_repo(name)
        return f"## GitHub create\n\n```\n{r.get('out') or r.get('message') or r}\n```\n", "" if r.get("ok") else r.get("error", ""), "repos"
    return "Unknown repos command. Try `help` or `open my 5 repos`.", "unknown", "repos"
