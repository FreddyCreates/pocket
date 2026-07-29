"""Lightweight agent task market on top of the hashed mesh bus.

Agents post claims; peers leave artifacts. Complements offload_queue.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket" / "task_market"
ROOT.mkdir(parents=True, exist_ok=True)
BOARD = ROOT / "board.jsonl"


def post_task(
    title: str,
    *,
    body: str = "",
    from_agent: str = "GROK",
    reward_note: str = "skill_memory+bus_credit",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    tid = f"mkt-{uuid.uuid4().hex[:10]}"
    rec = {
        "id": tid,
        "title": (title or "")[:200],
        "body": (body or "")[:4000],
        "from": (from_agent or "AI").upper(),
        "status": "open",
        "tags": tags or ["embodiment", "coding"],
        "reward_note": reward_note,
        "created_at": time.time(),
        "claimed_by": None,
        "claim_at": None,
    }
    with BOARD.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    try:
        from pocket.mesh_disk import send_message

        send_message(
            rec["from"],
            "CODEX",
            f"market task {tid}: {rec['title']}",
            channel="freq-coding",
            kind="market",
        )
        send_message(
            rec["from"],
            "ARCHON",
            f"market open {tid}: {rec['title']}",
            channel="freq-coding",
            kind="market",
        )
    except Exception:
        pass
    return {"ok": True, "task": rec}


def list_open(*, limit: int = 30) -> List[Dict[str, Any]]:
    if not BOARD.exists():
        return []
    items = []
    for ln in BOARD.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            items.append(json.loads(ln))
        except Exception:
            continue
    open_ = [t for t in items if t.get("status") == "open"]
    return list(reversed(open_[-limit:]))


def claim(tid: str, agent: str = "CODEX") -> Dict[str, Any]:
    if not BOARD.exists():
        return {"ok": False, "error": "empty board"}
    lines = BOARD.read_text(encoding="utf-8", errors="replace").splitlines()
    out: List[str] = []
    found = None
    for ln in lines:
        try:
            t = json.loads(ln)
        except Exception:
            out.append(ln)
            continue
        if t.get("id") == tid and t.get("status") == "open":
            t["status"] = "claimed"
            t["claimed_by"] = (agent or "AI").upper()
            t["claim_at"] = time.time()
            found = t
        out.append(json.dumps(t))
    BOARD.write_text("\n".join(out) + ("\n" if out else ""), encoding="utf-8")
    if not found:
        return {"ok": False, "error": "not open or missing"}
    try:
        from pocket.mesh_disk import send_message

        send_message(
            found["claimed_by"],
            found.get("from") or "GROK",
            f"claimed {tid}: {found.get('title')}",
            channel="freq-coding",
            kind="claim",
        )
    except Exception:
        pass
    return {"ok": True, "task": found}
