"""Auro14B / RO14B native LMR bridge for POCKET.

Ships the user's native runtime (auro_native_llm), not a third-party API model.
Silent continual training: background tick is opt-in via POCKET_AURO_TRAIN=1
and never shown as a chat product surface.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

_AURO_ROOTS = [
    os.environ.get("AURO14B_ROOT"),
    os.environ.get("POCKET_AURO_ROOT"),
    str(Path.home() / "Documents" / "GitHub" / "Auro14B"),
    r"C:\Users\Medin\Documents\GitHub\Auro14B",
]

_DEFAULT_CKPT = "checkpoints/auro_minds/Auro-2B_physics"
_train_thread: Optional[threading.Thread] = None
_train_stop = threading.Event()
_train_state: Dict[str, Any] = {"ticks": 0, "last": None, "errors": []}


def auro_root() -> Optional[Path]:
    for r in _AURO_ROOTS:
        if not r:
            continue
        p = Path(r)
        if p.is_dir() and (p / "auro_native_llm").is_dir():
            return p.resolve()
    return None


def checkpoint_path() -> Optional[Path]:
    env = os.environ.get("POCKET_AURO_CKPT")
    root = auro_root()
    if not root:
        return None
    if env:
        p = Path(env)
        if not p.is_absolute():
            p = root / env
        return p if p.exists() else root / _DEFAULT_CKPT
    # prefer physics then base Auro-2B
    for rel in (
        _DEFAULT_CKPT,
        "checkpoints/auro_minds/Auro-2B",
        "checkpoints/auro_minds/Auro-2B_continual",
    ):
        p = root / rel
        if p.exists():
            return p
    return root / _DEFAULT_CKPT


def status() -> Dict[str, Any]:
    root = auro_root()
    ckpt = checkpoint_path()
    return {
        "ok": root is not None,
        "product": "Auro14B / RO14B native LMR",
        "repo": "https://github.com/ItsNotAILABS/Auro14B",
        "root": str(root) if root else None,
        "checkpoint": str(ckpt) if ckpt else None,
        "checkpoint_exists": bool(ckpt and ckpt.exists()),
        "family": "Auro-2B live cores → Auro-14B architecture target",
        "ui_visible": False,  # silent training not a product surface
        "train_silent": os.environ.get("POCKET_AURO_TRAIN", "0") in ("1", "true", "yes"),
        "train_state": dict(_train_state),
        "use": "Session mode auro / ro14b · python -m auro_native_llm.use --resume <ckpt>",
    }


def _ensure_path(root: Path) -> None:
    s = str(root)
    if s not in sys.path:
        sys.path.insert(0, s)


def try_generate(prompt: str, *, max_tokens: int = 128) -> Dict[str, Any]:
    """One-shot native use if runtime loads; otherwise status-only."""
    root = auro_root()
    ckpt = checkpoint_path()
    if not root:
        return {"ok": False, "error": "Auro14B root not found", **status()}
    _ensure_path(root)
    prompt = (prompt or "What is MESIE?").strip()
    # Prefer subprocess isolation so train deps don't crash host
    import subprocess

    cmd = [
        sys.executable,
        "-m",
        "auro_native_llm.use",
        "--resume",
        str(ckpt) if ckpt else _DEFAULT_CKPT,
        prompt[:500],
    ]
    try:
        r = subprocess.run(
            cmd,
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "PYTHONPATH": str(root) + os.pathsep + os.environ.get("PYTHONPATH", "")},
        )
        out = (r.stdout or "")[-4000:]
        err = (r.stderr or "")[-1500:]
        return {
            "ok": r.returncode == 0,
            "stdout": out,
            "stderr": err,
            "checkpoint": str(ckpt),
            "returncode": r.returncode,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "checkpoint": str(ckpt)}


def run_auro_job(prompt: str) -> Tuple[str, str, str]:
    st = status()
    lines = [
        "# Auro14B · native LMR\n\n",
        f"**Root:** `{st.get('root')}`\n",
        f"**Checkpoint:** `{st.get('checkpoint')}` exists={st.get('checkpoint_exists')}\n",
        f"**Family:** {st.get('family')}\n\n",
        f"## Prompt\n{prompt or '(status)'}\n\n",
    ]
    if not st.get("ok"):
        return "".join(lines), "Auro14B not found", "auro"
    low = (prompt or "").lower()
    if low in ("", "status", "help", "who"):
        lines.append("Use a real question to run `auro_native_llm.use` once.\n")
        return "".join(lines), "", "auro"
    gen = try_generate(prompt)
    if gen.get("ok"):
        lines.append("## Native output\n```\n")
        lines.append(gen.get("stdout") or "")
        lines.append("\n```\n")
        return "".join(lines), "", "auro"
    lines.append(f"## Run note\n`{gen.get('error') or gen.get('stderr') or 'failed'}`\n")
    if gen.get("stdout"):
        lines.append("```\n" + gen["stdout"][:2000] + "\n```\n")
    return "".join(lines), gen.get("error") or "auro run incomplete", "auro"


def _silent_train_tick() -> None:
    """Background: record a silent train heartbeat — no UI surface.

    Full weight training stays in Auro14B train scripts; POCKET only keeps
    the loop warm and logs receipts under ~/.pocket/auro_train/.
    """
    root = auro_root()
    if not root:
        return
    out_dir = Path.home() / ".pocket" / "auro_train"
    out_dir.mkdir(parents=True, exist_ok=True)
    ckpt = checkpoint_path()
    note = (
        f"tick={_train_state['ticks']} at={time.time()} "
        f"ckpt={ckpt} root={root}\n"
    )
    (out_dir / "silent_ticks.log").open("a", encoding="utf-8").write(note)
    _train_state["last"] = time.time()
    _train_state["ticks"] = int(_train_state.get("ticks") or 0) + 1
    # Optional: call auro light continual if module present (best-effort)
    try:
        _ensure_path(root)
        # do not import heavy trainers by default
    except Exception as e:
        _train_state.setdefault("errors", []).append(str(e)[:200])


def start_silent_training(*, interval_sec: float = 600.0) -> Dict[str, Any]:
    global _train_thread
    if os.environ.get("POCKET_AURO_TRAIN", "0") not in ("1", "true", "yes"):
        return {"ok": True, "started": False, "reason": "POCKET_AURO_TRAIN not set"}
    if _train_thread and _train_thread.is_alive():
        return {"ok": True, "already": True, "state": _train_state}
    _train_stop.clear()

    def loop():
        while not _train_stop.is_set():
            try:
                _silent_train_tick()
            except Exception as e:
                _train_state.setdefault("errors", []).append(str(e)[:200])
            _train_stop.wait(interval_sec)

    _train_thread = threading.Thread(target=loop, name="pocket-auro-silent", daemon=True)
    _train_thread.start()
    return {"ok": True, "started": True, "interval_sec": interval_sec, "ui_visible": False}


def stop_silent_training() -> Dict[str, Any]:
    _train_stop.set()
    return {"ok": True, "stopped": True}
