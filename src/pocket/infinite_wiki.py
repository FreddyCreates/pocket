"""Infinite Wiki — hierarchical codebase summary engine for agents.

Solves context-window bloat: models never load multi-gig files wholesale.

Loop:
  1. get_file_profile(path)  → tiny Profile Card (sections, deps, symbols+lines)
  2. Inner monologue pinpoints e.g. L174
  3. read_file_lines(path, start, end) → high-resolution slice only
  4. Background worker watches mtimes → updates nodes + re-embeds vectors

Storage: ~/.pocket/infinite_wiki/wiki.db  (nodes + edges + embeddings)
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path.home() / ".pocket" / "infinite_wiki"
DB_PATH = ROOT / "wiki.db"
_lock = threading.Lock()
_watch_thread: Optional[threading.Thread] = None
_watch_stop = threading.Event()
_watch_started = False

# Skip heavy / irrelevant trees
SKIP_DIR_NAMES = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    "target",
    ".cache",
    ".pytest_cache",
    "desktop_profile",
    "workspaces",  # pocket huge trees unless explicitly rooted
}
MAX_FILE_BYTES = 2_000_000
MAX_PROFILE_EXCERPT = 400

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS roots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL UNIQUE,
  label TEXT,
  enabled INTEGER DEFAULT 1,
  updated_at REAL
);

CREATE TABLE IF NOT EXISTS nodes (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  path TEXT NOT NULL UNIQUE,
  root_id INTEGER,
  kind TEXT,                 -- file | dir
  language TEXT,
  size_bytes INTEGER,
  line_count INTEGER,
  mtime REAL,
  sha256 TEXT,
  summary TEXT,              -- short prose summary
  sections_json TEXT,        -- logical sections [{name,start,end}]
  symbols_json TEXT,         -- [{name,kind,line,end_line}]
  deps_json TEXT,            -- imports / requires
  profile_json TEXT,         -- full profile card cache
  embedding BLOB,
  updated_at REAL,
  FOREIGN KEY(root_id) REFERENCES roots(id)
);
CREATE INDEX IF NOT EXISTS idx_nodes_lang ON nodes(language);
CREATE INDEX IF NOT EXISTS idx_nodes_mtime ON nodes(mtime);

CREATE TABLE IF NOT EXISTS edges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  src_path TEXT NOT NULL,
  dst_path TEXT NOT NULL,
  kind TEXT,                 -- import | call | reference
  UNIQUE(src_path, dst_path, kind)
);

CREATE TABLE IF NOT EXISTS wiki_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT,
  detail TEXT,
  at REAL
);
"""


def _connect() -> sqlite3.Connection:
    ROOT.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(DB_PATH), timeout=60, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def ensure_db() -> Path:
    with _lock:
        con = _connect()
        try:
            con.executescript(SCHEMA)
            con.execute(
                "INSERT OR REPLACE INTO meta(key,value) VALUES(?,?)",
                ("schema", "infinite_wiki.v1"),
            )
            con.commit()
        finally:
            con.close()
    return DB_PATH


def embed_text(text: str, dim: int = 64) -> bytes:
    vec = [0.0] * dim
    for t in re.findall(r"[A-Za-z0-9_./\\-]+", (text or "").lower()):
        h = int(hashlib.sha256(t.encode("utf-8")).hexdigest()[:8], 16)
        vec[h % dim] += 1.0
    n = sum(x * x for x in vec) ** 0.5 or 1.0
    vec = [x / n for x in vec]
    return json.dumps(vec).encode("utf-8")


def cosine(a: bytes, b: bytes) -> float:
    try:
        va = json.loads(a.decode("utf-8"))
        vb = json.loads(b.decode("utf-8"))
        if len(va) != len(vb) or not va:
            return 0.0
        return float(sum(x * y for x, y in zip(va, vb)))
    except Exception:
        return 0.0


def _lang_for(path: Path) -> str:
    ext = path.suffix.lower()
    return {
        ".py": "python",
        ".js": "javascript",
        ".jsx": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".rs": "rust",
        ".go": "go",
        ".java": "java",
        ".md": "markdown",
        ".json": "json",
        ".html": "html",
        ".css": "css",
        ".motoko": "motoko",
        ".mo": "motoko",
        ".toml": "toml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".ps1": "powershell",
        ".sh": "shell",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
    }.get(ext, ext.lstrip(".") or "text")


def _safe_resolve(path: str, *, roots: Optional[List[str]] = None) -> Path:
    p = Path(path).expanduser()
    if not p.is_absolute():
        # try common roots
        candidates = []
        if roots:
            candidates.extend(Path(r) for r in roots)
        candidates.extend(
            [
                Path.home() / "OneDrive" / "pocket-os",
                Path.home() / ".pocket",
                Path.cwd(),
            ]
        )
        for base in candidates:
            cand = (base / path).resolve()
            if cand.exists():
                p = cand
                break
        else:
            p = (Path.cwd() / path).resolve()
    else:
        p = p.resolve()
    return p


def _path_allowed(path: Path) -> bool:
    """Refuse obvious founder-private dumps unless under indexed roots."""
    s = str(path).lower().replace("\\", "/")
    deny = ["/appdata/local/", "/ntuser", "/.ssh/"]
    for d in deny:
        if d in s:
            return False
    return True


# ---------- profilers ----------

_PY_DEF = re.compile(
    r"^(?P<indent>\s*)(?P<kind>def|class|async\s+def)\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)",
    re.M,
)
_PY_IMPORT = re.compile(
    r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))",
    re.M,
)
_JS_FUNC = re.compile(
    r"^(?P<indent>\s*)(?:export\s+)?(?:async\s+)?(?:function\s+(?P<name1>[A-Za-z_][\w]*)|"
    r"(?:const|let|var)\s+(?P<name2>[A-Za-z_][\w]*)\s*=\s*(?:async\s*)?\(|"
    r"(?:const|let|var)\s+(?P<name3>[A-Za-z_][\w]*)\s*=\s*(?:async\s*)?function)",
    re.M,
)
_JS_IMPORT = re.compile(
    r"""^\s*import\s+.*?from\s+['"]([^'"]+)['"]|^\s*require\(\s*['"]([^'"]+)['"]\s*\)""",
    re.M,
)
_RS_FN = re.compile(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_][\w]*)", re.M)
_MD_H = re.compile(r"^(#{1,3})\s+(.+)$", re.M)


def _indent_width(line: str) -> int:
    n = 0
    for ch in line:
        if ch == " ":
            n += 1
        elif ch == "\t":
            n += 4
        else:
            break
    return n


def _py_block_end(lines: List[str], start_idx: int, base_indent: int) -> int:
    """AST-ish: block ends at first non-empty, non-comment line with indent <= base (after header)."""
    n = len(lines)
    # start_idx is 0-based line of def/class
    i = start_idx + 1
    # skip blank/decorator-only until body starts
    saw_body = False
    last = start_idx
    while i < n:
        raw = lines[i]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        ind = _indent_width(raw)
        if not saw_body:
            # first real body line must be indented more (or pass/...)
            if ind > base_indent:
                saw_body = True
                last = i
                i += 1
                continue
            # single-line def: def f(): return 1
            if ind == base_indent:
                return start_idx + 1
            i += 1
            continue
        if ind <= base_indent:
            # dedent → block ended on previous content line
            return last + 1  # 1-based end_line
        last = i
        i += 1
    return last + 1 if saw_body else start_idx + 1


def _brace_block_end(lines: List[str], start_idx: int) -> int:
    """Count {} from the first '{' on/after start line."""
    depth = 0
    started = False
    for i in range(start_idx, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                started = True
            elif ch == "}":
                depth -= 1
                if started and depth <= 0:
                    return i + 1  # 1-based
    return min(len(lines), start_idx + 1)


def _profile_python(text: str) -> Tuple[List[Dict], List[Dict], List[str]]:
    symbols: List[Dict[str, Any]] = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)(async\s+def|def|class)\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        if not m:
            continue
        kind = "class" if m.group(2) == "class" else "function"
        base = _indent_width(m.group(1))
        end_line = _py_block_end(lines, i, base)
        symbols.append(
            {
                "name": m.group(3),
                "kind": kind,
                "line": i + 1,
                "end_line": max(i + 1, end_line),
                "indent": base,
            }
        )
    # Prefer indent-walk; clamp by next sibling if walk overshot oddly
    for idx, sym in enumerate(symbols):
        for nxt in symbols[idx + 1 :]:
            if nxt["indent"] <= sym["indent"]:
                sym["end_line"] = min(sym["end_line"], nxt["line"] - 1)
                break
        if "indent" in sym:
            del sym["indent"]

    sections = []
    if symbols:
        tops = [s for s in symbols if s["kind"] == "class"] or [
            s for s in symbols if s["line"] and True
        ]
        # top-level only (approx: first column symbols)
        tops = [s for s in symbols if True][:40]
        # filter to module-level: line starts with def/class at col 0 in original — recompute
        tops = []
        for s in symbols:
            ln = lines[s["line"] - 1] if s["line"] <= len(lines) else ""
            if _indent_width(ln) == 0:
                tops.append(s)
        tops = tops or symbols[:12]
        for s in tops[:40]:
            sections.append(
                {
                    "name": s["name"],
                    "kind": s["kind"],
                    "start": s["line"],
                    "end": s["end_line"],
                }
            )
    else:
        sections = [{"name": "body", "kind": "file", "start": 1, "end": len(lines) or 1}]

    deps = []
    for m in _PY_IMPORT.finditer(text):
        deps.append(m.group(1) or m.group(2) or "")
    deps = sorted({d for d in deps if d})[:80]
    return sections, symbols[:200], deps


def _profile_js(text: str) -> Tuple[List[Dict], List[Dict], List[str]]:
    lines = text.splitlines()
    symbols: List[Dict[str, Any]] = []
    for i, line in enumerate(lines):
        m = re.match(
            r"^\s*(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_][\w]*)",
            line,
        )
        if m:
            symbols.append(
                {
                    "name": m.group(1),
                    "kind": "function",
                    "line": i + 1,
                    "end_line": _brace_block_end(lines, i),
                }
            )
            continue
        m = re.match(
            r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][\w]*)\s*=\s*(?:async\s*)?(?:\(|function)",
            line,
        )
        if m:
            symbols.append(
                {
                    "name": m.group(1),
                    "kind": "function",
                    "line": i + 1,
                    "end_line": _brace_block_end(lines, i),
                }
            )
            continue
        m = re.match(r"^\s*(?:export\s+)?class\s+([A-Za-z_][\w]*)", line)
        if m:
            symbols.append(
                {
                    "name": m.group(1),
                    "kind": "class",
                    "line": i + 1,
                    "end_line": _brace_block_end(lines, i),
                }
            )
    sections = [
        {"name": s["name"], "kind": s["kind"], "start": s["line"], "end": s["end_line"]}
        for s in symbols[:40]
    ] or [{"name": "body", "kind": "file", "start": 1, "end": len(lines) or 1}]
    deps = []
    for m in _JS_IMPORT.finditer(text):
        deps.append(m.group(1) or m.group(2) or "")
    deps = sorted({d for d in deps if d})[:80]
    return sections, symbols[:200], deps


def _profile_md(text: str) -> Tuple[List[Dict], List[Dict], List[str]]:
    lines = text.splitlines()
    sections = []
    symbols = []
    for i, line in enumerate(lines, 1):
        m = re.match(r"^(#{1,3})\s+(.+)$", line)
        if m:
            name = m.group(2).strip()[:80]
            sections.append({"name": name, "kind": f"h{len(m.group(1))}", "start": i, "end": i})
            symbols.append({"name": name, "kind": "heading", "line": i, "end_line": i})
    for idx, sec in enumerate(sections):
        if idx + 1 < len(sections):
            sec["end"] = sections[idx + 1]["start"] - 1
        else:
            sec["end"] = len(lines) or 1
        symbols[idx]["end_line"] = sec["end"]
    if not sections:
        sections = [{"name": "document", "kind": "file", "start": 1, "end": len(lines) or 1}]
    return sections, symbols[:200], []


def _profile_generic(text: str) -> Tuple[List[Dict], List[Dict], List[str]]:
    n = len(text.splitlines()) or 1
    chunk = max(40, n // 8)
    sections = []
    for start in range(1, n + 1, chunk):
        end = min(n, start + chunk - 1)
        sections.append({"name": f"L{start}-L{end}", "kind": "slice", "start": start, "end": end})
    return sections[:40], [], []


def build_profile(path: str | Path, *, roots: Optional[List[str]] = None) -> Dict[str, Any]:
    """Compute Profile Card for a file (no DB write)."""
    ensure_db()
    fp = _safe_resolve(str(path), roots=roots)
    if not fp.exists() or not fp.is_file():
        return {"ok": False, "error": "file not found", "path": str(path)}
    if not _path_allowed(fp):
        return {"ok": False, "error": "path not allowed", "path": str(fp)}
    try:
        size = fp.stat().st_size
        mtime = fp.stat().st_mtime
    except Exception as e:
        return {"ok": False, "error": str(e)}
    if size > MAX_FILE_BYTES:
        return {
            "ok": True,
            "path": str(fp),
            "kind": "file",
            "language": _lang_for(fp),
            "size_bytes": size,
            "line_count": None,
            "summary": f"Large file ({size} bytes) — profile deferred; use read_file_lines with known ranges.",
            "sections": [{"name": "too_large", "kind": "file", "start": 1, "end": 1}],
            "symbols": [],
            "deps": [],
            "truncated": True,
        }
    try:
        raw = fp.read_bytes()
        text = raw.decode("utf-8", errors="replace")
    except Exception as e:
        return {"ok": False, "error": f"read failed: {e}"}

    lang = _lang_for(fp)
    lines = text.splitlines()
    engine = "heuristic"

    # Optional tree-sitter for tighter AST ranges
    ts_result = None
    if lang in ("python", "javascript", "typescript"):
        try:
            from pocket.wiki_treesitter import profile_with_treesitter

            ts_result = profile_with_treesitter(text, lang)
        except Exception:
            ts_result = None

    if ts_result is not None:
        sections, symbols, deps = ts_result
        engine = "tree-sitter"
    elif lang == "python":
        sections, symbols, deps = _profile_python(text)
    elif lang in ("javascript", "typescript"):
        sections, symbols, deps = _profile_js(text)
    elif lang == "markdown":
        sections, symbols, deps = _profile_md(text)
    elif lang == "rust":
        # reuse js-ish line estimate with rust fn regex
        symbols = []
        for i, line in enumerate(lines, 1):
            m = re.match(r"^\s*(?:pub\s+)?(?:async\s+)?fn\s+([A-Za-z_][\w]*)", line)
            if m:
                symbols.append({"name": m.group(1), "kind": "function", "line": i, "end_line": i})
        for idx, sym in enumerate(symbols):
            sym["end_line"] = symbols[idx + 1]["line"] - 1 if idx + 1 < len(symbols) else len(lines)
        sections = [
            {"name": s["name"], "kind": "function", "start": s["line"], "end": s["end_line"]}
            for s in symbols[:40]
        ] or [{"name": "crate", "kind": "file", "start": 1, "end": len(lines) or 1}]
        deps = re.findall(r"^\s*use\s+([\w:]+)", text, re.M)[:40]
    else:
        sections, symbols, deps = _profile_generic(text)

    # one-line summary
    head = " ".join(lines[:5])[:MAX_PROFILE_EXCERPT]
    summary = (
        f"{fp.name} · {lang} · {len(lines)} lines · {len(symbols)} symbols · "
        f"{len(deps)} deps · ast={engine}. Head: {head[:160]}"
    )
    sha = hashlib.sha256(raw).hexdigest()
    card = {
        "ok": True,
        "schema": "pocket.file_profile.v1",
        "path": str(fp),
        "name": fp.name,
        "kind": "file",
        "language": lang,
        "size_bytes": size,
        "line_count": len(lines),
        "mtime": mtime,
        "sha256": sha,
        "summary": summary,
        "sections": sections,
        "symbols": symbols,
        "deps": deps,
        "ast_engine": engine,
        "how_to_use": {
            "1": "Read this card — do NOT load the whole file",
            "2": "Pick symbol/section line numbers from the card",
            "3": "Call read_file_lines(path, start, end) for a tight window",
            "4": "Open definition via goto_definition(name, from_path)",
            "5": "Write minimal diffs; watcher will reindex",
        },
        "truncated": False,
    }
    return card


def get_file_profile(path: str, *, roots: Optional[List[str]] = None, refresh: bool = False) -> Dict[str, Any]:
    """Agent tool: tiny Profile Card, preferably from cache if mtime matches."""
    ensure_db()
    fp = _safe_resolve(path, roots=roots)
    if not fp.exists():
        return {"ok": False, "error": "file not found", "path": path}
    try:
        mtime = fp.stat().st_mtime
        size = fp.stat().st_size
    except Exception as e:
        return {"ok": False, "error": str(e)}

    if not refresh:
        with _lock:
            con = _connect()
            try:
                row = con.execute(
                    "SELECT profile_json, mtime, size_bytes FROM nodes WHERE path=?",
                    (str(fp),),
                ).fetchone()
                if row and row["profile_json"] and abs(float(row["mtime"] or 0) - mtime) < 0.001:
                    try:
                        card = json.loads(row["profile_json"])
                        card["cached"] = True
                        return card
                    except Exception:
                        pass
            finally:
                con.close()

    card = build_profile(fp, roots=roots)
    if card.get("ok"):
        _upsert_node(card)
    card["cached"] = False
    return card


def read_file_lines(
    path: str,
    start: int = 1,
    end: Optional[int] = None,
    *,
    roots: Optional[List[str]] = None,
    max_lines: int = 200,
) -> Dict[str, Any]:
    """Agent tool: high-resolution slice only."""
    fp = _safe_resolve(path, roots=roots)
    if not fp.exists() or not fp.is_file():
        return {"ok": False, "error": "file not found", "path": path}
    if not _path_allowed(fp):
        return {"ok": False, "error": "path not allowed"}
    try:
        text = fp.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return {"ok": False, "error": str(e)}
    lines = text.splitlines()
    n = len(lines)
    s = max(1, int(start or 1))
    e = int(end or min(n, s + 40 - 1))
    if e < s:
        e = s
    if e - s + 1 > max_lines:
        e = s + max_lines - 1
    e = min(n, e)
    slice_lines = lines[s - 1 : e]
    numbered = [f"{i}|{line}" for i, line in enumerate(slice_lines, start=s)]
    return {
        "ok": True,
        "path": str(fp),
        "start": s,
        "end": e,
        "line_count_total": n,
        "lines": numbered,
        "text": "\n".join(numbered),
        "hint": "Edit only this window; re-profile after write via get_file_profile(refresh=true)",
    }


def find_symbol(name: str, *, root: str = "", limit: int = 20) -> Dict[str, Any]:
    """Search cached symbols across indexed nodes."""
    ensure_db()
    name_l = (name or "").lower()
    hits = []
    with _lock:
        con = _connect()
        try:
            q = "SELECT path, language, symbols_json FROM nodes WHERE kind='file'"
            args: tuple = ()
            if root:
                q += " AND path LIKE ?"
                args = (str(Path(root).resolve()) + "%",)
            for row in con.execute(q, args):
                try:
                    syms = json.loads(row["symbols_json"] or "[]")
                except Exception:
                    continue
                for s in syms:
                    sn = (s.get("name") or "").lower()
                    if name_l == sn or name_l in sn:
                        hits.append(
                            {
                                "path": row["path"],
                                "language": row["language"],
                                "name": s.get("name"),
                                "kind": s.get("kind"),
                                "line": s.get("line"),
                                "end_line": s.get("end_line"),
                            }
                        )
                        if len(hits) >= limit:
                            break
                if len(hits) >= limit:
                    break
        finally:
            con.close()
    # exact matches first
    hits.sort(key=lambda h: (0 if (h.get("name") or "").lower() == name_l else 1, h.get("path") or ""))
    return {"ok": True, "query": name, "hits": hits}


def _resolve_python_module(mod: str, from_file: Path, roots: List[Path]) -> Optional[Path]:
    """Resolve import path to a .py file under roots / relative package."""
    if not mod:
        return None
    parts = mod.replace(".", "/")
    candidates = []
    # relative to file package
    pkg = from_file.parent
    candidates.append(pkg / f"{parts}.py")
    candidates.append(pkg / parts / "__init__.py")
    # walk up package roots
    for base in [pkg] + list(roots):
        candidates.append(base / f"{parts}.py")
        candidates.append(base / parts / "__init__.py")
        # pocket.foo style under src
        if "pocket" in parts or True:
            candidates.append(base / "src" / f"{parts}.py")
            candidates.append(base / "src" / parts / "__init__.py")
    for c in candidates:
        try:
            if c.is_file():
                return c.resolve()
        except Exception:
            continue
    return None


def _resolve_js_module(spec: str, from_file: Path) -> Optional[Path]:
    if not spec or not (spec.startswith(".") or spec.startswith("/")):
        return None  # bare package — leave unresolved
    base = (from_file.parent / spec).resolve()
    for cand in (
        base,
        Path(str(base) + ".js"),
        Path(str(base) + ".ts"),
        Path(str(base) + ".tsx"),
        Path(str(base) + ".jsx"),
        base / "index.js",
        base / "index.ts",
    ):
        if cand.is_file():
            return cand
    return None


def goto_definition(
    name: str,
    *,
    from_path: str = "",
    roots: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Cross-file go-to-definition using import map + symbol index."""
    ensure_db()
    name = (name or "").strip()
    if not name:
        return {"ok": False, "error": "name required"}

    # 1) exact/local symbol hits
    hits = find_symbol(name, limit=30).get("hits") or []
    definitions = list(hits)

    # 2) if from_path given, parse imports and resolve modules
    resolved_files: List[str] = []
    if from_path:
        fp = _safe_resolve(from_path, roots=roots)
        if fp.is_file():
            try:
                text = fp.read_text(encoding="utf-8", errors="replace")
            except Exception:
                text = ""
            root_paths = [Path(r) for r in (roots or [])]
            root_paths += [fp.parent, Path.home() / "OneDrive" / "pocket-os" / "src"]
            # python: from X import name / import X
            for m in re.finditer(
                rf"^\s*from\s+([\w.]+)\s+import\s+([^\n#]+)",
                text,
                re.M,
            ):
                mod, imports = m.group(1), m.group(2)
                names = [x.strip().split(" as ")[0].strip() for x in imports.split(",")]
                if name in names or name == mod.split(".")[-1]:
                    target = _resolve_python_module(mod, fp, root_paths)
                    if target:
                        resolved_files.append(str(target))
            for m in re.finditer(r"^\s*import\s+([\w.]+)", text, re.M):
                mod = m.group(1)
                if name == mod.split(".")[-1] or name == mod:
                    target = _resolve_python_module(mod, fp, root_paths)
                    if target:
                        resolved_files.append(str(target))
            # js relative
            for m in _JS_IMPORT.finditer(text):
                spec = m.group(1) or m.group(2) or ""
                if name in spec or Path(spec).stem == name:
                    target = _resolve_js_module(spec, fp)
                    if target:
                        resolved_files.append(str(target))

    # 3) profile resolved files and pull symbol
    for rpath in resolved_files:
        card = get_file_profile(rpath, refresh=False)
        if not card.get("ok"):
            continue
        for s in card.get("symbols") or []:
            if (s.get("name") or "") == name or name in (s.get("name") or ""):
                definitions.append(
                    {
                        "path": rpath,
                        "language": card.get("language"),
                        "name": s.get("name"),
                        "kind": s.get("kind"),
                        "line": s.get("line"),
                        "end_line": s.get("end_line"),
                        "via": "import_resolve",
                    }
                )
        if not any(d.get("path") == rpath for d in definitions):
            definitions.append(
                {
                    "path": rpath,
                    "language": card.get("language"),
                    "name": name,
                    "kind": "module",
                    "line": 1,
                    "end_line": min(40, card.get("line_count") or 40),
                    "via": "module_file",
                }
            )

    # de-dupe
    seen = set()
    uniq = []
    for d in definitions:
        key = (d.get("path"), d.get("name"), d.get("line"))
        if key in seen:
            continue
        seen.add(key)
        uniq.append(d)

    return {
        "ok": True,
        "name": name,
        "from_path": from_path or None,
        "definitions": uniq[:25],
        "resolved_modules": resolved_files[:15],
        "how_to_use": "Pick a definition → read_file_lines(path, line, end_line)",
    }


def inject_wiki_context(
    prompt: str,
    *,
    cwd: str = "",
    max_cards: int = 3,
    max_chars: int = 3500,
) -> str:
    """Auto-inject Profile Cards for paths/symbols mentioned in the prompt.

    Keeps coding agents hierarchical without saturating context.
    """
    text = (prompt or "").strip()
    if not text:
        return text
    # already injected
    if "[Infinite Wiki" in text or "Profile Card" in text[:500]:
        return text

    paths = re.findall(
        r"(?:[A-Za-z]:[\\/][^\s'\"`]+|/[^\s'\"`]+\.(?:py|js|ts|tsx|rs|md|go)|"
        r"(?:src|pocket)/[^\s'\"`]+\.(?:py|js|ts|tsx|rs|md))",
        text,
    )
    # symbols after def/class/function or camelCase tokens that look like APIs
    symbols = re.findall(
        r"\b(?:def|class|function|fn)\s+([A-Za-z_][\w]*)|"
        r"\b([A-Za-z_][\w]{4,})\b(?=\s*\()",
        text,
    )
    sym_names = []
    skip = {
        "print", "len", "open", "path", "json", "true", "false", "none",
        "self", "return", "import", "from", "class", "async", "await",
        "fix", "with", "for", "while", "if", "else", "try", "except",
    }
    for a, b in symbols:
        n = a or b
        if not n or n in sym_names:
            continue
        if n.lower() in skip:
            continue
        if n[0].isalpha():
            sym_names.append(n)
    sym_names = sym_names[:6]

    cards = []
    roots = [cwd] if cwd else None
    for p in paths[:max_cards]:
        p = p.strip(" \t,;:'\"()")
        card = get_file_profile(p, roots=roots)
        if card.get("ok"):
            # compact card for injection
            compact = {
                "path": card.get("path"),
                "language": card.get("language"),
                "line_count": card.get("line_count"),
                "summary": card.get("summary"),
                "symbols": (card.get("symbols") or [])[:25],
                "sections": (card.get("sections") or [])[:15],
                "deps": (card.get("deps") or [])[:20],
            }
            cards.append(compact)

    def_bits = []
    for sn in sym_names[:4]:
        g = goto_definition(sn, from_path=paths[0] if paths else "", roots=roots)
        defs = g.get("definitions") or []
        if defs:
            d0 = defs[0]
            def_bits.append(
                f"- `{sn}` → {d0.get('path')}:{d0.get('line')}-{d0.get('end_line')} ({d0.get('kind')})"
            )
            # also attach one profile if not already
            if len(cards) < max_cards and d0.get("path"):
                if not any(c.get("path") == d0["path"] for c in cards):
                    card = get_file_profile(d0["path"])
                    if card.get("ok"):
                        cards.append(
                            {
                                "path": card.get("path"),
                                "language": card.get("language"),
                                "line_count": card.get("line_count"),
                                "summary": card.get("summary"),
                                "symbols": (card.get("symbols") or [])[:20],
                                "sections": (card.get("sections") or [])[:12],
                                "deps": (card.get("deps") or [])[:15],
                            }
                        )

    if not cards and not def_bits:
        # still teach the protocol when coding
        if not re.search(r"\b(code|function|class|file|bug|fix|implement|refactor)\b", text, re.I):
            return text
        preface = (
            "[Infinite Wiki protocol — do NOT load whole files. "
            "Use get_file_profile(path), then read_file_lines(path,start,end) for tight windows. "
            "find_symbol / goto_definition for navigation.]\n\n"
        )
        return (preface + text)[:20000]

    parts = [
        "[Infinite Wiki — hierarchical context; do NOT paste whole files]",
        "Tools: get_file_profile · read_file_lines · find_symbol · goto_definition · search_profiles",
        "Workflow: Profile Card → pinpoint lines → read_file_lines only → minimal edit.",
    ]
    if def_bits:
        parts.append("Definitions:")
        parts.extend(def_bits)
    for c in cards:
        parts.append(
            f"\n### Profile Card · {c.get('path')}\n"
            f"{c.get('summary')}\n"
            f"symbols: "
            + ", ".join(
                f"{s.get('name')}@L{s.get('line')}-L{s.get('end_line')}"
                for s in (c.get("symbols") or [])[:18]
            )
        )
    inject = "\n".join(parts)
    if len(inject) > max_chars:
        inject = inject[: max_chars - 20] + "\n…[truncated]"
    return f"{inject}\n\n---\nUSER TASK:\n{text}"[:20000]


def ensure_default_index() -> Dict[str, Any]:
    """Boot: ensure pocket-os src is indexed if wiki is empty."""
    ensure_db()
    st = status()
    if int(st.get("nodes") or 0) >= 20:
        return {"ok": True, "skipped": True, "nodes": st.get("nodes")}
    pocket_src = Path.home() / "OneDrive" / "pocket-os" / "src" / "pocket"
    if pocket_src.is_dir():
        return index_tree(str(pocket_src), label="pocket-src", max_files=400)
    return {"ok": True, "skipped": True, "reason": "no default tree"}


def search_profiles(query: str, *, limit: int = 12) -> Dict[str, Any]:
    ensure_db()
    qemb = embed_text(query)
    scored = []
    with _lock:
        con = _connect()
        try:
            for row in con.execute(
                "SELECT path, language, summary, line_count, embedding FROM nodes WHERE kind='file'"
            ):
                sc = cosine(qemb, row["embedding"] or b"[]")
                # lexical boost
                blob = f"{row['path']} {row['summary'] or ''}".lower()
                if any(t in blob for t in query.lower().split()):
                    sc += 0.15
                scored.append(
                    {
                        "path": row["path"],
                        "language": row["language"],
                        "summary": row["summary"],
                        "line_count": row["line_count"],
                        "score": round(sc, 4),
                    }
                )
        finally:
            con.close()
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"ok": True, "query": query, "results": scored[:limit]}


def _upsert_node(card: Dict[str, Any], *, root_id: Optional[int] = None) -> None:
    if not card.get("ok"):
        return
    path = card["path"]
    emb = embed_text(
        f"{card.get('name')} {card.get('language')} {card.get('summary')} "
        + " ".join(s.get("name", "") for s in (card.get("symbols") or [])[:40])
    )
    with _lock:
        con = _connect()
        try:
            con.execute(
                """
                INSERT INTO nodes(path, root_id, kind, language, size_bytes, line_count, mtime, sha256,
                  summary, sections_json, symbols_json, deps_json, profile_json, embedding, updated_at)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(path) DO UPDATE SET
                  root_id=excluded.root_id,
                  language=excluded.language,
                  size_bytes=excluded.size_bytes,
                  line_count=excluded.line_count,
                  mtime=excluded.mtime,
                  sha256=excluded.sha256,
                  summary=excluded.summary,
                  sections_json=excluded.sections_json,
                  symbols_json=excluded.symbols_json,
                  deps_json=excluded.deps_json,
                  profile_json=excluded.profile_json,
                  embedding=excluded.embedding,
                  updated_at=excluded.updated_at
                """,
                (
                    path,
                    root_id,
                    "file",
                    card.get("language"),
                    card.get("size_bytes"),
                    card.get("line_count"),
                    card.get("mtime"),
                    card.get("sha256"),
                    card.get("summary"),
                    json.dumps(card.get("sections") or []),
                    json.dumps(card.get("symbols") or []),
                    json.dumps(card.get("deps") or []),
                    json.dumps(card),
                    emb,
                    time.time(),
                ),
            )
            # edges from deps (logical, not resolved paths)
            for dep in (card.get("deps") or [])[:40]:
                try:
                    con.execute(
                        "INSERT OR IGNORE INTO edges(src_path, dst_path, kind) VALUES(?,?,?)",
                        (path, dep, "import"),
                    )
                except Exception:
                    pass
            con.commit()
        finally:
            con.close()


def add_root(path: str, *, label: str = "") -> Dict[str, Any]:
    ensure_db()
    p = Path(path).expanduser().resolve()
    if not p.is_dir():
        return {"ok": False, "error": "not a directory", "path": str(p)}
    with _lock:
        con = _connect()
        try:
            con.execute(
                "INSERT INTO roots(path, label, enabled, updated_at) VALUES(?,?,1,?) "
                "ON CONFLICT(path) DO UPDATE SET label=excluded.label, enabled=1, updated_at=excluded.updated_at",
                (str(p), label or p.name, time.time()),
            )
            con.commit()
            rid = con.execute("SELECT id FROM roots WHERE path=?", (str(p),)).fetchone()["id"]
        finally:
            con.close()
    return {"ok": True, "root_id": rid, "path": str(p)}


def list_roots() -> List[Dict[str, Any]]:
    ensure_db()
    with _lock:
        con = _connect()
        try:
            rows = con.execute("SELECT id, path, label, enabled, updated_at FROM roots").fetchall()
            return [dict(r) for r in rows]
        finally:
            con.close()


def index_tree(
    root: str,
    *,
    label: str = "",
    max_files: int = 2000,
    extensions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Index a codebase tree into nodes (profile each file)."""
    ensure_db()
    r = add_root(root, label=label)
    if not r.get("ok"):
        return r
    root_path = Path(r["path"])
    rid = r["root_id"]
    exts = set(
        extensions
        or [
            ".py",
            ".js",
            ".jsx",
            ".ts",
            ".tsx",
            ".rs",
            ".go",
            ".md",
            ".json",
            ".html",
            ".css",
            ".mo",
            ".motoko",
            ".toml",
            ".ps1",
        ]
    )
    indexed = 0
    skipped = 0
    errors = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".")]
        for fn in filenames:
            if Path(fn).suffix.lower() not in exts:
                skipped += 1
                continue
            fp = Path(dirpath) / fn
            try:
                if fp.stat().st_size > MAX_FILE_BYTES:
                    skipped += 1
                    continue
                card = build_profile(fp)
                if card.get("ok"):
                    _upsert_node(card, root_id=rid)
                    indexed += 1
                else:
                    skipped += 1
            except Exception as e:
                errors.append(f"{fp}: {e}")
            if indexed >= max_files:
                break
        if indexed >= max_files:
            break
    _log("index_tree", f"root={root_path} indexed={indexed} skipped={skipped}")
    return {
        "ok": True,
        "root": str(root_path),
        "indexed": indexed,
        "skipped": skipped,
        "errors": errors[:20],
        "max_files": max_files,
    }


def reindex_if_stale(path: str) -> Dict[str, Any]:
    """Background: if mtime changed, rebuild profile + embedding."""
    ensure_db()
    fp = Path(path)
    if not fp.is_file():
        return {"ok": False, "error": "not a file"}
    try:
        mtime = fp.stat().st_mtime
    except Exception as e:
        return {"ok": False, "error": str(e)}
    with _lock:
        con = _connect()
        try:
            row = con.execute("SELECT mtime, sha256 FROM nodes WHERE path=?", (str(fp.resolve()),)).fetchone()
        finally:
            con.close()
    if row and abs(float(row["mtime"] or 0) - mtime) < 0.001:
        return {"ok": True, "changed": False, "path": str(fp)}
    card = build_profile(fp)
    if card.get("ok"):
        _upsert_node(card)
        _log("reindex", str(fp))
        return {"ok": True, "changed": True, "path": str(fp), "line_count": card.get("line_count")}
    return card


def _log(kind: str, detail: str) -> None:
    try:
        with _lock:
            con = _connect()
            try:
                con.execute(
                    "INSERT INTO wiki_log(kind, detail, at) VALUES(?,?,?)",
                    (kind[:40], detail[:2000], time.time()),
                )
                con.execute(
                    "DELETE FROM wiki_log WHERE id NOT IN (SELECT id FROM wiki_log ORDER BY id DESC LIMIT 500)"
                )
                con.commit()
            finally:
                con.close()
    except Exception:
        pass


def status() -> Dict[str, Any]:
    ensure_db()
    with _lock:
        con = _connect()
        try:
            n = con.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            r = con.execute("SELECT COUNT(*) FROM roots WHERE enabled=1").fetchone()[0]
            e = con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
        finally:
            con.close()
    try:
        from pocket.wiki_treesitter import treesitter_status

        ts = treesitter_status()
    except Exception:
        ts = {"available": False}
    return {
        "ok": True,
        "schema": "pocket.infinite_wiki.v1",
        "db": str(DB_PATH),
        "nodes": n,
        "roots": r,
        "edges": e,
        "watcher": _watch_started and _watch_thread is not None and _watch_thread.is_alive(),
        "treesitter": ts,
        "tools": [
            "get_file_profile(path)",
            "read_file_lines(path, start, end)",
            "find_symbol(name)",
            "goto_definition(name, from_path)",
            "search_profiles(query)",
            "index_tree(root)",
        ],
    }


def ensure_watcher(*, interval_sec: float = 8.0) -> Dict[str, Any]:
    """Autonomous updates: poll mtimes of known nodes + roots."""
    global _watch_started, _watch_thread
    ensure_db()
    if _watch_started and _watch_thread and _watch_thread.is_alive():
        return {"ok": True, "running": True}
    _watch_stop.clear()

    def loop():
        while not _watch_stop.is_set():
            try:
                _watch_tick()
            except Exception as e:
                _log("watch_error", str(e)[:200])
            for _ in range(int(max(2, interval_sec))):
                if _watch_stop.is_set():
                    break
                time.sleep(1)

    _watch_thread = threading.Thread(target=loop, name="infinite-wiki-watch", daemon=True)
    _watch_thread.start()
    _watch_started = True
    _log("watcher", "started")
    return {"ok": True, "running": True, "interval_sec": interval_sec}


def _watch_tick() -> None:
    """Reindex stale nodes; light scan of roots for new files."""
    ensure_db()
    paths: List[str] = []
    with _lock:
        con = _connect()
        try:
            rows = con.execute(
                "SELECT path FROM nodes WHERE kind='file' ORDER BY updated_at ASC LIMIT 80"
            ).fetchall()
            paths = [r["path"] for r in rows]
            roots = con.execute("SELECT path FROM roots WHERE enabled=1").fetchall()
            root_paths = [r["path"] for r in roots]
        finally:
            con.close()
    changed = 0
    for p in paths:
        try:
            r = reindex_if_stale(p)
            if r.get("changed"):
                changed += 1
        except Exception:
            pass
    # opportunistic: index a few new files under roots
    for rp in root_paths[:3]:
        try:
            base = Path(rp)
            if not base.is_dir():
                continue
            count = 0
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
                for fn in filenames:
                    if Path(fn).suffix.lower() not in {
                        ".py",
                        ".js",
                        ".ts",
                        ".tsx",
                        ".rs",
                        ".md",
                    }:
                        continue
                    fp = Path(dirpath) / fn
                    with _lock:
                        con = _connect()
                        try:
                            exists = con.execute(
                                "SELECT 1 FROM nodes WHERE path=?", (str(fp.resolve()),)
                            ).fetchone()
                        finally:
                            con.close()
                    if exists:
                        continue
                    card = build_profile(fp)
                    if card.get("ok"):
                        _upsert_node(card)
                        changed += 1
                        count += 1
                    if count >= 5:
                        break
                if count >= 5:
                    break
        except Exception:
            pass
    if changed:
        _log("watch_tick", f"changed={changed}")


def agent_tools_doc() -> str:
    return (
        "# Infinite Wiki tools (use these — do not dump whole files)\n\n"
        "1. `get_file_profile(path)` → Profile Card (sections, symbols+lines, deps)\n"
        "2. Inner monologue: pick line ranges from the card\n"
        "3. `read_file_lines(path, start, end)` → only those lines\n"
        "4. `find_symbol(name)` / `goto_definition(name, from_path=…)` → navigate\n"
        "5. `search_profiles(query)` → locate files by meaning\n"
        "6. After edits, watcher reindexes nodes + embeddings automatically\n"
    )


def run_wiki_job(prompt: str, *, cwd: str = "", job: Optional[Dict] = None) -> Tuple[str, str, str]:
    """Natural language → wiki tool dispatch for desk sessions."""
    text = (prompt or "").strip()
    low = text.lower()
    roots = [cwd] if cwd else None

    if low in ("help", "tools", "status", ""):
        st = status()
        return agent_tools_doc() + "\n" + json.dumps(st, indent=2), "", "infinite_wiki"

    m = re.match(r"profile\s+(.+)$", text, re.I) or re.match(
        r"get_file_profile\s*\(?\s*['\"]?(.+?)['\"]?\s*\)?\s*$", text, re.I
    )
    if m:
        card = get_file_profile(m.group(1).strip().strip("'\""), roots=roots)
        return json.dumps(card, indent=2), "" if card.get("ok") else card.get("error", ""), "infinite_wiki"

    m = re.match(
        r"read(?:_file)?_?lines?\s+(.+?)\s+(\d+)\s*(?:-|:|\s)\s*(\d+)\s*$",
        text,
        re.I,
    )
    if m:
        out = read_file_lines(m.group(1).strip().strip("'\""), int(m.group(2)), int(m.group(3)), roots=roots)
        return out.get("text") or json.dumps(out, indent=2), "" if out.get("ok") else out.get("error", ""), "infinite_wiki"

    m = re.match(r"symbol\s+(.+)$", text, re.I) or re.match(r"find_symbol\s+(.+)$", text, re.I)
    if m:
        return json.dumps(find_symbol(m.group(1).strip()), indent=2), "", "infinite_wiki"

    m = re.match(r"(?:goto|go\s*to|def(?:inition)?)\s+([A-Za-z_][\w]*)(?:\s+in\s+(.+))?$", text, re.I)
    if m:
        return (
            json.dumps(
                goto_definition(m.group(1).strip(), from_path=(m.group(2) or "").strip().strip("'\""), roots=roots),
                indent=2,
            ),
            "",
            "infinite_wiki",
        )

    m = re.match(r"index\s+(.+)$", text, re.I)
    if m:
        return json.dumps(index_tree(m.group(1).strip().strip("'\""), max_files=500), indent=2), "", "infinite_wiki"

    m = re.match(r"search\s+(.+)$", text, re.I)
    if m:
        return json.dumps(search_profiles(m.group(1).strip()), indent=2), "", "infinite_wiki"

    # default: search + show tools
    hits = search_profiles(text, limit=8)
    return (
        agent_tools_doc()
        + "\n## Search results\n"
        + json.dumps(hits, indent=2),
        "",
        "infinite_wiki",
    )
