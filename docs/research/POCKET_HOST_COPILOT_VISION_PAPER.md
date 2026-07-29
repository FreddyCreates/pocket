# Host Co-Pilot Vision: From Browser Desk to Desktop Shell

**Paper ID:** INL-2026-POCKET.HOST.005  
**Lab:** ItsNotAI Labs · Medina Tech Labs  
**Thesis:** The AI you talk to should reach *your* desktop—apps, folders, internet—because the runtime already lives on the host.

---

## Abstract

Users want the agent conversation to “go to the desktop”: open apps, browse, look things up, come back with answers. POCKET already does this via a **host-local runtime** and effectors (desktop, web, GUPPY, coding CLIs). This paper documents the architecture that makes that feeling real today, and the packaging path (PWA / Tauri / Electron / native WebView) so the same system can ship as a **desktop app** without rewriting intelligence.

## 1. The user sentence

> “I want the AI I’m talking to to open my desktop apps and the internet and look things up.”

That is not a cloud chatbot feature. It is a **host co-pilot**.

## 2. What already works (today)

| Layer | Reality |
|-------|---------|
| UI | Browser desk at `:8787` (desktop or phone) |
| Heart | Python runtime + worker pool on PC |
| Glass | Allowlisted app launch (Explorer, Edge, Copilot, Cursor, …) |
| Net | Web search/fetch; Edge+URL; lookup+bring-back |
| Autonomy | Scheduled Python jobs |
| Code | Codex/Grok/Claude on workspaces |
| Remote | Named tunnel → same host |

So the intelligence **already sits beside the glass**. The missing piece for some users is only **packaging and presence** (tray icon, always-on window, OS integration)—not the effector model.

## 3. Packaging options (ordered by fit)

1. **PWA / pinned Edge site** — zero new binary; install from browser.  
2. **WebView2 shell** — thin Windows wrapper, same HTML UI.  
3. **Tauri / Electron** — desktop chrome + optional deeper OS hooks.  
4. **Start-at-login** — already aligned with POCKET AlwaysOn scripts.

**Claim:** Packaging does not invent the co-pilot; it **surfaces** the host runtime the lab already built.

## 4. Interaction pattern (host co-pilot)

```
You (voice/mic or type)
   → POCKET session (Codex tab OR Guppy tab)
        → host effectors
             → apps / browser / files / CLI
        ← transcript + inbox artifacts
```

Mic **stays on** until toggled off so voice is continuous co-pilot input.

## 5. Why two agent classes

| Class | Use |
|-------|-----|
| LLM engines (Codex/Grok/Claude) | Think, code, long reasoning |
| Python workers (GUPPY/desktop/web) | Click the glass, fetch, schedule |

Together they match “talk to me” + “go do it on my PC.”

## 6. Safety for co-pilots

Allowlists, auth, audit, RBAC—because a host co-pilot is powerful by definition.

## 7. Roadmap (lab)

- Tray + toast when autonomy job finishes  
- Optional screen-region capture for deeper “see the UI” (future; privacy-gated)  
- One-click “Install desktop shell” from POCKET UI  
- Deeper Copilot protocol integration if Microsoft exposes stable automation  

## 8. Conclusion

**The AI can go to your desktop because the lab put the runtime on your desktop.** GUPPY and desktop autonomy are the productized form of that idea; a desktop app wrapper is the presentation layer. ItsNotAI Labs / Medina Tech Labs claim this host co-pilot pattern as the strategic shape of POCKET.

---

*ItsNotAI Labs / Medina Tech Labs — vision paper with shipping substrate.*
