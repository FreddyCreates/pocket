# POCKET vs Emergent — parity and beyond

**Competitor:** [Emergent](https://emergent.sh/) — agentic vibe-coding platform (multi-agent plan/design/code/test/deploy).

**POCKET stance:** Match conversation→ship multi-agent pipelines, then **surpass** with sovereign host execution, WSL, phone remote, mesh subagents, Novae hands, and founder/market isolation.

## Capability matrix

| Feature | Emergent | POCKET |
|---------|----------|--------|
| Prompt → full-stack app | yes | yes — `build_loop` |
| Specialized multi-agents | yes | yes — PLANNER…SHIP + Latin/mesh |
| Custom agents + tools + sub-agents | yes | yes — `custom_agents` |
| Test & fix loops | yes | yes — retries until green/cap |
| Deploy / preview | yes (their cloud) | yes — static deploy on host |
| Git | GitHub sync (plans) | sovereign git + export |
| Runs on **your** PC | no | **yes** |
| Phone remote desk | no | **yes** `/phone` |
| Native WSL agent | no | **yes** |
| Market seat ≠ founder disk | n/a cloud | **hard isolation** |
| Desktop embodiment | no | **yes** |
| Mesh hashed bus | no | **yes** |
| Vendor lock-in required | yes | **no** (self-host) |

## Real use cases (executable)

```text
GET  /v1/use-cases
GET  /v1/parity
POST /v1/build-loops   { "use_case": "fullstack_web_app", "wait": true }
POST /v1/custom-agents { "name": "SupportAgent", "tools": ["files","web","mesh"] }
```

Desk modes: **Build** · **Use cases** · **Custom agent** · **Emergent** (alias).

Examples:

- `use_case:fullstack_web_app`
- `use_case:saas_dashboard`
- `use_case:api_microservice`
- `use_case:test_troubleshoot`
- `use_case:multi_agent_swarm`
- `use_case:wsl_native_build`
- `use_case:host_automation`

## Loop lifecycle

```text
plan → design → implement → test → fix* → ship → done
         (* retries capped, managed by build_loop thread)
```

Projects land under `~/.pocket/build_loops/<id>/project/`.

## Why this is “more”

Emergent ships apps in **their** cloud.  
POCKET ships **real files on your machine**, remote-controllable from phone, with Linux (WSL) and host hands Emergent never has — while still offering the multi-agent ship factory they market.
