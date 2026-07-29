# Browser Mode: Real-World Desk Control with Codex/Grok

**Paper ID:** INL-2026-POCKET.BRW.006  
**Lab:** ItsNotAI Labs · Medina Tech Labs  
**Status:** Production-embedded (v1.3+)

## Abstract

**Browser mode** is a separate POCKET session box that lets Codex or Grok work in the real world: signed-in Edge, X compose intents, Windows Copilot app, web Copilot, and Python lookup. Models compose; the host executes `[[POCKET …]]` tags. Tweets are never auto-published.

## Architecture

```
User (Browser session)
   → intent detect (lookup | research_tweet | tweet | open | freeform)
   → Python research (optional)
   → Codex / Grok compose (optional)
   → execute tags + open Edge (Default profile)
   → human confirms Post on X
```

## Safety

- Allowlisted apps  
- http(s) URL policy  
- X: intent URL prefill only; user posts  
- Clipboard assist for tweet text  

## API

- Desk mode: `browser`  
- `POST /v1/browser/run`  
- Headless agent: `browser`  

## Claim

ItsNotAI Labs / Medina Tech Labs claim Browser mode as the production bridge between coding engines and the operator glass.
