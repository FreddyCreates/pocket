# Infinite Wiki — hierarchical codebase engine

## Problem

Loading a 10,000-line file into a model context is expensive and lossy.  
Agents should **navigate** code like a wiki, not swallow it.

## Agent loop

```text
1. get_file_profile(path)
      → Profile Card (metadata, sections, deps, symbols + line numbers)

2. Inner monologue
      → "I need Method shouldUseDarkLayer at L174"

3. read_file_lines(path, start=170, end=190)
      → only ~20 lines of interest

4. write minimal change

5. Background watcher
      → updates nodes table + re-embeds vectors when mtime changes
```

## Tools

| Tool | Purpose |
|------|---------|
| `get_file_profile(path)` | Tiny Profile Card |
| `read_file_lines(path, start, end)` | High-resolution slice |
| `find_symbol(name)` | Locate symbol across index |
| `goto_definition(name, from_path=…)` | Cross-file import resolve + symbol |
| `search_profiles(query)` | Vector/lexical search over cards |
| `index_tree(root)` | Bulk index a codebase |
| `inject_wiki_context(prompt)` | Auto-attach cards for paths/symbols |

## Auto-inject into coding jobs

Codex / Grok / Claude / Novae / Plan / Archon desk messages automatically get Infinite Wiki
Profile Cards when the prompt mentions paths or symbols — so models stay hierarchical by default.

### Sellable API (`POST /v1/ai/chat`)

Same inject runs for coding agents (`coder`, `grok_coder`, `architect`, `planner`, …):

```http
POST /v1/ai/chat
Authorization: Bearer sk_pocket_…
{
  "agent": "coder",
  "messages": [{"role":"user","content":"Fix ensure_embedded_worker in C:/.../server.py"}],
  "inject_wiki": true,
  "cwd": "C:/Users/.../pocket-os/src"
}
```

Response includes `pocket.infinite_wiki: { injected, chars }`.

### Optional tree-sitter

```bash
pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript
```

Profiles then set `ast_engine: "tree-sitter"` for tighter ranges. Without packages, heuristic AST is used.

### Desk UI

Profile Card JSON in chat renders as an interactive card:

- **Open definition** on each symbol (goto + line slice)
- **Read head** · **Copy path**
- `goto` results render a definition hit list

## API

```http
GET  /v1/wiki
POST /v1/wiki/profile   {"path":"..."}
POST /v1/wiki/lines     {"path":"...","start":170,"end":190}
POST /v1/wiki/symbol    {"name":"ensure_embedded_worker"}
POST /v1/wiki/search    {"q":"orchestrator"}
POST /v1/wiki/index     {"root":".../src/pocket","max_files":2000}
```

## Storage

`~/.pocket/infinite_wiki/wiki.db`

- **nodes** — path, mtime, sha, sections, symbols, deps, profile_json, embedding  
- **edges** — import graph  
- **roots** — watched trees  

## Desk

Mode **Infinite Wiki** — natural language:

```text
help
profile C:\...\server.py
read_lines C:\...\server.py 300 340
symbol ensure_embedded_worker
index C:\...\src\pocket
search orchestrator
```

## Design note

Profile cards stay small; high-res reads are capped (default 200 lines).  
This is how models reason over multi-gig codebases without saturating context windows.
