"""Learning loop — every real run can mint/update skills for workers.

Stores under ~/.pocket/learned_skills/ so the platform improves over time.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "learned_skills"
ROOT.mkdir(parents=True, exist_ok=True)
INDEX = ROOT / "index.json"


def _load_index() -> Dict[str, Any]:
    if INDEX.exists():
        try:
            return json.loads(INDEX.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"skills": [], "runs": 0}


def _save_index(data: Dict[str, Any]) -> None:
    INDEX.write_text(json.dumps(data, indent=2, default=str)[:200000], encoding="utf-8")


def record_run(
    *,
    name: str,
    steps: List[Dict[str, Any]],
    notes: str = "",
    worker: str = "ARCHON",
) -> Dict[str, Any]:
    """Persist a run as a reusable learned skill definition."""
    sid = f"learned_{int(time.time())}_{name[:40].replace(' ', '_')}"
    path = ROOT / f"{sid}.json"
    rec = {
        "id": sid,
        "name": name,
        "worker": worker,
        "created_at": time.time(),
        "notes": notes,
        "steps": steps,
        "source": "live_run",
    }
    path.write_text(json.dumps(rec, indent=2, default=str), encoding="utf-8")
    idx = _load_index()
    idx["skills"] = (idx.get("skills") or [])[-80:]
    idx["skills"].append({"id": sid, "name": name, "path": str(path), "at": rec["created_at"]})
    idx["runs"] = int(idx.get("runs") or 0) + 1
    _save_index(idx)
    emit("learn", f"Learned skill {sid}: {name}", agent=worker, role="python")
    return rec


def list_learned() -> List[Dict[str, Any]]:
    return _load_index().get("skills") or []
