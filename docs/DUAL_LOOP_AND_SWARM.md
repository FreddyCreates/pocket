# Dual loop, Work Studio, always-on swarm, world model

## Architecture

```text
                 ┌─────────────────────────┐
  User chat ───► │ CORTEX (System 1)       │  beautiful dialogue / code explanations
                 │ streams response text   │
                 └───────────┬─────────────┘
                             │ brief yield
                 ┌───────────▼─────────────┐
                 │ SUBCORTEX (System 2)    │  silent daemon
                 │ world model SQLite      │  fact-check · archetypes · prose · syntax
                 │ narrative timeline      │  writes before user finishes reading
                 └───────────┬─────────────┘
                             │
                 ┌───────────▼─────────────┐
                 │ ALWAYS-ON SWARM         │  rotates work loops / use cases
                 │ build_loop pulses       │  host stays productive
                 └─────────────────────────┘
```

## World model datasets

| Target | Table | Purpose |
|--------|-------|---------|
| Narrative Archetype Graph | `archetypes` | Tropes, arcs, plot beats |
| Literary Prose Standards | `prose_standards` | Style exemplars (Gutenberg-ready) |
| Factual Common Sense | `facts` | S-P-O triples (Wikidata/ConceptNet shape) |
| Syntactic Specifications | `syntax_specs` | Python/JS/Rust/ICP API fidelity |

DB: `~/.pocket/world_model/world.db`

## Work types & loops

- **Work type** = atomic labor (Plan, Code, Test, Narrative, WSL, …) with layer = cortex|subcortex  
- **Work loop** = ordered chain; generate from plain English  

UI: `/work` · API: `/v1/work-studio`, `POST /v1/work-loops/generate`

## Always-on swarm

```http
POST /v1/swarm/start
POST /v1/swarm/pulse
POST /v1/swarm/stop
GET  /v1/swarm
```

Auto-starts with host boot (ensure_embedded_worker).

## Dual loop

```http
POST /v1/dual  {"goal":"…"}
```

Desk mode: **Dual loop**.
