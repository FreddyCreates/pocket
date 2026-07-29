# Pixel-to-Meaning on the Operator Host: Multimodal Screen Understanding for Host Co-Pilots

**A Full-Length Research Paper**

| Field | Value |
|-------|--------|
| **Title** | Pixel-to-Meaning on the Operator Host: Multimodal Screen Understanding for Host Co-Pilots |
| **Paper ID** | INL-2026-POCKET.PIX.FULL.001 |
| **Authors / Lab** | ItsNotAI Labs · Medina Tech Labs |
| **Product** | POCKET Multi-Agent Host Co-Pilot Platform |
| **Subsystem** | OCULUS Pixel Translator · Vision Core · Live Bridge |
| **Version** | POCKET 1.8+ |
| **Date** | 2026-07-27 |
| **Status** | Product-embedded empirical systems paper |
| **Keywords** | host co-pilot, screen understanding, UI Automation, OCR, pure visual saliency, multimodal fusion, agent perception, POCKET |

---

## Abstract

Large language models excel at language but are blind to the operator’s desktop unless an external perception stack is attached. We present the **POCKET Pixel Translator**, a host-local multimodal perception system that converts screen pixels and accessibility structure into agent-actionable meaning. Unlike OCR-only pipelines, the translator fuses three modalities—(1) **semantic UI text** from Windows UI Automation, (2) **optical character recognition** via Windows.Media.Ocr when available, and (3) **pure visual structure** (edge density, regional saliency, palette, mood)—and selects a **primary modality** with an explicit rationale. Empirical live capture on an operator workstation shows 200 accessibility-named controls and 37–53 OCR lines simultaneously, with the fusion policy correctly preferring semantic UI text for application chrome. The system is exposed as a first-class platform API (`/v1/vision/understand`, `/v1/pixel/text`), integrated into observe bridges and skill orchestration, enabling outer agents (Grok Build, Codex, phone clients) to *see* the glass and act through the same POCKET API. We argue this multimodal host perception is a fundable wedge relative to chat-only AI: it operationalizes signed-in browsers, real UI navigation, and commercial demo recording without requiring cloud screen streaming.

---

## 1. Introduction

### 1.1 Motivation

When an operator says “what do you see on my screen?”, a cloud chat model has no native answer. When they say “click the third link,” the model cannot resolve coordinates without a host sensory layer. Prior POCKET work established desktop allowlists, multi-step doers, browser mode, Latin workers, and orchestrated skills. Missing was a **principled, multimodal translator from pixels (and OS structure) to meaning**, with honesty about when text is *not* optimal.

### 1.2 Contributions

1. **Three-modality fusion** for host screen understanding: semantic UI, OCR, pure visual.  
2. **Primary modality selection** with human-readable `why_primary`.  
3. **Action hints** that route agents to click-by-name vs region click vs scroll.  
4. **Platform API integration** so Grok/Codex/phone share one perception path.  
5. **Empirical live observation** on a production operator host (this paper’s Section 6).  
6. **Positioning** of host co-pilot perception vs chat-only AI as product differentiation.

### 1.3 Scope and non-claims

We do **not** claim perfect OCR on every font. We do **not** claim end-to-end purchase automation. We **do** claim a production-usable sensory stack that prefers the right modality and exposes it over HTTP.

---

## 2. Related Work and Positioning

| Approach | Limitation |
|----------|------------|
| Chat LLM alone | No host pixels |
| Cloud browser automation | Wrong machine; no local signed-in apps |
| OCR-only | Misses named buttons; fails on dark sparse UIs |
| Accessibility-only | Misses painted text in canvases/images |
| Pure CV detection | Hard to ground to clickable names |

POCKET’s translator sits **on the operator host**, fuses modalities, and feeds **workers and live bridges** that already control Edge, Copilot, Outlook, and desktop apps under allowlists.

---

## 3. System Architecture

```
                    ┌─────────────────────┐
                    │  Clients            │
                    │  UI · Grok · Codex  │
                    │  Phone · API keys   │
                    └──────────┬──────────┘
                               │ HTTP /v1/*
                    ┌──────────▼──────────┐
                    │  POCKET Platform    │
                    │  Orchestrator       │
                    │  Bridge / Workers   │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  OCULUS             │
                    │  Pixel Translator   │
                    └───┬──────┬──────┬───┘
                        │      │      │
              semantic  │  OCR │  pure│
              UI text   │      │ visual
                        │      │      │
              UIA names │ Win  │ edges│
                        │ OCR  │ color│
                        └──┬───┴──┬───┘
                           │ fuse │
                    primary_modality
                    brief + action_hints
```

### 3.1 Capture

Full primary display capture via PIL `ImageGrab`, optional downscale (default max width 1280) for latency and token-friendly previews.

### 3.2 Modality A — Semantic UI text

Windows UI Automation enumerates on-screen named elements (Name, ControlType, bounding rectangle). This often **dominates OCR** for app chrome: Start, taskbar pins, “Pull requests,” Copilot, etc.

### 3.3 Modality B — OCR

- Prefer **Windows.Media.Ocr** via PowerShell/WinRT when present.  
- Optional **Tesseract** if installed.  
- Produces line list + plain text for documents and web bodies.

### 3.4 Modality C — Pure visual

Without reading glyphs:

- Mean RGB, brightness, contrast  
- 3×3 regional **edge density** (FIND_EDGES) → busy vs calm zones  
- Quantized palette  
- Mood (`dark_ui` / `bright_page` / `mixed`) and structure class  

Busy region centers become **click_xy** candidates when text fails.

### 3.5 Fusion policy

```
if semantic_count >= 15:
    primary = semantic_ui_text
elif ocr_count >= 8 and mood == bright_page:
    primary = ocr
elif semantic_count < 8 and ocr_count < 5:
    primary = pure_visual
elif ocr_count > semantic_count:
    primary = ocr
else:
    primary = semantic_ui_text or pure_visual
```

### 3.6 Action hints

- Links/buttons → `click_name`  
- Pure visual → `click_xy` on busiest region centers + `scroll_down`  
- Agents should **not** force OCR clicks when UIA already named the control.

---

## 4. Platform API Surface

| Method | Path | Role |
|--------|------|------|
| GET/POST | `/v1/vision/understand` | Full fusion |
| GET | `/v1/pixel/text` | Force text extraction (UI + OCR) |
| GET | `/v1/vision/observe` | Worker observe (understand default) |
| GET | `/v1/live/vision` | Continuous JPEG frames |
| POST | `/v1/vision/click` | Click by name via map |
| POST | `/v1/skills/run` | `{"skill":"understand"}` |
| POST | `/v1/bridge/{id}/observe` | Live bridge sensory packet |

Auth: Basic / `X-Pocket-Access` / `Bearer sk_pocket_…`.

**Invariant:** Outer agents (including Grok Build) should call these endpoints rather than private offline imports, so the public/platform path stays the only production path.

---

## 5. Integration with Workers and Bridges

### 5.1 Dynamic workers

Goal-conditioned loops call `observe()` each step, read `ui_names` / `action_hints`, then scroll, click, or screenshot. Memory persists under `~/.pocket/worker_brains/`.

### 5.2 Real-time bridge

Synchronous bridge:

1. `POST /v1/bridge/open` (optional record)  
2. `POST /v1/bridge/{id}/observe` → outer agent reads brief  
3. `POST /v1/bridge/{id}/act` with **agent-chosen** click/scroll  
4. Repeat  
5. `POST /v1/bridge/{id}/close`  

This enables *human-in-the-loop or LLM-in-the-loop* control without prewritten multi-app scripts.

### 5.3 Orchestrator

Skills `understand`, `pixel_text`, `see_screen` dispatch through the orchestrator so chat workflows can request perception as a first-class step.

---

## 6. Empirical Live Observation (Operator Host, 2026-07-27)

A live `understand()` call on the operator machine produced:

| Signal | Value |
|--------|--------|
| Primary modality | **semantic_ui_text** |
| Why | 200 named UIA controls — better than OCR for chrome |
| Semantic count | 200 elements; ~110 buttons; links include “Back to start” |
| OCR | **ok=true**, 37–53 lines (Windows OCR functional) |
| Pure visual | 1280×853, brightness ~41–49, mood mixed/dark, busy regions bottom-left and top-center |
| Window titles observed | Microsoft Edge (“Nexus Agentic IDE \| Google AI Studio…”), Notepad, Snipping Tool, Word, Media Player, Terminal-related pins |

OCR plain-text fragments referenced AI Studio / Nexus Agentic IDE UI copy, navigation labels (“Code”, “START…CHANNEL”), and chat-like content—consistent with a multi-window builder workstation, not a blank desktop.

**Interpretation for the outer agent:**  
The glass is a **dense dark productivity desk**. Taskbar and shell chrome dominate accessibility names. Content-heavy pixels appear in the Edge/Nexus region (OCR). Optimal control: **click by accessibility name** for OS/app chrome; **OCR brief** for document/web body; **visual hotspots** if both are sparse.

This section is deliberately empirical: the paper is grounded in a real host observation, not synthetic screenshots alone.

---

## 7. What This Enables That Chat-Only AI Cannot

1. **Signed-in host context** — Edge profiles, X, GitHub Desktop stay local.  
2. **Modality honesty** — Do not OCR a named Button if UIA already exposes it.  
3. **Commercial demos** — SPECULUM records while OCULUS samples frames.  
4. **Multi-client identity** — UI, Grok Build, Codex, phone hit the same `/v1` perception.  
5. **Fundable product shape** — “AI that sees and moves *your* computer” is a host co-pilot, not a chatbot skin.

---

## 8. Limitations and Future Work

| Limitation | Mitigation path |
|------------|-----------------|
| UIA may emphasize shell over in-page DOM | Prefer focused window; browser accessibility trees; optional DOM bridge |
| OCR noisy on small fonts | Upscale crop ROIs around busy regions |
| No full vision-language model on host by default | Optional local VLM later; fusion already separates concerns |
| Purchase automation | Scaffold only; human gate mandatory |

Future: ROI-cropped OCR on busiest regions; focused-window UIA only; VLM caption as fourth modality; remote VM host with identical `/v1/vision/*`.

---

## 9. Security and Safety

- Perception is **local**; frames stay under `~/.pocket/vision` unless the operator exposes the API.  
- Public tunnel requires auth (Basic / API key).  
- Click actions remain bound to allowlisted apps and bridge policy.  
- No automatic payment confirmation.

---

## 10. Related POCKET Subsystems

- Latin workers (ARCHON, OCULUS, PORTARIUS, …)  
- Orchestrator + 170+ skill suite  
- Dynamic workers (observe→decide→act)  
- Realtime bridge  
- Campaigns API  
- Host backend (local / remote VM scaffold)

---

## 11. Conclusion

The POCKET Pixel Translator treats the operator screen as a **multimodal signal**, not a single OCR dump. By fusing semantic accessibility text, OCR, and pure visual structure—and by publishing the result on the platform API—we enable outer agents to answer “what do you see?” with evidence and to choose actions that match the optimal modality. Live host experiments confirm simultaneous richness of UIA and OCR, with correct primary selection for app chrome. This perception layer is foundational to host co-pilots that create commercial value beyond chat: real glass, real signed-in sessions, real recordings, real multi-agent work on the machine people already own.

---

## Acknowledgments

Operator validation on the Medina Tech Labs workstation; continuous product pressure toward API-first, non-scripted workers.

## References (systems)

1. POCKET Platform API First (INL-2026-POCKET.API.015)  
2. Vision Workers First Class (INL-2026-POCKET.VIS.014)  
3. Orchestrator & Real-Time Vision (INL-2026-POCKET.ORCH.013)  
4. Microsoft UI Automation documentation  
5. Windows.Media.Ocr API  

## Appendix A — API Examples

```http
GET /v1/vision/understand
Authorization: Basic …

→ {
  "primary_modality": "semantic_ui_text",
  "why_primary": "UI Automation exposed 200 named controls…",
  "brief": "…",
  "action_hints": [{"action":"click_name","name":"…"}]
}
```

```http
GET /v1/pixel/text
→ { "text": "=== UI TEXT ===\n…\n=== OCR TEXT ===\n…", "primary_modality": "…" }
```

## Appendix B — Artifact Paths

| Artifact | Path |
|----------|------|
| Last understand JSON | `~/.pocket/vision/last_live_see.json` / `pixel_understand.json` |
| Live frame | `~/.pocket/live/frame.jpg` |
| UI map | `~/.pocket/vision/ui_map.json` |
| Research paper (md) | `docs/research/POCKET_PIXEL_TRANSLATOR_FULL_PAPER.md` |
| Research paper (pdf) | `docs/research/POCKET_PIXEL_TRANSLATOR_FULL_PAPER.pdf` |
| Notes copy | OneDrive Documents / notes path |

---

**© 2026 ItsNotAI Labs / Medina Tech Labs. Product-embedded research.**  
**End of paper.**
