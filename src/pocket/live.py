"""Live service probes + best-effort auto-connect for suite products."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

# Services we can show / try to start on this PC
SERVICES: List[Dict[str, Any]] = [
    {
        "id": "pocket",
        "name": "POCKET console",
        "port": 8787,
        "health": "http://127.0.0.1:8787/health",
        "url": "http://127.0.0.1:8787/",
        "kind": "self",
    },
    {
        "id": "hz",
        "name": "HZ Hub",
        "port": 8765,
        "health": "http://127.0.0.1:8765/health",
        "url": "http://127.0.0.1:8765/",
        "kind": "start",
        "cwd": str(Path.home() / "OneDrive" / "hz-offline"),
        "env_pythonpath": str(Path.home() / "OneDrive" / "hz-offline" / "src"),
        "cmd": ["python", "-m", "hz", "hub", "--host", "0.0.0.0", "--port", "8765"],
    },
    {
        "id": "board",
        "name": "Suite board",
        "port": 8700,
        "health": "http://127.0.0.1:8700/health",
        "url": "http://127.0.0.1:8700/",
        "kind": "start",
        "cwd": str(Path.home() / "OneDrive" / "suite-board"),
        "cmd": ["python", str(Path.home() / "OneDrive" / "suite-board" / "board.py")],
    },
    {
        "id": "mb",
        "name": "MonadBuilder web",
        "port": 5174,
        "health": "http://127.0.0.1:5174/",
        "url": "http://127.0.0.1:5174/",
        "kind": "info",
        "note": "Start: npm run dev in Monad-Hackaton/web",
    },
    {
        "id": "wsl",
        "name": "WSL Debian",
        "port": None,
        "health": None,
        "kind": "probe_wsl",
        "note": "Local Linux terminals inside POCKET",
    },
    {
        "id": "codex",
        "name": "Codex CLI",
        "port": None,
        "health": None,
        "kind": "probe_bin",
        "bin": "codex",
    },
    {
        "id": "claude",
        "name": "Claude CLI",
        "port": None,
        "health": None,
        "kind": "probe_bin",
        "bin": "claude",
    },
    {
        "id": "cloudflared",
        "name": "Cloudflare tunnel",
        "port": None,
        "health": None,
        "kind": "probe_bin",
        "bin": "cloudflared",
        "note": "Use scripts/Start-POCKET-Cloudflare.ps1 for public URL",
    },
]


def lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def _http_ok(url: str, timeout: float = 1.8) -> Dict[str, Any]:
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return {"ok": True, "code": r.status}
    except urllib.error.HTTPError as e:
        return {"ok": e.code < 500, "code": e.code}
    except Exception as e:
        return {"ok": False, "error": str(e)[:120]}


def _which(name: str) -> Optional[str]:
    import shutil

    return shutil.which(name)


def _wsl_ok() -> Dict[str, Any]:
    try:
        p = subprocess.run(
            ["wsl", "-l", "-v"],
            capture_output=True,
            timeout=8,
            text=True,
            encoding="utf-16-le",
            errors="replace",
        )
        out = (p.stdout or "") + (p.stderr or "")
        running = "Running" in out
        return {"ok": running or p.returncode == 0, "detail": out[:400], "running": running}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def probe_all() -> Dict[str, Any]:
    items = []
    live = 0
    for s in SERVICES:
        entry = {
            "id": s["id"],
            "name": s["name"],
            "url": s.get("url"),
            "note": s.get("note"),
            "connectable": s.get("kind") == "start",
            "kind": s.get("kind"),
        }
        kind = s.get("kind")
        if kind in ("self", "start", "info") and s.get("health"):
            h = _http_ok(s["health"])
            entry["live"] = bool(h.get("ok"))
            entry["detail"] = h
        elif kind == "probe_wsl":
            h = _wsl_ok()
            entry["live"] = bool(h.get("ok"))
            entry["detail"] = h
        elif kind == "probe_bin":
            path = _which(s.get("bin") or "")
            entry["live"] = bool(path)
            entry["detail"] = {"path": path}
        else:
            entry["live"] = False
            entry["detail"] = {}
        if entry["live"]:
            live += 1
        items.append(entry)

    ip = lan_ip()
    return {
        "ok": True,
        "lan_ip": ip,
        "live_count": live,
        "services": items,
        "phone_urls": {
            "pocket": f"http://{ip}:8787/",
            "hz": f"http://{ip}:8765/",
            "board": f"http://{ip}:8700/",
        },
        "public_url": (os.environ.get("POCKET_PUBLIC_URL") or "").strip() or None,
    }


def connect_service(service_id: str) -> Dict[str, Any]:
    """Best-effort start for disconnected startable services."""
    svc = next((s for s in SERVICES if s["id"] == service_id), None)
    if not svc:
        return {"ok": False, "error": "unknown service"}
    if svc.get("kind") != "start":
        return {
            "ok": False,
            "error": "not auto-startable",
            "hint": svc.get("note") or "Start this service manually",
        }
    # already live?
    if svc.get("health"):
        h = _http_ok(svc["health"])
        if h.get("ok"):
            return {"ok": True, "already": True, "service": service_id}

    cwd = svc.get("cwd") or None
    cmd = list(svc.get("cmd") or [])
    env = os.environ.copy()
    if svc.get("env_pythonpath"):
        env["PYTHONPATH"] = svc["env_pythonpath"] + os.pathsep + env.get("PYTHONPATH", "")
    try:
        # Detached start on Windows
        flags = 0
        if os.name == "nt":
            flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP  # type: ignore
            subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
            )
        else:
            subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        return {"ok": True, "started": True, "service": service_id, "cmd": cmd}
    except Exception as e:
        return {"ok": False, "error": str(e), "service": service_id}


def connect_all_down() -> Dict[str, Any]:
    st = probe_all()
    results = []
    for s in st["services"]:
        if s.get("connectable") and not s.get("live"):
            results.append(connect_service(s["id"]))
    return {"ok": True, "actions": results, "after": probe_all()}
