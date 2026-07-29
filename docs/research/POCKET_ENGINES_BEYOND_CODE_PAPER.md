# Engines Beyond Code: What Codex, Grok, Claude, and GUPPY Do on a Working Computer

**Paper ID:** INL-2026-POCKET.ENG.003  
**Lab:** ItsNotAI Labs · Medina Tech Labs  
**Product:** POCKET Multi-Agent Platform  
**Status:** Doctrine + implementation notes  

---

## Abstract

Coding agents are marketed as “write code.” On an operator host with POCKET, engines do more: plan, review, open the desk, research the web, resume conversations, deploy static apps, and run silent multi-step host control. This paper catalogs **engine roles beyond code**, names each engine, and assigns commercial claims to ItsNotAI Labs / Medina Tech Labs.

## 1. Engine registry (named)

| Engine | Primary strength | Beyond code |
|--------|------------------|-------------|
| **Codex** | Implementation in workspace | Multi-turn **resume per POCKET tab**; repo health; test loops; file ops; OneDrive SUBST bridge |
| **Grok** | Fast coding + plan density | Planning AI; handoff packages; research pulls into inbox; situational whole-plan context |
| **Claude** | Careful prose & review | Code review, docs, security-minded critique when CLI present |
| **Plan / Ask** | Structure | Roadmaps without writes |
| **Shell / WSL / Term** | Host truth | Diagnostics, builds, long-lived PowerShell |
| **Desktop** | Glass | 50+ apps, Edge+URL, Copilot |
| **Web** | Evidence | search / fetch / research without model keys |
| **NEXUS** | Federated workers | MERIDIAN catalog (Bridge, Cipher, …) |
| **GUPPY / Doer** | Autonomy | ≤10 steps, lookup+bring-back, daily schedules |
| **Squad / Router** | Product API | Multi-agent chains & routing |

## 2. Codex on a working computer

With session resume bound to a POCKET tab:

1. **Conversation continuity** — second message is not a cold start.  
2. **Workspace agency** — edit, run, summarize diffs.  
3. **Bridge** — OneDrive paths mapped for sandbox friendliness.  
4. **Not for** — free-form “open Discord every hour” (that is GUPPY).

**Claim:** Codex is the **implementation engine** of the lab stack; POCKET is the **session fabric**.

## 3. Grok on a working computer

1. Planning-only modes  
2. Coding via `grok --single` when installed  
3. Dense research packages for operators (“check pocket”)  
4. Handoff without auto-code  

**Claim:** Grok is the **situation engine** — dense context for humans and later agents.

## 4. Claude on a working computer

When CLI exists: review, docs, careful implementation fallback. When missing: honest degrade to Codex/plan.

## 5. GUPPY / Python workers (non-LLM path)

The lab explicitly claims a **second intelligence class**:

- Not a frontier model loop  
- Deterministic multi-step effector  
- Opens Copilot and **returns** public web text  
- Background schedules  

This is how POCKET can feel like “the AI went to my desktop” **without** spending coding tokens per click.

## 6. What “go to my desktop” means (system)

Operator desire: *the AI I’m talking to opens my apps and the internet.*

Implementation layers:

1. **Desk UI** (browser or future packaged shell) → messages  
2. **Host runtime** on PC → jobs  
3. **Effectors** → desktop / web / CLI engines  
4. **Phone remote** → same host  

Vision path to “desktop app”: wrap the same runtime (see host-copilot paper)—the intelligence is already host-local.

## 7. Conclusion

Engines beyond code are not marketing fluff. They are **named, routed, metered modes** in POCKET. The lab claims the full registry—and the split between **LLM coding engines** and **Python desk workers**—as core IP of the platform.

---

*ItsNotAI Labs / Medina Tech Labs*
