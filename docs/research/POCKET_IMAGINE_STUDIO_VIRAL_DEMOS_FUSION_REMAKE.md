# Imagine Studio, Viral Software Demos, and Fusion Remake
## Research Report for the POCKET Platform (Not In-App Copy)

**Document ID:** INL-2026-POCKET.IMAGINE.VIRAL.001  
**Lab:** ItsNotAI Labs / Medina Tech Labs  
**Date:** 2026-07-27  
**Audience:** Operator (you), Grok / Codex / Claude agents on the host API  
**Location of this file:**  
`C:\Users\Medin\OneDrive\Documents\POCKET_Research\ImagineStudio_ViralDemos_FusionRemake\`

---

## 0. Why this paper exists

POCKET already captures the host (SPECULUM), understands the screen (OCULUS fusion: UIA + OCR + pure visual), and can export “viral” clips. Early exports were **flat phone silhouettes** with a **destructive crop** of a desktop recording. That is not what people mean when they say:

> “We made this in one prompt.”

What they mean is a **composition system** that looks like the demos flooding X right now: real UI clarity, motion that teaches, and (when needed) a **3D device** that holds a *correct* screen — not a stretched mess inside a 2D rectangle.

This report is the research backbone for:

1. **Viral demo styles that actually work on X** (taxonomy + craft rules).  
2. **Imagine Studio** — a full image / media studio product, not more clutter inside the POCKET desk shell.  
3. **Fusion remake** — page symbols that not only *name* UI, but can **rebuild** it and step toward **3D / video / animation**.  
4. **Platform rule:** every new capability is API-first and updates the whole host surface, so agents cannot be replaced by “just ask normal Claude.”

---

## 1. What “viral software demos on X” actually are

### 1.1 Two families (do not mix them up)

| Family | What you see | Examples (public craft) | Core rule |
|--------|----------------|-------------------------|-----------|
| **A. Screencast polish** | Real product UI, full or zoomed frame | Notion Formulas 2.0, Figma FigJam AI, Slack Canvas, Taskade | Content is king; chrome is minimal |
| **B. Device showcase** | Floating 3D phone / laptop; screen is glass | Rotato, Protato, BrandBird, App Launch Flow style | Device is a stage; screen must be letterboxed correctly |

Family A is what most **Claude / Grok / Cursor** product posts look like: cursor moves, UI reacts, captions hit hard, 15–45 seconds.

Family B is what **app marketers** use: dark studio gradient, soft shadow, slight tilt / orbit, glass reflections, correct phone proportions.

**Failure mode we hit before:** using Family B *shape* with Family A *source* and a **cover-crop** that destroys the UI. That is why “the screen shape was fine but the inside made no sense.”

### 1.2 Craft rules (portable checklist)

1. **Hook in 2 seconds** — one claim or one surprising UI move.  
2. **Show, don’t narrate** — real UI; text overlays only for labels / CTA.  
3. **Preserve aspect of the product surface** — letterbox / pad into the device glass; never force-fill if it warps text.  
4. **One idea per beat** — scroll, click, result; not a 4-minute tour.  
5. **Silent-readable** — large captions; many people watch muted.  
6. **End card** — product name + one CTA.  
7. **Length** — 15–45s for X; 9:16 for Reels/Shorts; 16:9 for timeline / web ads.

### 1.3 Tools people use (industry baseline)

- **Screen Studio** — auto-zoom, cursor polish, Mac device framing.  
- **Rotato / Protato / BrandBird** — 3D device mockups from screenshots/video.  
- **FocuSee-class** tools — auto-zoom, spotlight, captions for short demos.  
- **Pure AI posts** — “one prompt” is usually: strong product already exists + template pack + short clip.

**Platform implication:** POCKET must own **capture → understand → compose → export** as one API, not “export a bezel PNG.”

---

## 2. Inventory: which of *your* builds becomes Imagine Studio

We scanned OneDrive / Documents / Desktop / organism-ai / AIEOSpro.

### 2.1 Best seed: Creative Muse (organism-ai)

**Path:** `C:\Users\Medin\OneDrive\organism-ai\creative-muse.zip`  
**Seeded into:** `C:\Users\Medin\OneDrive\imagine-studio\seed-creative-muse\`

What it already models:

- Image engines catalog (Stable Diffusion / DALL-E style slots)  
- Music engines catalog  
- Golden-ratio composition helpers  
- Creation history records (artId, seed, dimensions, quality)

It is **not** yet a full layered photo editor — but it is the right *creative orchestration* brain for Imagine Studio.

### 2.2 Related but different products (do not force into POCKET UI)

| Build | Path | Role |
|-------|------|------|
| Sovereign Forge Studio | `...\AIEOSpro\sovereign-forge-studio\` | Code / ICP IDE shell — **not** image studio |
| Deployinstudio | `...\AIEOSpro\Deployinstudio\` | Buildsafe package only |
| command-platform | `...\command-platform\` | Sharp-based image resize for deploy assets |
| CAPSULA / Expo Orbit tree | Documents\CAPSULA | Device install / orbit — mobile ops, not editing |
| POCKET video_studio | `pocket-os\src\pocket\video_studio.py` | Viral export engine (being upgraded) |
| POCKET page_renderer | fusion symbol graph | Input to remake + 3D scene |

### 2.3 Product split (so we do not bloat one window)

```
POCKET (host co-pilot API)
  · OCULUS perception / page symbols / stream
  · SPECULUM record
  · STUDIO compose viral demos (calls Imagine compositions)
  · Agents / campaigns / bridge

Imagine Studio (full image + media studio product)
  · Layers, masks, generate, edit, remake from symbols
  · 3D device scenes, mockup stills + video
  · Exports back into POCKET /v1/studio and agent packs
```

**Doctrine:** Imagine Studio is a **first-class product folder + API surface**, referenced by POCKET — not a pile of buttons dumped into the desk UI.

---

## 3. Why flat phone frames fail (and how real 3D mockups work)

### 3.1 What we did wrong

1. Crop desktop landscape **to fill** 9:16 (`force_original_aspect_ratio=increase` + center crop).  
2. Draw a **2D rounded rectangle** “bezel” on top.  
3. Dump captions on the cropped chaos.

Result: wrong content, wrong scale, no depth, no studio lighting. Not viral — just branded crop.

### 3.2 What Rotato-class pipelines do

1. **Content stage:** screenshot or video kept **readable** (contain / letterbox into glass).  
2. **Device mesh / matte:** realistic proportions, thickness, camera notch or Dynamic Island, home indicator.  
3. **Scene:** gradient or soft environment, contact shadow, ambient occlusion under device.  
4. **Camera:** slight perspective / tilt / slow orbit (even a few degrees sells “3D”).  
5. **Light:** specular edge + optional reflection plane.  
6. **Export:** 9:16 / 1:1 / 16:9 masters.

### 3.3 What Screencast-polish pipelines do (no phone)

1. Full product window or clean region capture.  
2. Auto-zoom toward pointer / active control.  
3. Smooth cursor, click flashes.  
4. Lower-thirds + end card.  
5. Optional subtle background blur — **not** a fake phone.

POCKET must support **both** as named presets, not one broken hybrid.

---

## 4. Fusion modeling → remake → 3D / video

### 4.1 What fusion already gives us

From page render / understand:

- **UIA symbols** — kind, text, bbox, click, automation_id, invokable  
- **OCR lines** — text, optional bbox/click  
- **Visual regions** — edge density, hotspots  
- **page_text** — agent-readable dump  
- **primary_modality** — which channel is trustworthy

This is a **scene graph of the glass**, not a JPEG.

### 4.2 Intermediate Representation (IR) for remake

```
ScreenIR
  size: [W,H]
  windows: [...]
  nodes: [
    { id, kind, text, bbox, style_hints, source, click }
  ]
  reading_order: [...]
  palette: [...]
  action_hints: [...]
```

**Remake levels:**

| Level | Output | Use |
|-------|--------|-----|
| L0 Observe | symbols + brief | agents act on host |
| L1 Wireframe | HTML/CSS skeleton of layout | docs, a11y, rebuilds |
| L2 Styled remake | approximate UI clone | prototypes, demos |
| L3 Scene graph 3D | device + plane + UI texture | viral mockups |
| L4 Motion | keyframes / scroll / click paths | animations & demos |

### 4.3 Research anchors (public literature)

- **Screen Parsing** (Wu et al.) — reverse engineer UI structure from pixels.  
- **UI2Code / UI-to-code** lines of work — screenshot → executable frontend; modern variants treat it as iterative visual optimization, not one-shot.  
- Industry reverse-engineering blogs — screenshot → wireframe → code as a staged pipeline.

**POCKET edge:** we are not screenshot-only. We fuse **OS accessibility truth** with OCR and visual structure. Normal chat models get a picture; we get a **host-grounded symbol graph** with click targets.

### 4.4 3D step (practical, local)

Without shipping Blender by default:

1. Map UI plane to a textured rectangle in a simple scene (Pillow composite + perspective).  
2. Optional: export glTF-lite / Three.js scene JSON for web preview.  
3. Optional later: Blender / USD if installed.

**Agents call:** `POST /v1/fusion/remake` then `POST /v1/studio/render` with preset `rotato_phone` / `x_screencast`.

---

## 5. Imagine Studio product definition

### 5.1 Jobs to be done

1. Generate / edit stills (prompt + layers + masks).  
2. Rebuild UI from fusion IR.  
3. Place assets into **viral device / web scenes**.  
4. Export stills + MP4 packs agents and humans can post.  
5. Stay callable by **one POCKET API** so Grok / Codex / Claude share the same tools.

### 5.2 Module map

```
imagine-studio/
  seed-creative-muse/     # your existing Creative Muse engine
  docs/                   # product notes
  (runtime lives also in pocket-os as pocket.imagine_studio)

pocket-os/src/pocket/
  imagine_studio.py       # layers, generate hooks, composition API
  fusion_remake.py        # symbols → IR → HTML remake + scene
  video_studio.py         # viral presets (rotato_phone, x_screencast, macbook_web)
  page_renderer.py        # micro symbols (input)
```

### 5.3 API surface (unified)

```
GET  /v1/api                         # master catalog
GET  /v1/vision/page                 # fusion symbols
POST /v1/fusion/remake               # IR + HTML remake + scene graph
POST /v1/imagine/compose             # still composition / edit
POST /v1/studio/render               # viral video presets
POST /v1/studio/auto                 # pack for X / web / clean
```

---

## 6. Platform doctrine: do not get lost in micros

### 6.1 The failure pattern

Ship a clever micro (flat bezel, extra button) → demo it once → never wire agents → never update catalog → user cannot tell POCKET from “paste a screenshot into Claude.”

### 6.2 The rule

Every deliverable must update **all** of:

1. **Core module** (real code)  
2. **HTTP route** on `/v1/...`  
3. **`GET /v1/api` catalog**  
4. **Skill id** for orchestrator  
5. **Persistence** under `~/.pocket/` so agents resume  
6. **Docs / research** when the idea is strategic  

### 6.3 Differentiation vs “normal Claude / normal Grok”

| Capability | Chat-only LLM | POCKET host platform |
|------------|---------------|----------------------|
| See live UI with OS names | partial screenshot guess | UIA + OCR + visual fusion |
| Click real controls | no | vision click / orchestrator |
| Record full desktop | no | SPECULUM |
| Stream understanding | no | `/v1/vision/stream` |
| Remake from grounded IR | freeform guess | `/v1/fusion/remake` |
| Viral compose from *your* recording | manual CapCut | `/v1/studio/*` |
| Multi-agent desk workers | no | Latin workers + campaigns |

---

## 7. Implementation plan (executed alongside this paper)

### Phase A — Truth in viral export (now)

- New presets: `rotato_phone`, `x_screencast`, `macbook_web`  
- Content **contain** into glass; studio gradient; shadow; perspective tilt  
- Retire “crop to death + flat bezel” as default  

### Phase B — Fusion remake (now)

- `fusion_remake.py`: symbols → IR → HTML remake + scene JSON  
- API + skill `fusion_remake`  

### Phase C — Imagine Studio product home (now)

- Repo: `OneDrive\imagine-studio` with Creative Muse seed  
- Runtime bridge in `pocket.imagine_studio`  

### Phase D — Next (not blocking)

- True glTF / Three.js orbit previews  
- Auto-zoom from pointer path in SPECULUM records  
- Layered editor UI as separate product window (not stuffed into desk)  

---

## 8. Evaluation criteria (what “good” means)

1. **Readable glass:** body text on screen remains legible after mockup.  
2. **Device depth:** shadow + perspective sell 3D without real Blender.  
3. **Screencast clarity:** x_screencast looks like a Notion/Figma X post, not a phone toy.  
4. **Remake fidelity:** ≥ major named buttons/links present in HTML IR.  
5. **Agent usability:** one JSON from `/v1/api` lists every call.  
6. **No UI dump:** research lives in files; product UI stays lean.

---

## 9. File map (where everything lives)

| Artifact | Path |
|----------|------|
| This research (MD) | `Documents\POCKET_Research\ImagineStudio_ViralDemos_FusionRemake\POCKET_IMAGINE_STUDIO_VIRAL_DEMOS_FUSION_REMAKE.md` |
| This research (PDF) | same folder, `.pdf` |
| Imagine Studio product | `OneDrive\imagine-studio\` |
| Creative Muse seed | `imagine-studio\seed-creative-muse\` |
| POCKET runtime | `OneDrive\pocket-os\src\pocket\` |
| Studio exports | `~\.pocket\studio\exports\` |
| Fusion remake out | `~\.pocket\imagine\remakes\` |

---

## 10. Closing

Viral demos are not “draw a phone.” They are **composition + truth**.  
Imagine Studio is not “another tab.” It is the **media product** that Creative Muse already pointed at.  
Fusion remake is not OCR trivia. It is the bridge from **host reality** to **rebuild → 3D → motion**.

Update the platform every time — or it is just another script someone can replace with a chat window.

---

*End of report. ItsNotAI Labs / Medina Tech Labs — 2026.*
