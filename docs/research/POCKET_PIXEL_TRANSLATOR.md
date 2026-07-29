# POCKET Pixel Translator — Text When Useful, Pure Visual When Better

**Paper ID:** INL-2026-POCKET.PIX.016  
**Agent:** OCULUS  
**Lab:** ItsNotAI Labs / Medina Tech Labs  

## Problem

Screen understanding is not always OCR. Buttons and app chrome already expose **semantic names**. Dense UIs need **layout/saliency**. Documents need **pixel→text**.

## Modalities

| Modality | Source | Best for |
|----------|--------|----------|
| **semantic_ui_text** | UI Automation names | Apps, links, buttons (often beats OCR) |
| **ocr** | Windows.Media.Ocr / tesseract | Documents, bright pages, plain text |
| **pure_visual** | Edge density, regions, palette | Sparse text, dark UIs, “where to look” |

`understand()` fuses all three and sets `primary_modality` + `why_primary`.

## API (platform)

```http
GET  /v1/vision/understand
GET  /v1/pixel/text
POST /v1/vision/understand   {"ocr":true,"semantic":true,"visual":true}
POST /v1/skills/run          {"skill":"understand"}
POST /v1/bridge/{id}/observe  # includes brief + action_hints
```

## Action hints

When primary is semantic → click by **name**.  
When pure visual → click **busy region centers** or scroll.  
Never force OCR when UI already named the control.

## Claim

Pixel translator is first-class host perception for POCKET workers and live bridges.
