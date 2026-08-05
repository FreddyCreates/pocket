"""POCKET Native WSL Agent — first-class Linux-in-app hands.

Whole story:
  Windows host runs POCKET. WSL is the native Linux subsystem on that host.
  The WSL agent is not a toy shell tab — it is a first-class worker that:

  1. Probes distros, default, version, online status
  2. Owns a Linux workspace under the chosen distro (~/pocket-wsl)
  3. Accepts natural language + raw shell (with safety)
  4. Runs as mode ``wsl`` / ``wsl_native`` on the desk and phone
  5. Stays founder-host only on a shared operator PC (never market→founder WSL)

Market seats on someone else's host do NOT get that host's WSL.
Self-hosters are founders of *their* machine and get full WSL hands.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path.home() / ".pocket"
STATE = ROOT / "wsl_agent.json"
LOG = ROOT / "wsl_agent.log"
_lock = Lock()

# Commands that are never allowed through the agent (even founder)
BLOCK_RE = re.compile(
    r"(?i)("
    r"rm\s+-rf\s+/\s|rm\s+-rf\s+/\*|mkfs\.|dd\s+if=.*of=/dev/"
    r"|:\(\)\s*\{\s*:\|:&\s*\};:|"  # fork bomb
    r"curl\s+[^\n|]*\|\s*(ba)?sh|"
    r"wget\s+[^\n|]*\|\s*(ba)?sh|"
    r"chmod\s+-R\s+777\s+/|"
    r">\s*/etc/passwd|>\s*/etc/shadow|"
    r"shutdown\s|reboot\s|init\s+0|systemctl\s+poweroff"
    r")"
)

# Soft danger — require explicit "force:" prefix
SOFT_DANGER = re.compile(
    r"(?i)\b(rm\s+-rf|git\s+push\s+--force|drop\s+database|truncate\s+table)\b"
)

WORKSPACE_LINUX = "~/pocket-wsl"


def _log(msg: str) -> None:
    try:
        ROOT.mkdir(parents=True, exist_ok=True)
        with _lock:
            with LOG.open("a", encoding="utf-8") as f:
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")
    except Exception:
        pass


def which_wsl() -> str:
    return shutil.which("wsl") or shutil.which("wsl.exe") or ""


def _run_utf16(argv: List[str], timeout: float = 12) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            argv,
            capture_output=True,
            timeout=timeout,
            text=True,
            encoding="utf-16-le",
            errors="replace",
        )
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except FileNotFoundError:
        return 127, "", "wsl not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        return 1, "", str(e)


def _run_utf8(argv: List[str], timeout: float = 30) -> Tuple[int, str, str]:
    try:
        p = subprocess.run(
            argv,
            capture_output=True,
            timeout=timeout,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return p.returncode, (p.stdout or ""), (p.stderr or "")
    except FileNotFoundError:
        return 127, "", "wsl not found"
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except Exception as e:
        return 1, "", str(e)


def list_distros() -> List[Dict[str, Any]]:
    """Return installed distros (name, default flag)."""
    if not which_wsl():
        return []
    rc, out, _ = _run_utf16(["wsl", "-l", "-v"], timeout=10)
    # Fallback quiet list
    if rc != 0 or not out.strip():
        rc2, out2, _ = _run_utf16(["wsl", "-l", "-q"], timeout=8)
        names = [n.strip() for n in (out2 or "").splitlines() if n.strip()]
        return [{"name": n, "state": "Unknown", "version": "?", "default": i == 0} for i, n in enumerate(names)]

    rows: List[Dict[str, Any]] = []
    for line in (out or "").splitlines():
        raw = line.strip()
        if not raw or raw.lower().startswith("windows subsystem") or raw.lower().startswith("name"):
            continue
        default = raw.startswith("*")
        raw = raw.lstrip("*").strip()
        # NAME STATE VERSION
        parts = re.split(r"\s{2,}|\t+", raw)
        if not parts:
            continue
        name = parts[0].strip()
        if not name or name.lower() == "docker":
            # still include docker-desktop if present — skip only empty
            pass
        state = parts[1].strip() if len(parts) > 1 else "Unknown"
        ver = parts[2].strip() if len(parts) > 2 else "?"
        if name:
            rows.append({"name": name, "state": state, "version": ver, "default": default})
    return rows


def pick_distro(preferred: str = "") -> str:
    distros = list_distros()
    if preferred:
        for d in distros:
            if d["name"].lower() == preferred.lower():
                return d["name"]
    for d in distros:
        if d.get("default"):
            return d["name"]
    # Prefer Debian/Ubuntu for agent work
    for want in ("Debian", "Ubuntu", "Ubuntu-24.04", "Ubuntu-22.04"):
        for d in distros:
            if d["name"].lower() == want.lower() or d["name"].lower().startswith(want.lower()):
                return d["name"]
    return distros[0]["name"] if distros else ""


def _load_state() -> Dict[str, Any]:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "distro": "",
        "cwd": WORKSPACE_LINUX,
        "runs": 0,
        "last_at": 0,
        "last_cmd": "",
        "online": False,
    }


def _save_state(st: Dict[str, Any]) -> None:
    try:
        ROOT.mkdir(parents=True, exist_ok=True)
        STATE.write_text(json.dumps(st, indent=2), encoding="utf-8")
    except Exception:
        pass


def probe() -> Dict[str, Any]:
    """Full WSL health story for UI + API."""
    wsl = which_wsl()
    distros = list_distros() if wsl else []
    st = _load_state()
    default = pick_distro(st.get("distro") or "")
    online = False
    uname = ""
    if wsl and default:
        rc, out, err = _run_utf8(
            ["wsl", "-d", default, "--", "bash", "-lc", "uname -a && echo '---' && pwd && whoami"],
            timeout=15,
        )
        online = rc == 0
        uname = (out or err or "").strip()[:500]
    story = {
        "ok": bool(wsl),
        "schema": "pocket.wsl.v1",
        "installed": bool(wsl),
        "wsl_path": wsl or None,
        "distros": distros,
        "default_distro": default or None,
        "online": online,
        "workspace_linux": WORKSPACE_LINUX,
        "state": {
            "distro": st.get("distro") or default,
            "cwd": st.get("cwd") or WORKSPACE_LINUX,
            "runs": int(st.get("runs") or 0),
            "last_at": st.get("last_at") or 0,
        },
        "probe": uname,
        "first_class": True,
        "host_only": True,
        "story": (
            "WSL is POCKET's native Linux hands on this Windows host. "
            "Agents plan, build, and test inside a real distro workspace "
            f"({WORKSPACE_LINUX}) without leaving the desk."
        ),
        "modes": ["wsl", "wsl_native"],
        "safety": {
            "block_destructive_root": True,
            "soft_danger_needs_force": True,
            "market_on_shared_host": "denied — founder/host only",
        },
    }
    return story


def ensure_workspace(distro: str = "") -> Dict[str, Any]:
    """Create ~/pocket-wsl tree inside the distro."""
    d = pick_distro(distro)
    if not d:
        return {"ok": False, "error": "No WSL distro installed. Install Debian/Ubuntu from Microsoft Store."}
    script = (
        f"mkdir -p {WORKSPACE_LINUX}/{{src,build,notes,proofs}} && "
        f"cd {WORKSPACE_LINUX} && "
        f"if [ ! -f README.md ]; then "
        f"printf '%s\\n' '# POCKET WSL workspace' '' "
        f"'Native Linux hands for the POCKET desk.' "
        f"'Created by wsl_agent — first-class host agent.' > README.md; fi && "
        f"pwd && ls -la"
    )
    rc, out, err = _run_utf8(["wsl", "-d", d, "--", "bash", "-lc", script], timeout=30)
    st = _load_state()
    st["distro"] = d
    st["cwd"] = WORKSPACE_LINUX
    st["online"] = rc == 0
    st["last_at"] = time.time()
    _save_state(st)
    return {
        "ok": rc == 0,
        "distro": d,
        "workspace": WORKSPACE_LINUX,
        "output": (out or err or "").strip()[-8000:],
        "error": "" if rc == 0 else (err or f"exit {rc}"),
    }


def safety_check(cmd: str) -> Tuple[bool, str]:
    c = (cmd or "").strip()
    if not c:
        return False, "empty command"
    if len(c) > 12000:
        return False, "command too long"
    if BLOCK_RE.search(c):
        return False, "blocked by WSL safety policy (destructive / pipe-to-shell / power)"
    if SOFT_DANGER.search(c) and not c.lower().startswith("force:"):
        return False, "soft-danger command — prefix with 'force:' to confirm (e.g. force: rm -rf ./build)"
    return True, "ok"


def interpret_prompt(prompt: str) -> str:
    """Turn natural language into a bash -lc script when not raw shell."""
    p = (prompt or "").strip()
    if not p:
        return "echo 'empty'"
    # strip force: for interpretation but keep for safety_check on final
    raw = p
    force = False
    if p.lower().startswith("force:"):
        force = True
        p = p[6:].strip()

    low = p.lower()

    # Explicit shell markers
    if low.startswith("!") or low.startswith("$ ") or low.startswith("run:"):
        cmd = p.lstrip("!$ ").strip()
        if low.startswith("run:"):
            cmd = p[4:].strip()
        return ("force: " if force else "") + cmd

    # Natural language recipes
    if low in ("help", "?", "status", "probe"):
        return (
            "echo '=== POCKET WSL agent ===' && uname -a && echo && "
            f"echo workspace={WORKSPACE_LINUX} && cd {WORKSPACE_LINUX} 2>/dev/null; "
            "pwd; ls -la; echo; which python3 node npm git cargo rustc 2>/dev/null; "
            "echo done"
        )
    if low.startswith("cd ") and "&&" not in low and ";" not in low:
        path = p[3:].strip()
        return f"cd {path} && pwd && ls -la"
    if any(low.startswith(x) for x in ("ls", "pwd", "cat ", "head ", "tail ", "git ", "python", "pip", "npm", "node", "cargo", "make", "cmake", "apt", "sudo ")):
        return ("force: " if force else "") + p

    # NL → structured plan+act
    safe = p.replace("'", "'\\''")
    return (
        f"cd {WORKSPACE_LINUX} 2>/dev/null || mkdir -p {WORKSPACE_LINUX} && cd {WORKSPACE_LINUX}; "
        f"echo '## WSL agent task'; echo '{safe}'; echo; "
        f"# Heuristic: show context then attempt common research steps\n"
        f"pwd; ls -la; echo; "
        f"if echo '{safe}' | grep -qiE 'install|setup|deps'; then "
        f"  echo '(install intent — dry-run) show package managers:'; which apt-get apk dnf yum 2>/dev/null; "
        f"elif echo '{safe}' | grep -qiE 'test|pytest|npm test'; then "
        f"  (test -f package.json && npm test --silent) || (test -f pyproject.toml && python3 -m pytest -q) || echo 'no test runner detected'; "
        f"elif echo '{safe}' | grep -qiE 'build|compile'; then "
        f"  (test -f package.json && npm run build) || (test -f Makefile && make) || echo 'no build recipe'; "
        f"else "
        f"  echo 'Context ready. Run explicit shell with: ! command   or   run: command'; "
        f"  echo 'Examples: ! ls -la   |   run: git status   |   status'; "
        f"fi"
    )


def run_wsl(
    prompt: str,
    *,
    distro: str = "",
    cwd: str = "",
    job_id: str = "",
    timeout: int = 300,
) -> Tuple[str, str, str]:
    """Execute one WSL agent turn. Returns (stdout, error, engine)."""
    if not which_wsl():
        return (
            "",
            "WSL not installed. Install from Microsoft Store (Debian or Ubuntu recommended), "
            "then run `wsl --install` if needed and reopen POCKET.",
            "wsl",
        )

    d = pick_distro(distro or _load_state().get("distro") or "")
    if not d:
        return "", "No WSL distro found. Install Debian/Ubuntu.", "wsl"

    # Ensure workspace once
    ensure_workspace(d)

    script_body = interpret_prompt(prompt)
    ok, why = safety_check(script_body)
    if not ok:
        _log(f"blocked distro={d} why={why} prompt={prompt[:120]}")
        return "", why, "wsl"

    if script_body.lower().startswith("force:"):
        script_body = script_body[6:].strip()

    work = (cwd or _load_state().get("cwd") or WORKSPACE_LINUX).strip() or WORKSPACE_LINUX
    # Stay inside home-ish paths — block absolute host mounts abuse lightly
    if work.startswith("/mnt/c/Users") and ".." in work:
        return "", "refusing unsafe cwd", "wsl"

    full = f"cd {work} 2>/dev/null || cd {WORKSPACE_LINUX} 2>/dev/null || true; {script_body}"
    argv = ["wsl", "-d", d, "--", "bash", "-lc", full]

    from pocket.stream_util import run_streaming

    out, rc, err = run_streaming(argv, job_id=job_id, timeout=timeout, engine="wsl")
    out = (out or "").strip()[-50000:]

    st = _load_state()
    st["distro"] = d
    st["cwd"] = work
    st["runs"] = int(st.get("runs") or 0) + 1
    st["last_at"] = time.time()
    st["last_cmd"] = (prompt or "")[:300]
    st["online"] = True
    _save_state(st)
    _log(f"run distro={d} rc={rc} job={job_id} chars={len(out)}")

    header = (
        f"[WSL native · distro={d} · cwd={work} · rc={rc}]\n"
        f"{'—' * 40}\n"
    )
    if err and not out:
        return header, err, "wsl"
    if rc != 0:
        return header + (out or f"(exit {rc})"), err or f"wsl exit {rc}", "wsl"
    return header + (out or "(no output)"), "", "wsl"


def run_wsl_job(prompt: str, *, cwd: str = "", job: Optional[Dict[str, Any]] = None) -> Tuple[str, str, str]:
    job = job or {}
    return run_wsl(
        prompt,
        distro=str(job.get("wsl_distro") or job.get("distro") or ""),
        cwd=cwd or str(job.get("wsl_cwd") or ""),
        job_id=str(job.get("id") or ""),
        timeout=int(job.get("timeout") or 300),
    )


def status() -> Dict[str, Any]:
    return probe()
