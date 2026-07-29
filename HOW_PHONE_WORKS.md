# How the phone actually works

## Product

**POCKET** is a remote control for coding agents on your PC.

1. Phone opens the LAN URL.
2. You type a real task and pick **Codex** (or Claude / shell).
3. PC worker runs the agent in a real project folder.
4. Phone polls until **done** and shows the full agent output.
5. Files on the PC are actually changed.

## Not this

- Fake instant “AI reply” with no PC work
- Dead mailbox / queue you never see again
- Broken public tunnel as the only path

## URLs

| Who | URL |
|-----|-----|
| Phone (same Wi‑Fi) | `http://192.168.12.127:8787/` |
| PC browser | `http://127.0.0.1:8787/` |

## Proven on this machine

- Shell job: done in ~1s, real `dir` output from `pocket-os`
- Codex job: done, engine=`codex`, OneDrive project bridged via `P:\` SUBST
- File `PHONE_AGENT_PROOF.md` written and updated by the agent

## Windows + OneDrive note

Codex sandbox fails on raw `...\OneDrive\...` paths (`os error 2`).  
POCKET auto-maps those folders with `subst` (e.g. `P:\`) so Codex can write for real.

## Claude

If you install Claude Code CLI and it is on PATH, pick **Claude** mode.  
Same phone UI, different engine.
