# Cowork + Sovereign Forge

## Cowork (working mode, not plan)

Desktop **embodiment** for demos and non-deep-code work:

- Screen **record** (SPECULUM / ffmpeg when installed)
- Open apps / browser
- Screenshots + deliverable notes
- Proof packs under `~/.pocket/proofs/`

| | Plan | Cowork | Codex/Grok code |
|--|------|--------|-----------------|
| Purpose | Think / design | Do desk demos | Multi-file ship |
| Screen record | optional | first-class | optional |
| Tokens | low | low (host actions) | higher |

Desk: **Cowork** agent · presets include “Record demo”.

API: `POST /v1/cowork` · session mode `cowork`

## Sovereign Git

Repos live in the host vault (`E:/POCKET_MESH/vdisk/git` or `~/.pocket/git_vault`):

- `create repo my-app` → `git init` + `pocket.toml`
- `list repos`
- `export my-app` → zip under `~/.pocket/git_exports`
- Clone: `git clone "<path>"` (real git)

Companion site: **`/forge`**

API: `GET /v1/git/repos` · `POST /v1/git/create` · zip download routes

## Ghost math

Deterministic hash chains / phi / digests — **no LLM**.

Session mode `ghost` · `POST /v1/ghost`

## Screen record API

- `POST /v1/record/start` `{ "label": "demo" }`
- `POST /v1/record/stop`
- `GET /v1/record/status`
