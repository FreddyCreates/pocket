"""POCKET Desktop — installable host product shell.

- Ensures local runtime (:8787)
- Opens desk in Edge app window (or pywebview if available)
- Optional system tray: Open · Studio · Status · Restart runtime · Quit
- Used by: python -m pocket desktop | Start-POCKET-Desktop.ps1 | installed shortcuts
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

PORT = int(os.environ.get("POCKET_PORT") or "8787")
HOST = os.environ.get("POCKET_HOST") or "127.0.0.1"
BASE = f"http://{HOST}:{PORT}"
ROOT = Path(__file__).resolve().parents[2]  # pocket-os/


def _port_open(host: str = HOST, port: int = PORT) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except OSError:
        return False


def _health_ok() -> bool:
    try:
        with urllib.request.urlopen(f"{BASE}/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def health_json() -> Dict[str, Any]:
    try:
        import json

        with urllib.request.urlopen(f"{BASE}/health", timeout=2) as r:
            return json.loads(r.read().decode("utf-8", errors="replace"))
    except Exception as e:
        return {"ok": False, "error": str(e)}


def ensure_server(*, wait_sec: float = 30.0) -> Dict[str, Any]:
    """Start host only if down. Never kill an existing healthy process."""
    if _port_open() or _health_ok():
        # Port already taken by a live host — do not spawn a second server
        return {"ok": True, "already": True, "url": BASE, "pid": None}

    src = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env["PYTHONPATH"] = str(src) + os.pathsep + env.get("PYTHONPATH", "")
    nexus = Path.home() / "OneDrive" / "nexus"
    if nexus.is_dir():
        env["PYTHONPATH"] = str(nexus) + os.pathsep + env["PYTHONPATH"]
        env["NEXUS_ROOT"] = str(nexus)
    if not env.get("POCKET_PUBLIC_URL"):
        env["POCKET_PUBLIC_URL"] = "https://pocket.medinatechlabs.net"

    creation = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if sys.platform == "win32" else 0
    log = Path.home() / ".pocket" / "desktop-serve.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    out_f = open(log, "a", encoding="utf-8", errors="replace")
    # Bind 0.0.0.0 so Cloudflare tunnel + LAN + Edge app all hit one host
    bind = os.environ.get("POCKET_BIND") or "0.0.0.0"
    proc = subprocess.Popen(
        [sys.executable, "-m", "pocket", "serve", "--host", bind, "--port", str(PORT)],
        cwd=str(src.parent),
        env=env,
        stdout=out_f,
        stderr=subprocess.STDOUT,
        creationflags=creation,
    )
    # stash pid
    pid_path = Path.home() / ".pocket" / "desktop-serve.pid"
    pid_path.write_text(str(proc.pid), encoding="utf-8")

    t0 = time.time()
    while time.time() - t0 < wait_sec:
        if _health_ok():
            return {"ok": True, "started": True, "pid": proc.pid, "url": BASE, "log": str(log)}
        if proc.poll() is not None:
            return {"ok": False, "error": "serve exited early", "pid": proc.pid, "log": str(log)}
        time.sleep(0.3)
    return {"ok": False, "error": "timeout waiting for health", "pid": proc.pid, "url": BASE}


def stop_server() -> Dict[str, Any]:
    """Best-effort stop of process holding :8787 and saved pid."""
    killed = []
    pid_path = Path.home() / ".pocket" / "desktop-serve.pid"
    if pid_path.exists():
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
            if sys.platform == "win32":
                subprocess.run(["taskkill", "/PID", str(pid), "/F", "/T"], capture_output=True)
            else:
                os.kill(pid, 15)
            killed.append(pid)
        except Exception:
            pass
        try:
            pid_path.unlink(missing_ok=True)
        except Exception:
            pass
    if sys.platform == "win32":
        try:
            ps = (
                "Get-NetTCPConnection -LocalPort %d -State Listen -EA SilentlyContinue | "
                "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -EA SilentlyContinue }"
                % PORT
            )
            subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=15)
        except Exception:
            pass
    return {"ok": True, "killed": killed, "listening": _port_open()}


def _edge_path() -> Optional[str]:
    for p in (
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
    ):
        if Path(p).is_file():
            return p
    return None


def open_edge_app(url: Optional[str] = None) -> bool:
    edge = _edge_path()
    if not edge:
        return False
    # Production default: desk surface (auth + splash + agents)
    target = url or f"{BASE}/desk"
    profile = Path.home() / ".pocket" / "desktop_profile"
    profile.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        [
            edge,
            f"--app={target}",
            f"--user-data-dir={str(profile)}",
            "--window-size=1440,920",
            "--disable-features=TranslateUI",
            "--new-window",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return True


def open_window(url: Optional[str] = None) -> Dict[str, Any]:
    target = url or f"{BASE}/desk"
    try:
        import webview  # type: ignore

        webview.create_window(
            "POCKET Desktop",
            target,
            width=1440,
            height=920,
            min_size=(960, 640),
            background_color="#050508",
        )
        webview.start()
        return {"ok": True, "mode": "pywebview", "url": target}
    except Exception as e:
        if open_edge_app(target):
            return {"ok": True, "mode": "edge_app", "url": target, "note": str(e)}
        import webbrowser

        webbrowser.open(target)
        return {"ok": True, "mode": "browser", "url": target, "note": str(e)}


def _tray_icon_image():
    from PIL import Image, ImageDraw

    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, 60, 60], radius=14, fill=(16, 185, 129, 255))
    d.rounded_rectangle([14, 14, 50, 50], radius=10, fill=(5, 46, 22, 255))
    d.text((22, 18), "P", fill=(52, 211, 153, 255))
    return img


def run_tray() -> int:
    """System tray controller — always available while you work."""
    try:
        import pystray
        from pystray import MenuItem as Item
    except ImportError:
        print("[POCKET Desktop] pystray missing — open window only", flush=True)
        boot = ensure_server()
        if not boot.get("ok"):
            print(boot, flush=True)
            return 1
        open_edge_app(f"{BASE}/")
        return 0

    print("[POCKET Desktop] ensuring runtime …", flush=True)
    boot = ensure_server()
    if not boot.get("ok"):
        print(f"[POCKET Desktop] runtime failed: {boot}", flush=True)
        # still show tray so user can retry
    else:
        open_edge_app(f"{BASE}/")

    state = {"icon": None}

    def _open(icon=None, item=None):
        ensure_server(wait_sec=15)
        open_edge_app(f"{BASE}/")

    def _studio(icon=None, item=None):
        ensure_server(wait_sec=15)
        open_edge_app(f"{BASE}/studio")

    def _status(icon=None, item=None):
        h = health_json()
        title = "POCKET · online" if h.get("ok") else "POCKET · offline"
        if state["icon"]:
            state["icon"].title = f"{title} · v{h.get('version', '?')}"
        print(h, flush=True)

    def _restart(icon=None, item=None):
        stop_server()
        time.sleep(1)
        r = ensure_server(wait_sec=25)
        print("restart", r, flush=True)
        if r.get("ok"):
            open_edge_app(f"{BASE}/")
        _status()

    def _quit(icon=None, item=None):
        # leave runtime running (always-on host); only quit tray
        if state["icon"]:
            state["icon"].stop()

    def _quit_stop(icon=None, item=None):
        stop_server()
        if state["icon"]:
            state["icon"].stop()

    menu = pystray.Menu(
        Item("Open POCKET Desk", _open, default=True),
        Item("Open Studio", _studio),
        Item("Status", _status),
        Item("Restart runtime", _restart),
        pystray.Menu.SEPARATOR,
        Item("Quit tray (keep runtime)", _quit),
        Item("Quit tray + stop runtime", _quit_stop),
    )
    icon = pystray.Icon("pocket", _tray_icon_image(), "POCKET Desktop", menu)
    state["icon"] = icon
    h = health_json()
    icon.title = "POCKET · online" if h.get("ok") else "POCKET · offline"
    print("[POCKET Desktop] tray ready — right-click the green P in the system tray", flush=True)
    icon.run()
    return 0


def run_desktop(*, tray: bool = True) -> int:
    """
    Default product entry: tray + open desk.
    Set POCKET_DESKTOP_NO_TRAY=1 for window-only (no tray loop).
    """
    if os.environ.get("POCKET_DESKTOP_NO_TRAY") == "1" or not tray:
        print(f"[POCKET Desktop] ensuring runtime on {BASE} …", flush=True)
        boot = ensure_server()
        if not boot.get("ok"):
            print(f"[POCKET Desktop] FAILED: {boot}", flush=True)
            return 1
        r = open_window()
        print(r, flush=True)
        return 0 if r.get("ok") else 1
    return run_tray()


if __name__ == "__main__":
    raise SystemExit(run_desktop())
