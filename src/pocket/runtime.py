"""POCKET full Python runtime — start, watch, restart. No toy cmd loops.

Usage:
  python -m pocket runtime
  python -m pocket runtime --once   # serve only, no watchdog
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
HOME = Path.home() / ".pocket"
LOG = HOME / "runtime.log"
PY = sys.executable
PORT = int(os.environ.get("POCKET_PORT", "8787"))
HOST = os.environ.get("POCKET_HOST", "0.0.0.0")


def _log(msg: str) -> None:
    HOME.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _load_env_file() -> None:
    for path in (HOME / "access.env", ROOT / ".pocket" / "access.env"):
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k and k not in os.environ:
                os.environ[k] = v
    # NEXUS product path
    nexus = Path(os.environ.get("NEXUS_ROOT") or (Path.home() / "OneDrive" / "nexus"))
    os.environ.setdefault("NEXUS_ROOT", str(nexus))
    os.environ.setdefault("POCKET_PUBLIC_URL", "https://pocket.medinatechlabs.net")
    parts = [str(SRC), str(nexus)]
    prev = os.environ.get("PYTHONPATH", "")
    if prev:
        parts.append(prev)
    os.environ["PYTHONPATH"] = os.pathsep.join(parts)
    # Load nexus .env (GITHUB_TOKEN etc.)
    nx_env = nexus / ".env"
    if nx_env.exists():
        for raw in nx_env.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k and k not in os.environ:
                os.environ[k] = v


def health_ok() -> bool:
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{PORT}/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as r:
            body = r.read().decode("utf-8", errors="replace")
            return r.status == 200 and "ok" in body
    except Exception:
        return False


def start_server() -> subprocess.Popen:
    env = os.environ.copy()
    nexus = env.get("NEXUS_ROOT") or str(Path.home() / "OneDrive" / "nexus")
    env["NEXUS_ROOT"] = nexus
    env["PYTHONPATH"] = os.pathsep.join(
        [str(SRC), nexus, env.get("PYTHONPATH", "")]
    )
    env["POCKET_PUBLIC_URL"] = env.get("POCKET_PUBLIC_URL") or "https://pocket.medinatechlabs.net"
    # Ensure grok CLI on PATH for product agent mode
    grok_bin = str(Path.home() / ".grok" / "bin")
    env["Path"] = grok_bin + os.pathsep + env.get("Path", env.get("PATH", ""))
    log_f = open(HOME / "pocket-serve.log", "a", encoding="utf-8", errors="replace")
    log_f.write(f"\n--- runtime start {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
    log_f.flush()
    p = subprocess.Popen(
        [PY, "-u", "-m", "pocket", "serve", "--host", HOST, "--port", str(PORT)],
        cwd=str(ROOT),
        env=env,
        stdout=log_f,
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0,  # type: ignore
    )
    _log(f"started pocket pid={p.pid} py={PY}")
    return p


def run_watchdog(poll: float = 12.0) -> None:
    _load_env_file()
    # Ensure auth material exists
    try:
        from pocket.auth import load_basic_auth

        a = load_basic_auth()
        _log(f"auth user={a.user} file={a.source}")
    except Exception as e:
        _log(f"auth load warn: {e}")

    _log("=" * 50)
    _log("POCKET Python Runtime (watchdog)")
    _log(f"  python: {PY}")
    _log(f"  root:   {ROOT}")
    _log(f"  local:  http://127.0.0.1:{PORT}/")
    _log(f"  public: {os.environ.get('POCKET_PUBLIC_URL')}")
    _log(f"  log:    {LOG}")
    _log("=" * 50)

    proc: subprocess.Popen | None = None
    if not health_ok():
        proc = start_server()
        time.sleep(3)

    while True:
        try:
            if health_ok():
                time.sleep(poll)
                continue
            _log("health FAIL — restarting serve")
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=4)
                except Exception:
                    try:
                        proc.kill()
                    except Exception:
                        pass
            # Only reclaim our own python serve children — never kill IDE/other apps on the port
            if os.name == "nt":
                try:
                    ps = (
                        f"$p=Get-CimInstance Win32_Process | Where-Object "
                        f"{{ $_.Name -match 'python' -and $_.CommandLine -match 'pocket' "
                        f"-and $_.CommandLine -match 'serve' }}; "
                        f"if($p){{ $p | ForEach-Object {{ Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }} }}"
                    )
                    subprocess.run(
                        ["powershell", "-NoProfile", "-Command", ps],
                        capture_output=True,
                        timeout=15,
                    )
                except Exception as e:
                    _log(f"port reclaim warn: {e}")
            time.sleep(1)
            proc = start_server()
            time.sleep(4)
            if health_ok():
                _log("restart OK")
            else:
                _log("restart still failing — see pocket-serve.log")
        except KeyboardInterrupt:
            _log("runtime stop")
            if proc and proc.poll() is None:
                proc.terminate()
            break
        except Exception as e:
            _log(f"watchdog error: {e}")
            time.sleep(5)


def main(argv: list | None = None) -> None:
    args = list(argv or sys.argv[1:])
    if "--once" in args:
        _load_env_file()
        from pocket.server import serve

        serve(HOST, PORT)
        return
    run_watchdog()


if __name__ == "__main__":
    main()
