"""World Model — SQLite + embed targets for commercial-grade agent memory.

Datasets (indexed, not raw dumps on day one):
  1. Narrative Archetype Graph — plot beats, arcs, tropes (relational)
  2. Literary Prose Standards  — style exemplars (Gutenberg-ready slots)
  3. Factual Common Sense      — subject-predicate-object triples
  4. Syntactic Specifications  — language/library API docs for high-fidelity code

Subcortex daemons read/write here silently while Cortex streams dialogue.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import time
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path.home() / ".pocket" / "world_model"
DB_PATH = ROOT / "world.db"
_lock = Lock()

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS archetypes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  kind TEXT NOT NULL,          -- beat | arc | trope | framework
  description TEXT,
  structure_json TEXT,         -- ordered beats / roles
  tags TEXT,
  embedding BLOB,
  updated_at REAL
);
CREATE INDEX IF NOT EXISTS idx_arch_kind ON archetypes(kind);
CREATE INDEX IF NOT EXISTS idx_arch_name ON archetypes(name);

CREATE TABLE IF NOT EXISTS prose_standards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT NOT NULL,
  author TEXT,
  source TEXT,                 -- gutenberg | curated | user
  style_notes TEXT,
  excerpt TEXT,
  embedding BLOB,
  updated_at REAL
);

CREATE TABLE IF NOT EXISTS facts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  subject TEXT NOT NULL,
  predicate TEXT NOT NULL,
  object TEXT NOT NULL,
  source TEXT,                 -- wikidata | conceptnet | seed
  confidence REAL DEFAULT 1.0,
  embedding BLOB,
  updated_at REAL
);
CREATE INDEX IF NOT EXISTS idx_facts_s ON facts(subject);
CREATE INDEX IF NOT EXISTS idx_facts_p ON facts(predicate);

CREATE TABLE IF NOT EXISTS syntax_specs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  language TEXT NOT NULL,      -- python | js | rust | icp | ...
  library TEXT NOT NULL,
  symbol TEXT NOT NULL,         -- function/class/module
  signature TEXT,
  doc TEXT,
  embedding BLOB,
  updated_at REAL
);
CREATE INDEX IF NOT EXISTS idx_syn_lang ON syntax_specs(language);
CREATE INDEX IF NOT EXISTS idx_syn_lib ON syntax_specs(library);

CREATE TABLE IF NOT EXISTS narrative_state (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  character TEXT,
  timeline_json TEXT,
  notes TEXT,
  updated_at REAL
);
CREATE INDEX IF NOT EXISTS idx_ns_sess ON narrative_state(session_id);

CREATE TABLE IF NOT EXISTS subcortex_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT,
  detail TEXT,
  at REAL
);
"""


def _connect() -> sqlite3.Connection:
    ROOT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH), timeout=30, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def ensure_db() -> Path:
    with _lock:
        con = _connect()
        try:
            con.executescript(SCHEMA)
            con.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                ("schema_version", "1"),
            )
            con.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                ("updated_at", str(time.time())),
            )
            con.commit()
            if _count(con, "archetypes") == 0:
                _seed(con)
                con.commit()
        finally:
            con.close()
    return DB_PATH


def _count(con: sqlite3.Connection, table: str) -> int:
    return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


def embed_text(text: str, dim: int = 64) -> bytes:
    """Lightweight deterministic bag-of-hashes vector (no third-party)."""
    vec = [0.0] * dim
    toks = [t.lower() for t in (text or "").replace("\n", " ").split() if t]
    if not toks:
        return json.dumps(vec).encode("utf-8")
    for t in toks:
        h = int(hashlib.sha256(t.encode("utf-8")).hexdigest()[:8], 16)
        vec[h % dim] += 1.0
    # L2 normalize
    norm = sum(x * x for x in vec) ** 0.5 or 1.0
    vec = [x / norm for x in vec]
    return json.dumps(vec).encode("utf-8")


def cosine(a: bytes, b: bytes) -> float:
    try:
        va = json.loads(a.decode("utf-8"))
        vb = json.loads(b.decode("utf-8"))
    except Exception:
        return 0.0
    if len(va) != len(vb) or not va:
        return 0.0
    return float(sum(x * y for x, y in zip(va, vb)))


def _seed(con: sqlite3.Connection) -> None:
    now = time.time()
    archetypes = [
        (
            "Hero's Journey",
            "framework",
            "Classic monomyth arc",
            json.dumps(
                [
                    "ordinary_world",
                    "call_to_adventure",
                    "refusal",
                    "mentor",
                    "threshold",
                    "tests",
                    "ordeal",
                    "reward",
                    "road_back",
                    "resurrection",
                    "return",
                ]
            ),
            "story,arc",
        ),
        (
            "Three-Act Structure",
            "framework",
            "Setup / Confrontation / Resolution",
            json.dumps(["act1_setup", "act2_confrontation", "act3_resolution"]),
            "story,structure",
        ),
        (
            "Chekhov's Gun",
            "trope",
            "Introduce only what will be used later",
            json.dumps(["plant", "payoff"]),
            "foreshadow",
        ),
        (
            "Character Arc — Positive",
            "arc",
            "Flaw → pressure → change → new equilibrium",
            json.dumps(["flaw", "pressure", "choice", "change", "new_self"]),
            "character",
        ),
        (
            "Midpoint Reversal",
            "beat",
            "Story pivots; stakes flip",
            json.dumps(["false_victory_or_defeat", "new_direction"]),
            "plot",
        ),
        (
            "Save the Cat",
            "beat",
            "Early empathy moment for the protagonist",
            json.dumps(["empathy_action"]),
            "character,open",
        ),
    ]
    for name, kind, desc, structure, tags in archetypes:
        emb = embed_text(f"{name} {kind} {desc} {tags}")
        con.execute(
            "INSERT INTO archetypes(name,kind,description,structure_json,tags,embedding,updated_at) VALUES(?,?,?,?,?,?,?)",
            (name, kind, desc, structure, tags, emb, now),
        )

    prose = [
        (
            "Pride and Prejudice (excerpt style)",
            "Jane Austen",
            "gutenberg",
            "Ironic free indirect style; social observation; balanced clauses",
            "It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
        ),
        (
            "Moby-Dick (excerpt style)",
            "Herman Melville",
            "gutenberg",
            "Encyclopedic digression; elevated diction; sea mythos",
            "Call me Ishmael. Some years ago—never mind how long precisely—having little or no money in my purse...",
        ),
        (
            "Technical product prose",
            "POCKET Lab",
            "curated",
            "Clear, short sentences; concrete verbs; no hype",
            "The agent writes files on the host, runs tests, and only then answers.",
        ),
    ]
    for title, author, source, notes, excerpt in prose:
        emb = embed_text(f"{title} {author} {notes} {excerpt}")
        con.execute(
            "INSERT INTO prose_standards(title,author,source,style_notes,excerpt,embedding,updated_at) VALUES(?,?,?,?,?,?,?)",
            (title, author, source, notes, excerpt, emb, now),
        )

    facts = [
        ("Shakespeare", "wrote", "Hamlet", "seed", 1.0),
        ("Shakespeare", "wrote", "Macbeth", "seed", 1.0),
        ("Paris", "capital_of", "France", "seed", 1.0),
        ("Python", "created_by", "Guido van Rossum", "seed", 1.0),
        ("HTTP", "status_ok", "200", "seed", 1.0),
        ("SQLite", "is_a", "embedded relational database", "seed", 1.0),
        ("WSL", "runs_on", "Windows", "seed", 1.0),
        ("POCKET", "is_a", "host multi-agent co-pilot", "seed", 1.0),
        ("Cortex", "handles", "conversational dialogue", "seed", 1.0),
        ("Subcortex", "handles", "silent background world updates", "seed", 1.0),
        ("water", "boils_at_celsius", "100", "seed", 0.9),
        ("sun", "is_a", "star", "seed", 1.0),
    ]
    for s, p, o, src, conf in facts:
        emb = embed_text(f"{s} {p} {o}")
        con.execute(
            "INSERT INTO facts(subject,predicate,object,source,confidence,embedding,updated_at) VALUES(?,?,?,?,?,?,?)",
            (s, p, o, src, conf, emb, now),
        )

    specs = [
        ("python", "stdlib", "pathlib.Path", "Path(*pathsegments)", "Object-oriented filesystem paths"),
        ("python", "stdlib", "json.loads", "loads(s)", "Deserialize JSON string to Python object"),
        ("python", "stdlib", "sqlite3.connect", "connect(database)", "Open SQLite database connection"),
        ("python", "flask", "Flask", "Flask(__name__)", "WSGI web application object"),
        ("js", "stdlib", "Array.map", "array.map(fn)", "Transform each element"),
        ("js", "stdlib", "fetch", "fetch(url, init?)", "HTTP client returning Promise"),
        ("rust", "stdlib", "Vec::push", "vec.push(value)", "Append element to vector"),
        ("rust", "stdlib", "Result", "Result<T, E>", "Success or error enum"),
        ("icp", "motoko", "actor", "actor { ... }", "Canister actor definition"),
        ("icp", "motoko", "stable", "stable var x", "Persisted canister state"),
        ("typescript", "stdlib", "Promise.all", "Promise.all(iterable)", "Wait for all promises"),
        ("python", "pytest", "assert", "assert expr", "Test assertion"),
    ]
    for lang, lib, symbol, sig, doc in specs:
        emb = embed_text(f"{lang} {lib} {symbol} {sig} {doc}")
        con.execute(
            "INSERT INTO syntax_specs(language,library,symbol,signature,doc,embedding,updated_at) VALUES(?,?,?,?,?,?,?)",
            (lang, lib, symbol, sig, doc, emb, now),
        )


def status() -> Dict[str, Any]:
    ensure_db()
    with _lock:
        con = _connect()
        try:
            counts = {
                "archetypes": _count(con, "archetypes"),
                "prose_standards": _count(con, "prose_standards"),
                "facts": _count(con, "facts"),
                "syntax_specs": _count(con, "syntax_specs"),
                "narrative_state": _count(con, "narrative_state"),
                "subcortex_log": _count(con, "subcortex_log"),
            }
        finally:
            con.close()
    return {
        "ok": True,
        "schema": "pocket.world_model.v1",
        "db": str(DB_PATH),
        "counts": counts,
        "targets": [
            "narrative_archetype_graph",
            "literary_prose_standards",
            "factual_common_sense",
            "syntactic_specifications",
        ],
        "note": "Seed graph online; expand via ingest APIs / offline packs (Gutenberg, Wikidata, ConceptNet).",
    }


def search(query: str, *, kind: str = "all", limit: int = 8) -> Dict[str, Any]:
    ensure_db()
    qemb = embed_text(query)
    results: List[Dict[str, Any]] = []
    with _lock:
        con = _connect()
        try:
            if kind in ("all", "archetype", "narrative"):
                for row in con.execute("SELECT id,name,kind,description,structure_json,embedding FROM archetypes"):
                    score = cosine(qemb, row["embedding"] or b"[]")
                    results.append(
                        {
                            "type": "archetype",
                            "score": score,
                            "id": row["id"],
                            "name": row["name"],
                            "kind": row["kind"],
                            "description": row["description"],
                        }
                    )
            if kind in ("all", "prose"):
                for row in con.execute("SELECT id,title,author,style_notes,excerpt,embedding FROM prose_standards"):
                    score = cosine(qemb, row["embedding"] or b"[]")
                    results.append(
                        {
                            "type": "prose",
                            "score": score,
                            "id": row["id"],
                            "title": row["title"],
                            "author": row["author"],
                            "style_notes": row["style_notes"],
                        }
                    )
            if kind in ("all", "fact", "facts"):
                for row in con.execute("SELECT id,subject,predicate,object,source,embedding FROM facts"):
                    score = cosine(qemb, row["embedding"] or b"[]")
                    results.append(
                        {
                            "type": "fact",
                            "score": score,
                            "id": row["id"],
                            "triple": f"{row['subject']} → {row['predicate']} → {row['object']}",
                            "source": row["source"],
                        }
                    )
            if kind in ("all", "syntax", "code"):
                for row in con.execute(
                    "SELECT id,language,library,symbol,signature,doc,embedding FROM syntax_specs"
                ):
                    score = cosine(qemb, row["embedding"] or b"[]")
                    results.append(
                        {
                            "type": "syntax",
                            "score": score,
                            "id": row["id"],
                            "language": row["language"],
                            "symbol": f"{row['library']}.{row['symbol']}",
                            "signature": row["signature"],
                            "doc": row["doc"],
                        }
                    )
        finally:
            con.close()
    results.sort(key=lambda r: r.get("score") or 0, reverse=True)
    return {"ok": True, "query": query, "results": results[: max(1, min(limit, 40))]}


def fact_check(claim: str) -> Dict[str, Any]:
    """Subcortex-style fact review against common-sense graph."""
    hits = search(claim, kind="fact", limit=5)
    top = hits.get("results") or []
    supported = [h for h in top if (h.get("score") or 0) > 0.15]
    return {
        "ok": True,
        "claim": claim,
        "supported": bool(supported),
        "matches": supported[:3],
        "confidence": round(supported[0]["score"], 3) if supported else 0.0,
    }


def update_narrative_state(session_id: str, *, character: str = "", notes: str = "", timeline: Optional[list] = None) -> Dict[str, Any]:
    ensure_db()
    now = time.time()
    with _lock:
        con = _connect()
        try:
            con.execute(
                "INSERT INTO narrative_state(session_id,character,timeline_json,notes,updated_at) VALUES(?,?,?,?,?)",
                (session_id, character, json.dumps(timeline or []), notes[:4000], now),
            )
            con.commit()
        finally:
            con.close()
    return {"ok": True, "session_id": session_id}


def log_subcortex(kind: str, detail: str) -> None:
    ensure_db()
    with _lock:
        con = _connect()
        try:
            con.execute(
                "INSERT INTO subcortex_log(kind,detail,at) VALUES(?,?,?)",
                (kind[:40], (detail or "")[:2000], time.time()),
            )
            # keep log bounded
            con.execute(
                "DELETE FROM subcortex_log WHERE id NOT IN (SELECT id FROM subcortex_log ORDER BY id DESC LIMIT 500)"
            )
            con.commit()
        finally:
            con.close()


def cortex_context(query: str, *, limit: int = 6) -> str:
    """Compact context string Cortex can stream with — Subcortex precomputes this."""
    hits = search(query, kind="all", limit=limit).get("results") or []
    lines = ["[World Model brief]"]
    for h in hits:
        t = h.get("type")
        if t == "archetype":
            lines.append(f"- Archetype: {h.get('name')} ({h.get('kind')}) — {h.get('description')}")
        elif t == "prose":
            lines.append(f"- Prose: {h.get('title')} — {h.get('style_notes')}")
        elif t == "fact":
            lines.append(f"- Fact: {h.get('triple')}")
        elif t == "syntax":
            lines.append(f"- API: {h.get('language')} {h.get('symbol')} {h.get('signature')}")
    return "\n".join(lines)


def ingest_fact(subject: str, predicate: str, obj: str, *, source: str = "user") -> Dict[str, Any]:
    ensure_db()
    emb = embed_text(f"{subject} {predicate} {obj}")
    with _lock:
        con = _connect()
        try:
            con.execute(
                "INSERT INTO facts(subject,predicate,object,source,confidence,embedding,updated_at) VALUES(?,?,?,?,?,?,?)",
                (subject, predicate, obj, source, 1.0, emb, time.time()),
            )
            con.commit()
        finally:
            con.close()
    return {"ok": True}
