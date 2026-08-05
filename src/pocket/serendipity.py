"""Serendipity — unexpected links between projects, wiki nodes, and world facts.

Surfaces connections the human didn't ask for — the 'cool' of a co-pilot lab.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Set


def _tokens(s: str) -> Set[str]:
    stop = {
        "the",
        "and",
        "for",
        "with",
        "from",
        "this",
        "that",
        "into",
        "your",
        "have",
        "path",
        "file",
        "http",
        "true",
        "none",
        "self",
        "import",
        "return",
        "class",
        "function",
        "def",
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z0-9_]{3,}", (s or "").lower())
    return {w for w in words if w not in stop}


def find_links(*, limit: int = 8) -> Dict[str, Any]:
    nodes: List[Dict[str, Any]] = []
    # wiki summaries
    try:
        from pocket.infinite_wiki import ensure_db, _connect, _lock

        ensure_db()
        with _lock:
            con = _connect()
            try:
                for row in con.execute(
                    "SELECT path, summary, language FROM nodes WHERE kind='file' ORDER BY updated_at DESC LIMIT 60"
                ):
                    nodes.append(
                        {
                            "kind": "wiki",
                            "id": row["path"],
                            "label": Path(row["path"]).name,
                            "text": f"{row['path']} {row['summary'] or ''} {row['language'] or ''}",
                        }
                    )
            finally:
                con.close()
    except Exception:
        pass

    # world facts
    try:
        from pocket.world_model import ensure_db as wm_db, _connect as wm_con, _lock as wm_lock

        wm_db()
        with wm_lock:
            con = wm_con()
            try:
                for row in con.execute("SELECT subject, predicate, object FROM facts LIMIT 40"):
                    nodes.append(
                        {
                            "kind": "fact",
                            "id": f"{row['subject']}|{row['predicate']}|{row['object']}",
                            "label": f"{row['subject']}→{row['object']}",
                            "text": f"{row['subject']} {row['predicate']} {row['object']}",
                        }
                    )
            finally:
                con.close()
    except Exception:
        pass

    # recent dreams / duels / build goals
    home = Path.home() / ".pocket"
    for folder, kind in (
        ("dreams", "dream"),
        ("duels", "duel"),
        ("build_loops", "build"),
    ):
        d = home / folder
        if not d.is_dir():
            continue
        try:
            files = sorted(d.rglob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:8]
            files += sorted(d.rglob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:8]
            for fp in files[:10]:
                try:
                    txt = fp.read_text(encoding="utf-8", errors="replace")[:800]
                except Exception:
                    continue
                nodes.append(
                    {
                        "kind": kind,
                        "id": str(fp),
                        "label": fp.name,
                        "text": txt,
                    }
                )
        except Exception:
            pass

    links = []
    for i in range(len(nodes)):
        ti = _tokens(nodes[i]["text"])
        if len(ti) < 2:
            continue
        for j in range(i + 1, min(len(nodes), i + 25)):
            if nodes[i]["kind"] == nodes[j]["kind"] == "wiki":
                # prefer cross-kind or different dirs
                if Path(nodes[i]["id"]).parent == Path(nodes[j]["id"]).parent:
                    continue
            tj = _tokens(nodes[j]["text"])
            inter = ti & tj
            if len(inter) < 2:
                continue
            score = len(inter) / max(3, len(ti | tj) ** 0.5)
            if score < 0.35:
                continue
            shared = sorted(inter)[:5]
            links.append(
                {
                    "a": nodes[i]["label"],
                    "a_kind": nodes[i]["kind"],
                    "a_id": nodes[i]["id"],
                    "b": nodes[j]["label"],
                    "b_kind": nodes[j]["kind"],
                    "b_id": nodes[j]["id"],
                    "why": "shared: " + ", ".join(shared),
                    "score": round(score, 3),
                }
            )
    links.sort(key=lambda x: -x["score"])
    # de-dupe pairs
    seen = set()
    uniq = []
    for L in links:
        key = tuple(sorted([L["a"], L["b"]]))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(L)
        if len(uniq) >= limit:
            break
    return {
        "ok": True,
        "schema": "pocket.serendipity.v1",
        "links": uniq,
        "scanned": len(nodes),
        "hint": "Unexpected adjacency is a feature — follow a link into Wiki or a duel.",
    }
