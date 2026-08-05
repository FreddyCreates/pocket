"""Dream Mode — POCKET sleeps with one eye open.

While the human is idle, Subcortex consolidates:
  - Infinite Wiki reindex ticks
  - World-model brief on recent goals
  - Serendipity links between projects
  - A short dream journal entry (not chat spam)

Dreams are stored under ~/.pocket/dreams/ and can surface on desk.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "dreams"
ROOT.mkdir(parents=True, exist_ok=True)
STATE = ROOT / "state.json"
JOURNAL = ROOT / "journal.jsonl"

_lock = threading.Lock()
_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_started = False


def _load() -> Dict[str, Any]:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "enabled": True,
        "interval_sec": 180,
        "dreams": 0,
        "last_dream_at": 0,
        "last_title": "",
        "idle_threshold_sec": 90,
    }


def _save(data: Dict[str, Any]) -> None:
    STATE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _append_dream(entry: Dict[str, Any]) -> None:
    with _lock:
        with JOURNAL.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")


def list_dreams(limit: int = 20) -> List[Dict[str, Any]]:
    if not JOURNAL.exists():
        return []
    lines = JOURNAL.read_text(encoding="utf-8", errors="replace").splitlines()
    out = []
    for ln in reversed(lines[-200:]):
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
        if len(out) >= limit:
            break
    return out


def status() -> Dict[str, Any]:
    data = _load()
    alive = _started and _thread is not None and _thread.is_alive()
    return {
        "ok": True,
        "schema": "pocket.dream.v1",
        "enabled": bool(data.get("enabled")),
        "running": alive and bool(data.get("enabled")),
        "interval_sec": data.get("interval_sec"),
        "dreams": data.get("dreams"),
        "last_dream_at": data.get("last_dream_at"),
        "last_title": data.get("last_title"),
        "recent": list_dreams(5),
    }


def start(*, interval_sec: Optional[int] = None) -> Dict[str, Any]:
    global _started, _thread
    data = _load()
    data["enabled"] = True
    if interval_sec:
        data["interval_sec"] = max(60, int(interval_sec))
    _save(data)
    _stop.clear()
    if _thread and _thread.is_alive():
        return status()
    _thread = threading.Thread(target=_loop, name="pocket-dream-mode", daemon=True)
    _thread.start()
    _started = True
    emit("dream", "dream mode started", agent="DREAMER", role="daemon")
    return status()


def stop() -> Dict[str, Any]:
    data = _load()
    data["enabled"] = False
    _save(data)
    _stop.set()
    return status()


def ensure_running() -> Dict[str, Any]:
    data = _load()
    if data.get("enabled", True):
        return start()
    return status()


def _host_idle_sec() -> float:
    """Best-effort: last session/job activity vs now."""
    home = Path.home() / ".pocket"
    newest = 0.0
    for sub in ("sessions", "jobs", "build_loops"):
        d = home / sub
        if not d.is_dir():
            continue
        try:
            for p in d.glob("**/*"):
                if p.is_file():
                    newest = max(newest, p.stat().st_mtime)
        except Exception:
            pass
    if newest <= 0:
        return 9999.0
    return max(0.0, time.time() - newest)


def dream_once(*, force: bool = False) -> Dict[str, Any]:
    """Produce one dream consolidation cycle."""
    data = _load()
    if not force and not data.get("enabled", True):
        return {"ok": False, "error": "dream mode disabled"}

    idle = _host_idle_sec()
    threshold = float(data.get("idle_threshold_sec") or 90)
    if not force and idle < threshold:
        return {"ok": True, "skipped": True, "reason": f"host busy (idle {int(idle)}s < {int(threshold)}s)"}

    fragments: List[str] = []
    serendipity: Dict[str, Any] = {}
    wiki: Dict[str, Any] = {}
    world: Dict[str, Any] = {}

    try:
        from pocket.infinite_wiki import ensure_watcher, reindex_if_stale, status as wiki_status

        ensure_watcher(interval_sec=12)
        wiki = wiki_status()
        # reindex a few stale nodes via watch tick side-effect
        fragments.append(f"Wiki nodes={wiki.get('nodes')} watcher={wiki.get('watcher')}")
    except Exception as e:
        fragments.append(f"wiki: {e}")

    try:
        from pocket.world_model import cortex_context, log_subcortex, status as wm_status

        world = wm_status()
        brief = cortex_context("agentic software shipping host co-pilot", limit=4)
        fragments.append(brief[:400])
        log_subcortex("dream", "night consolidation")
    except Exception as e:
        fragments.append(f"world: {e}")

    try:
        from pocket.serendipity import find_links

        serendipity = find_links(limit=4)
        for link in serendipity.get("links") or []:
            fragments.append(f"Serendipity: {link.get('a')} ↔ {link.get('b')} — {link.get('why')}")
    except Exception as e:
        fragments.append(f"serendipity: {e}")

    title = _dream_title(fragments)
    body = (
        f"# Dream · {time.strftime('%Y-%m-%d %H:%M')}\n\n"
        f"**Title:** {title}\n\n"
        f"**Idle:** {int(idle)}s\n\n"
        "## Fragments\n"
        + "\n".join(f"- {f}" for f in fragments[:12])
        + "\n\n## Note\n"
        "This is Subcortex consolidation — not a chat message. "
        "Wake the desk; ship what resonates.\n"
    )
    did = f"dream-{uuid.uuid4().hex[:10]}"
    (ROOT / f"{did}.md").write_text(body, encoding="utf-8")
    entry = {
        "id": did,
        "at": time.time(),
        "title": title,
        "idle_sec": idle,
        "path": str(ROOT / f"{did}.md"),
        "wiki_nodes": wiki.get("nodes"),
        "links": (serendipity.get("links") or [])[:4],
        "snippet": fragments[0][:200] if fragments else "",
    }
    _append_dream(entry)
    data["dreams"] = int(data.get("dreams") or 0) + 1
    data["last_dream_at"] = time.time()
    data["last_title"] = title
    _save(data)
    emit("dream", title[:80], agent="DREAMER", role="daemon")

    try:
        from pocket.proof_chain import mint_receipt

        mint_receipt("dream", title, meta={"id": did})
    except Exception:
        pass

    return {"ok": True, "dream": entry}


def _dream_title(fragments: List[str]) -> str:
    blob = " ".join(fragments).lower()
    if "serendipity" in blob:
        return "Crossed wires in the lab"
    if "wiki" in blob:
        return "Re-indexing the house of code"
    if "fact" in blob or "shakespeare" in blob:
        return "Common sense at 3am"
    if "swarm" in blob:
        return "The swarm that wouldn't sleep"
    return "Host co-pilot REM cycle"


def _loop() -> None:
    while not _stop.is_set():
        data = _load()
        if data.get("enabled", True):
            try:
                dream_once(force=False)
            except Exception as e:
                emit("dream", f"error {e}", agent="DREAMER", role="daemon")
        iv = max(60, int(data.get("interval_sec") or 180))
        for _ in range(iv):
            if _stop.is_set():
                break
            time.sleep(1)
