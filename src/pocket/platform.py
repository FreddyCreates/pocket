"""Platform inventory + local deploys (static / npm / python) with logs."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import time
import uuid
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock, Thread
from typing import Any, Dict, List, Optional

from pocket.executor import KNOWN_WORKSPACES, resolve_cwd
from pocket.jobs import WORK_DIR
from pocket.live import lan_ip, probe_all
from pocket.tokenomics import burn

ROOT = Path.home() / ".pocket"
DEPLOY_DIR = ROOT / "deploys"
LOG_DIR = DEPLOY_DIR / "logs"
DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
_lock = Lock()
_servers: Dict[str, Any] = {}  # deploy_id -> runtime handles


def _dpath(did: str) -> Path:
    return DEPLOY_DIR / f"{did}.json"


def _save_deploy(d: Dict[str, Any]) -> None:
    _dpath(d["id"]).write_text(json.dumps(d, indent=2), encoding="utf-8")


def list_deploys() -> List[Dict[str, Any]]:
    out = []
    for f in sorted(DEPLOY_DIR.glob("d-*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    # refresh alive flag for process deploys
    for d in out:
        if d.get("status") == "running" and d.get("pid"):
            try:
                os.kill(int(d["pid"]), 0)
            except Exception:
                d["status"] = "exited"
                try:
                    _save_deploy(d)
                except Exception:
                    pass
    return out


def _free_port(start: int = 8800) -> int:
    for port in range(start, start + 120):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError("no free port")


def platform_manifest() -> Dict[str, Any]:
    ip = lan_ip()
    live = probe_all()
    deploys = list_deploys()
    running = [d for d in deploys if d.get("status") == "running"]
    return {
        "ok": True,
        "product": "POCKET Platform",
        "tagline": "Orchestration layer on top of the CLIs you already pay for",
        "why_not_just_cli": [
            "You already have Codex + Grok — POCKET is the multi-agent desk, not a replacement CLI.",
            "Run many agents + interactive terminals side-by-side with shared workspaces.",
            "Live suite connect, session history, plan handoffs, and streaming tokens in one UI.",
            "Local deploys (static/npm/python) with logs — ship without leaving the desk.",
            "Phone/LAN remote control of the same desk.",
            "Embedded POCK metering so multi-agent spend is visible.",
        ],
        "you_have": {
            "multi_agent_console": f"http://127.0.0.1:8787/",
            "phone_url": f"http://{ip}:8787/",
            "engines": ["codex", "claude", "shell", "wsl", "grok", "term", "handoff"],
            "workspaces": KNOWN_WORKSPACES,
            "live_services": live.get("services"),
            "local_deploys_running": len(running),
            "local_deploys_total": len(deploys),
            "tokenomics": "embedded POCK ledger",
            "streaming": "live log_tail + stream_tokens on running jobs",
            "interactive_terminals": True,
        },
        "tools": [
            {"id": "sessions", "what": "Unlimited parallel Codex/Grok/Claude/shell sessions"},
            {"id": "stream", "what": "Stream agent logs + token estimates while running"},
            {"id": "term", "what": "Long-lived interactive PowerShell/cmd/WSL terminals"},
            {"id": "deploy_static", "what": "Static file server from workspace"},
            {"id": "deploy_npm", "what": "npm run dev/start with log tail"},
            {"id": "deploy_python", "what": "python app / http.server with log tail"},
            {"id": "live_connect", "what": "Probe + start suite services"},
            {"id": "tokenomics", "what": "POCK burn on agent/deploy/terminal use"},
            {"id": "handoff", "what": "Plan handoff packages without burning coding turns"},
        ],
        "deploys": deploys[:20],
        "lan_ip": ip,
    }


def deploy_static(
    *,
    workspace: str = "workspace",
    subpath: str = "",
    title: str = "",
    port: int = 0,
) -> Dict[str, Any]:
    cwd = resolve_cwd({"workspace": workspace, "cwd": ""})
    root = Path(cwd)
    if subpath:
        root = (root / subpath).resolve()
        try:
            root.relative_to(Path(cwd).resolve())
        except ValueError:
            return {"ok": False, "error": "subpath escapes workspace"}
    if not root.is_dir():
        return {"ok": False, "error": f"not a directory: {root}"}

    port = port or _free_port()
    did = f"d-{uuid.uuid4().hex[:10]}"

    class _Handler(SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(root), **k)

        def log_message(self, *a):
            pass

    try:
        httpd = ThreadingHTTPServer(("0.0.0.0", port), _Handler)
    except OSError as e:
        return {"ok": False, "error": str(e)}

    t = Thread(target=httpd.serve_forever, name=f"deploy-{did}", daemon=True)
    t.start()
    ip = lan_ip()
    rec = {
        "id": did,
        "schema": "pocket.deploy.v2",
        "kind": "static",
        "title": title or f"static:{root.name}",
        "workspace": workspace,
        "root": str(root),
        "port": port,
        "url_local": f"http://127.0.0.1:{port}/",
        "url_lan": f"http://{ip}:{port}/",
        "status": "running",
        "started_at": time.time(),
        "log_path": None,
    }
    with _lock:
        _servers[did] = {"type": "static", "httpd": httpd, "thread": t}
        _save_deploy(rec)
    burn("deploy_start", meta={"deploy_id": did, "kind": "static"})
    return {"ok": True, **rec}


def deploy_process(
    *,
    kind: str = "npm",
    workspace: str = "workspace",
    command: str = "",
    title: str = "",
    port: int = 0,
    cwd_subpath: str = "",
) -> Dict[str, Any]:
    """Start npm or python process with log file."""
    kind = (kind or "npm").lower()
    base = Path(resolve_cwd({"workspace": workspace, "cwd": ""}))
    root = base / cwd_subpath if cwd_subpath else base
    if not root.is_dir():
        return {"ok": False, "error": f"not a directory: {root}"}

    port = port or _free_port(8900)
    did = f"d-{uuid.uuid4().hex[:10]}"
    log_path = LOG_DIR / f"{did}.log"

    if command.strip():
        # user override — run via shell
        cmd_str = command.strip()
        # inject PORT if placeholder
        cmd_str = cmd_str.replace("{port}", str(port))
        argv = cmd_str if os.name == "nt" else cmd_str
        use_shell = True
        cmd_list: Any = argv
    elif kind == "npm":
        # Prefer dev server bound to port
        pkg = root / "package.json"
        if not pkg.exists():
            return {"ok": False, "error": "no package.json — use command= or static deploy"}
        # cross-platform-ish: npm run dev -- --host 0.0.0.0 --port N
        cmd_list = f'npm run dev -- --host 0.0.0.0 --port {port}'
        use_shell = True
    elif kind in ("python", "py"):
        # Prefer app.py / main.py, else http.server
        if (root / "app.py").exists():
            cmd_list = f"python app.py"
            use_shell = True
        elif (root / "main.py").exists():
            cmd_list = f"python main.py"
            use_shell = True
        else:
            cmd_list = f"python -m http.server {port} --bind 0.0.0.0"
            use_shell = True
        kind = "python"
    else:
        return {"ok": False, "error": "kind must be npm|python|static"}

    log_f = open(log_path, "w", encoding="utf-8", errors="replace")
    log_f.write(f"[deploy {did}] kind={kind} port={port}\ncmd={cmd_list}\ncwd={root}\n\n")
    log_f.flush()
    try:
        if os.name == "nt":
            p = subprocess.Popen(
                cmd_list if use_shell else cmd_list,
                cwd=str(root),
                shell=use_shell,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PORT": str(port), "HOST": "0.0.0.0"},
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,  # type: ignore
            )
        else:
            p = subprocess.Popen(
                cmd_list if use_shell else cmd_list,
                cwd=str(root),
                shell=use_shell,
                stdout=log_f,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PORT": str(port), "HOST": "0.0.0.0"},
                start_new_session=True,
            )
    except Exception as e:
        log_f.close()
        return {"ok": False, "error": str(e)}

    ip = lan_ip()
    rec = {
        "id": did,
        "schema": "pocket.deploy.v2",
        "kind": kind,
        "title": title or f"{kind}:{root.name}",
        "workspace": workspace,
        "root": str(root),
        "command": str(cmd_list),
        "port": port,
        "pid": p.pid,
        "url_local": f"http://127.0.0.1:{port}/",
        "url_lan": f"http://{ip}:{port}/",
        "status": "running",
        "started_at": time.time(),
        "log_path": str(log_path),
    }
    with _lock:
        _servers[did] = {"type": "process", "proc": p, "log": log_f}
        _save_deploy(rec)
    burn("deploy_start", meta={"deploy_id": did, "kind": kind, "port": port})
    return {"ok": True, **rec}


def deploy_log_tail(deploy_id: str, lines: int = 80) -> Dict[str, Any]:
    p = _dpath(deploy_id)
    if not p.exists():
        return {"ok": False, "error": "not found"}
    rec = json.loads(p.read_text(encoding="utf-8"))
    log_path = rec.get("log_path")
    text = ""
    if log_path and Path(log_path).exists():
        raw = Path(log_path).read_text(encoding="utf-8", errors="replace")
        text = "\n".join(raw.splitlines()[-lines:])
    return {"ok": True, "id": deploy_id, "log_tail": text, "deploy": rec}


def stop_deploy(deploy_id: str) -> Dict[str, Any]:
    with _lock:
        entry = _servers.get(deploy_id)
        rec = None
        p = _dpath(deploy_id)
        if p.exists():
            try:
                rec = json.loads(p.read_text(encoding="utf-8"))
            except Exception:
                rec = {"id": deploy_id}
        if entry:
            if entry.get("type") == "static" and entry.get("httpd"):
                try:
                    entry["httpd"].shutdown()
                except Exception:
                    pass
            if entry.get("type") == "process" and entry.get("proc"):
                proc = entry["proc"]
                try:
                    proc.terminate()
                    proc.wait(timeout=4)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            if entry.get("log"):
                try:
                    entry["log"].close()
                except Exception:
                    pass
            _servers.pop(deploy_id, None)
        elif rec and rec.get("pid"):
            try:
                os.kill(int(rec["pid"]), 15)
            except Exception:
                pass
        if rec:
            rec["status"] = "stopped"
            rec["stopped_at"] = time.time()
            _save_deploy(rec)
            return {"ok": True, **rec}
    return {"ok": False, "error": "deploy not found"}


def workspace_tools(workspace: str = "workspace") -> Dict[str, Any]:
    cwd = resolve_cwd({"workspace": workspace})
    root = Path(cwd)
    files = []
    if root.is_dir():
        for i, f in enumerate(sorted(root.rglob("*"))):
            if i > 80:
                break
            if f.is_file() and f.stat().st_size < 2_000_000:
                files.append(str(f.relative_to(root)).replace("\\", "/"))
    has_pkg = (root / "package.json").exists()
    has_py = any(root.glob("*.py")) or (root / "pyproject.toml").exists()
    has_index = (root / "index.html").exists() or (root / "web" / "index.html").exists()
    return {
        "ok": True,
        "workspace": workspace,
        "path": str(root),
        "has_package_json": has_pkg,
        "has_python": has_py,
        "has_static_index": has_index,
        "sample_files": files[:40],
        "suggested_actions": [
            {"action": "deploy_static", "api": "POST /v1/deploy {kind:static}"},
            {"action": "deploy_npm", "api": "POST /v1/deploy {kind:npm}", "when": "package.json"},
            {"action": "deploy_python", "api": "POST /v1/deploy {kind:python}"},
            {"action": "term", "api": "POST /v1/terminals"},
            {"action": "codex_or_grok", "api": "POST /v1/sessions"},
        ],
        "platform_badge": "Powered by POCKET Multi-Agent Platform",
        "value": "Your Codex/Grok CLIs stay yours — POCKET orchestrates many of them + deploys + terminals.",
    }
