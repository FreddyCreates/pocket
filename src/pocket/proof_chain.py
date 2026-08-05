"""Proof chain — local hash-linked receipts for work that happened.

Not a blockchain product — a lab ledger you can show: dreams, duels, ships, capsules.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket" / "proofs"
ROOT.mkdir(parents=True, exist_ok=True)
CHAIN = ROOT / "chain.jsonl"
HEAD = ROOT / "HEAD"


def _last_hash() -> str:
    if HEAD.exists():
        try:
            return HEAD.read_text(encoding="utf-8").strip()
        except Exception:
            pass
    if CHAIN.exists():
        lines = CHAIN.read_text(encoding="utf-8", errors="replace").splitlines()
        if lines:
            try:
                return json.loads(lines[-1]).get("hash") or "genesis"
            except Exception:
                pass
    return "genesis"


def mint_receipt(kind: str, summary: str, *, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    prev = _last_hash()
    rid = f"rcpt-{uuid.uuid4().hex[:12]}"
    body = {
        "id": rid,
        "at": time.time(),
        "kind": (kind or "work")[:40],
        "summary": (summary or "")[:500],
        "meta": meta or {},
        "prev": prev,
    }
    payload = json.dumps(body, sort_keys=True, default=str)
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    body["hash"] = h
    with CHAIN.open("a", encoding="utf-8") as f:
        f.write(json.dumps(body, default=str) + "\n")
    HEAD.write_text(h, encoding="utf-8")
    # human card
    card = ROOT / f"{rid}.md"
    card.write_text(
        f"# Receipt `{rid}`\n\n"
        f"**Kind:** {body['kind']}\n"
        f"**When:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(body['at']))}\n"
        f"**Summary:** {body['summary']}\n\n"
        f"**Hash:** `{h}`\n"
        f"**Prev:** `{prev}`\n",
        encoding="utf-8",
    )
    return {"ok": True, "id": rid, "hash": h, "prev": prev, "card": str(card)}


def list_receipts(limit: int = 25) -> List[Dict[str, Any]]:
    if not CHAIN.exists():
        return []
    lines = CHAIN.read_text(encoding="utf-8", errors="replace").splitlines()
    out = []
    for ln in reversed(lines[-200:]):
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def verify_chain() -> Dict[str, Any]:
    if not CHAIN.exists():
        return {"ok": True, "length": 0, "valid": True}
    lines = CHAIN.read_text(encoding="utf-8", errors="replace").splitlines()
    prev = "genesis"
    bad = []
    for i, ln in enumerate(lines):
        try:
            rec = json.loads(ln)
        except Exception:
            bad.append({"i": i, "error": "json"})
            continue
        if rec.get("prev") != prev:
            bad.append({"i": i, "id": rec.get("id"), "error": "prev mismatch", "expected": prev})
        body = {k: rec[k] for k in ("id", "at", "kind", "summary", "meta", "prev") if k in rec}
        payload = json.dumps(body, sort_keys=True, default=str)
        h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if h != rec.get("hash"):
            bad.append({"i": i, "id": rec.get("id"), "error": "hash mismatch"})
        prev = rec.get("hash") or prev
    return {
        "ok": len(bad) == 0,
        "valid": len(bad) == 0,
        "length": len(lines),
        "head": prev,
        "errors": bad[:20],
    }


def status() -> Dict[str, Any]:
    v = verify_chain()
    return {
        "ok": True,
        "schema": "pocket.proof.v1",
        "length": v.get("length"),
        "valid": v.get("valid"),
        "head": v.get("head"),
        "recent": list_receipts(5),
    }
