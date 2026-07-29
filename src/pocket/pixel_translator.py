"""Pixel translator — screen understanding: text when useful, pure visual when better.

Modalities:
  1) SEMANTIC TEXT  — UI Automation names (often better than OCR for apps)
  2) OCR TEXT       — Windows.Media.Ocr (when available) / optional tesseract
  3) PURE VISUAL    — layout regions, saliency, color structure (no text needed)

`understand()` picks/fuses modalities and returns an agent-ready brief.
"""

from __future__ import annotations

import base64
import io
import json
import math
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit

VISION = Path.home() / ".pocket" / "vision"
VISION.mkdir(parents=True, exist_ok=True)
LAST = VISION / "pixel_understand.json"


# ---------------------------------------------------------------------------
# Capture
# ---------------------------------------------------------------------------

def _capture_pil(*, max_width: int = 1280):
    from PIL import ImageGrab

    img = ImageGrab.grab(all_screens=False)
    if img.width > max_width:
        ratio = max_width / float(img.width)
        img = img.resize((max_width, int(img.height * ratio)))
    return img.convert("RGB")


def _img_to_b64(img, *, fmt: str = "JPEG", quality: int = 70) -> Tuple[str, str, bytes]:
    buf = io.BytesIO()
    if fmt.upper() == "PNG":
        img.save(buf, format="PNG", optimize=True)
        raw = buf.getvalue()
        return base64.b64encode(raw).decode("ascii"), "image/png", raw
    img.save(buf, format="JPEG", quality=quality)
    raw = buf.getvalue()
    return base64.b64encode(raw).decode("ascii"), "image/jpeg", raw


# ---------------------------------------------------------------------------
# Pure visual understanding (always available, no OCR)
# ---------------------------------------------------------------------------

def pure_visual_analyze(img, *, grid: int = 3) -> Dict[str, Any]:
    """Structure the screen without reading text — layout, saliency, color.

    grid: NxN micro regions (3 default; page renderer uses 5 for micro detail).
    """
    from PIL import Image, ImageFilter, ImageStat, ImageOps

    w, h = img.size
    # downsample for speed
    small = img.resize((min(200, w), max(1, int(min(200, w) * h / w))))
    sw, sh = small.size

    # color stats
    stat = ImageStat.Stat(small)
    mean_rgb = [round(x, 1) for x in stat.mean]
    # brightness
    gray = ImageOps.grayscale(small)
    gstat = ImageStat.Stat(gray)
    brightness = round(gstat.mean[0], 1)
    contrast = round(gstat.stddev[0], 1)

    # edge density → activity map (NxN micro regions)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    ed = edges.load()
    regions = []
    rows = cols = max(2, min(int(grid or 3), 8))
    for ry in range(rows):
        for cx in range(cols):
            x0, y0 = int(cx * sw / cols), int(ry * sh / rows)
            x1, y1 = int((cx + 1) * sw / cols), int((ry + 1) * sh / rows)
            acc, n = 0, 0
            for y in range(y0, max(y0 + 1, y1)):
                for x in range(x0, max(x0 + 1, x1)):
                    acc += ed[x, y]
                    n += 1
            density = acc / max(1, n)
            # map back to full image coords
            fx0, fy0 = int(cx * w / cols), int(ry * h / rows)
            fx1, fy1 = int((cx + 1) * w / cols), int((ry + 1) * h / rows)
            regions.append(
                {
                    "id": f"r{ry}{cx}",
                    "row": ry,
                    "col": cx,
                    "edge_density": round(density, 2),
                    "bbox": [fx0, fy0, fx1, fy1],
                    "center": [(fx0 + fx1) // 2, (fy0 + fy1) // 2],
                    "busy": density > 12,
                }
            )
    # dominant palette (simple quantize)
    q = small.quantize(colors=6, method=Image.Quantize.MEDIANCUT)
    palette = q.getpalette() or []
    counts = q.getcolors() or []
    colors = []
    for count, idx in sorted(counts, reverse=True)[:5]:
        if palette and idx * 3 + 2 < len(palette):
            colors.append(
                {
                    "rgb": [palette[idx * 3], palette[idx * 3 + 1], palette[idx * 3 + 2]],
                    "share": round(count / (sw * sh), 3),
                }
            )

    busiest = sorted(regions, key=lambda r: r["edge_density"], reverse=True)[: max(3, rows)]
    calm = sorted(regions, key=lambda r: r["edge_density"])[:2]

    # visual mode guess
    if brightness < 40:
        mood = "dark_ui"
    elif brightness > 200:
        mood = "bright_page"
    else:
        mood = "mixed"

    if contrast > 55:
        structure = "high_contrast_structured"
    elif contrast < 25:
        structure = "flat_low_detail"
    else:
        structure = "normal"

    summary = (
        f"Visual: {w}x{h}, grid={rows}x{cols}, brightness={brightness}, contrast={contrast}, mood={mood}, "
        f"structure={structure}. Busiest regions: "
        + ", ".join(f"{b['id']}@{b['center']}" for b in busiest[:5])
    )

    return {
        "ok": True,
        "modality": "pure_visual",
        "size": [w, h],
        "grid": [rows, cols],
        "brightness": brightness,
        "contrast": contrast,
        "mean_rgb": mean_rgb,
        "mood": mood,
        "structure": structure,
        "palette": colors,
        "regions": regions,
        "busiest_regions": busiest,
        "calm_regions": calm,
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# Semantic text from UI Automation (often better than OCR for apps)
# ---------------------------------------------------------------------------

def semantic_ui_text(*, max_elements: int = 200) -> Dict[str, Any]:
    """Text the OS already knows — accessibility names. Optimal for buttons/links."""
    from pocket.vision_core import build_ui_map

    ui = build_ui_map(max_elements=max_elements)
    elements = ui.get("elements") or []
    lines = []
    links = []
    buttons = []
    for el in elements:
        name = (el.get("name") or "").strip()
        if not name:
            continue
        t = (el.get("type") or "").lower()
        lines.append({"text": name, "type": t, "x": el.get("x"), "y": el.get("y"), "source": "uia"})
        if "hyperlink" in t or "link" in t:
            links.append(name)
        if "button" in t or "menuitem" in t:
            buttons.append(name)
    plain = " | ".join(x["text"] for x in lines[:80])
    return {
        "ok": True,
        "modality": "semantic_ui_text",
        "count": len(lines),
        "lines": lines[:120],
        "links": links[:40],
        "buttons": buttons[:40],
        "plain_text": plain[:4000],
        "summary": f"Semantic UI text: {len(lines)} named elements, {len(links)} link-like, {len(buttons)} buttons",
    }


# ---------------------------------------------------------------------------
# OCR — Windows.Media.Ocr when available
# ---------------------------------------------------------------------------

def _windows_ocr_from_file(path: Path) -> Dict[str, Any]:
    """Use WinRT OCR via PowerShell on a saved image file."""
    p = str(path).replace("'", "''")
    ps = rf"""
$ErrorActionPreference = 'Stop'
try {{
  Add-Type -AssemblyName System.Runtime.WindowsRuntime | Out-Null
  $null = [Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime]
  $null = [Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics,ContentType=WindowsRuntime]
  $null = [Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime]

  function Await($WinRtTask, $ResultType) {{
    $asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{
      $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and
      $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    }})[0]
    $asTaskGeneric = $asTask.MakeGenericMethod($ResultType)
    $netTask = $asTaskGeneric.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
  }}

  $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync('{p}')) ([Windows.Storage.StorageFile])
  $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
  $decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
  $bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
  $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
  if (-not $engine) {{ $engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage([Windows.Globalization.Language]::new('en-US')) }}
  if (-not $engine) {{ 'NO_ENGINE'; exit 2 }}
  $result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
  $lines = New-Object System.Collections.Generic.List[string]
  foreach ($line in $result.Lines) {{
    $t = $line.Text -replace '[|`]', ' '
    $x = 0; $y = 0; $w = 0; $h = 0
    try {{
      $br = $line.Words[0].BoundingRect
      $x2 = $br.X; $y2 = $br.Y; $x3 = $br.X; $y3 = $br.Y
      foreach ($wd in $line.Words) {{
        $r = $wd.BoundingRect
        if ($r.X -lt $x2) {{ $x2 = $r.X }}
        if ($r.Y -lt $y2) {{ $y2 = $r.Y }}
        if (($r.X + $r.Width) -gt $x3) {{ $x3 = $r.X + $r.Width }}
        if (($r.Y + $r.Height) -gt $y3) {{ $y3 = $r.Y + $r.Height }}
      }}
      $x = [int]$x2; $y = [int]$y2; $w = [int]($x3 - $x2); $h = [int]($y3 - $y2)
    }} catch {{}}
    $lines.Add(($t + '|' + $x + '|' + $y + '|' + $w + '|' + $h))
  }}
  $lines -join "`n"
}} catch {{
  'OCR_ERR:' + $_.Exception.Message
}}
"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            timeout=45,
        )
        out = (r.stdout or b"").decode("utf-8", errors="replace").strip()
        if out.startswith("OCR_ERR") or out == "NO_ENGINE" or not out:
            return {"ok": False, "error": out or "empty ocr", "lines": [], "modality": "ocr_windows"}
        lines = []
        for ln in out.splitlines():
            if not ln.strip():
                continue
            parts = ln.split("|")
            text = parts[0].strip()
            if not text:
                continue
            entry: Dict[str, Any] = {"text": text, "source": "windows_ocr"}
            if len(parts) >= 5:
                try:
                    x, y, ww, hh = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                    if ww > 0 and hh > 0:
                        entry["bbox"] = [x, y, ww, hh]
                        entry["click"] = {"x": x + ww // 2, "y": y + hh // 2}
                except Exception:
                    pass
            lines.append(entry)
        plain = "\n".join(x["text"] for x in lines)
        return {
            "ok": True,
            "modality": "ocr_windows",
            "lines": lines,
            "plain_text": plain[:12000],
            "count": len(lines),
            "summary": f"Windows OCR: {len(lines)} lines (with bboxes)",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "lines": [], "modality": "ocr_windows"}


def ocr_pixels(img) -> Dict[str, Any]:
    """Pixel→text via best available engine."""
    # try tesseract if present
    try:
        import pytesseract  # type: ignore

        text = pytesseract.image_to_string(img) or ""
        lines = [{"text": ln.strip(), "source": "tesseract"} for ln in text.splitlines() if ln.strip()]
        if lines:
            return {
                "ok": True,
                "modality": "ocr_tesseract",
                "lines": lines,
                "plain_text": text[:8000],
                "count": len(lines),
                "summary": f"Tesseract OCR: {len(lines)} lines",
            }
    except Exception:
        pass

    # Windows OCR
    tmp = VISION / f"ocr_frame_{int(time.time())}.png"
    try:
        img.save(tmp, format="PNG")
        res = _windows_ocr_from_file(tmp)
        return res
    finally:
        try:
            tmp.unlink(missing_ok=True)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Fusion / understand
# ---------------------------------------------------------------------------

def _pick_optimal(visual: Dict, semantic: Dict, ocr: Dict) -> str:
    """Choose primary modality for agent brief."""
    sem_n = int(semantic.get("count") or 0)
    ocr_n = int(ocr.get("count") or 0) if ocr.get("ok") else 0
    # Apps with rich accessibility → semantic wins
    if sem_n >= 15:
        return "semantic_ui_text"
    # Document-like bright page + OCR worked → OCR
    if ocr_n >= 8 and visual.get("mood") == "bright_page":
        return "ocr"
    # Sparse UI text, busy visual → pure visual
    if sem_n < 8 and ocr_n < 5:
        return "pure_visual"
    if ocr_n > sem_n:
        return "ocr"
    if sem_n > 0:
        return "semantic_ui_text"
    return "pure_visual"


def understand(
    *,
    max_width: int = 1280,
    want_ocr: bool = True,
    want_semantic: bool = True,
    want_visual: bool = True,
    include_image: bool = False,
) -> Dict[str, Any]:
    """Full pixel translator: fuse visual + semantic + OCR; pick optimal primary."""
    emit("vision", "pixel_translator.understand()", agent="OCULUS", role="python")
    t0 = time.time()
    img = _capture_pil(max_width=max_width)
    w, h = img.size

    visual = pure_visual_analyze(img) if want_visual else {"ok": False}
    semantic = semantic_ui_text() if want_semantic else {"ok": False, "count": 0, "lines": []}
    ocr = ocr_pixels(img) if want_ocr else {"ok": False, "count": 0, "lines": []}

    primary = _pick_optimal(visual if visual.get("ok") else {}, semantic, ocr)

    # Build agent-facing brief
    brief_parts = []
    if primary == "pure_visual":
        brief_parts.append(visual.get("summary") or "Visual only")
        brief_parts.append(
            "Text sparse — navigate by region centers / UI map, not OCR."
        )
    elif primary == "semantic_ui_text":
        brief_parts.append(semantic.get("summary") or "")
        if semantic.get("links"):
            brief_parts.append("Links: " + ", ".join(semantic["links"][:12]))
        if semantic.get("buttons"):
            brief_parts.append("Buttons: " + ", ".join(semantic["buttons"][:12]))
        brief_parts.append("Optimal: click by accessibility name (not OCR).")
    else:
        brief_parts.append(ocr.get("summary") or "OCR")
        if ocr.get("plain_text"):
            brief_parts.append("Text seen:\n" + (ocr.get("plain_text") or "")[:1200])

    # always attach visual busiest for click targets when text fails
    if visual.get("busiest_regions"):
        brief_parts.append(
            "Busy visual hotspots: "
            + ", ".join(f"{b['id']} center={b['center']}" for b in visual["busiest_regions"][:3])
        )

    # window titles
    titles = []
    try:
        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process | Where-Object {$_.MainWindowTitle} | "
                "Select-Object -First 20 -ExpandProperty MainWindowTitle",
            ],
            capture_output=True,
            timeout=12,
        )
        titles = [
            t.strip()
            for t in (r.stdout or b"").decode("utf-8", errors="replace").splitlines()
            if t.strip()
        ]
    except Exception:
        pass

    out: Dict[str, Any] = {
        "ok": True,
        "product": "POCKET Pixel Translator",
        "agent": "OCULUS",
        "at": time.time(),
        "ms": int((time.time() - t0) * 1000),
        "size": [w, h],
        "primary_modality": primary,
        "why_primary": _why(primary, semantic, ocr, visual),
        "brief": "\n".join(brief_parts),
        "window_titles": titles,
        "page_hint": titles[0] if titles else "",
        "modalities": {
            "pure_visual": {k: visual.get(k) for k in (
                "ok", "summary", "brightness", "contrast", "mood", "structure",
                "busiest_regions", "palette",
            ) if k in visual},
            "semantic_ui_text": {
                "ok": semantic.get("ok"),
                "count": semantic.get("count"),
                "links": semantic.get("links"),
                "buttons": semantic.get("buttons"),
                "plain_text": (semantic.get("plain_text") or "")[:2000],
                "summary": semantic.get("summary"),
            },
            "ocr": {
                "ok": ocr.get("ok"),
                "count": ocr.get("count") or 0,
                "plain_text": (ocr.get("plain_text") or "")[:2000] if ocr.get("ok") else "",
                "summary": ocr.get("summary") or ocr.get("error"),
                "modality": ocr.get("modality"),
            },
        },
        "action_hints": _action_hints(primary, semantic, visual),
    }

    if include_image:
        b64, mime, _ = _img_to_b64(img, quality=55)
        out["image_b64"] = b64
        out["mime"] = mime

    try:
        slim = {k: v for k, v in out.items() if k != "image_b64"}
        LAST.write_text(json.dumps(slim, indent=2, default=str)[:120000], encoding="utf-8")
    except Exception:
        pass

    emit(
        "vision",
        f"understand primary={primary} sem={semantic.get('count')} ocr={ocr.get('count')}",
        agent="OCULUS",
        role="python",
    )
    return out


def _why(primary: str, semantic: Dict, ocr: Dict, visual: Dict) -> str:
    if primary == "semantic_ui_text":
        return f"UI Automation exposed {semantic.get('count')} named controls — better than OCR for app chrome."
    if primary == "ocr":
        return f"OCR produced {ocr.get('count')} lines on a readable surface."
    return (
        f"Text sparse (ui={semantic.get('count')}, ocr={ocr.get('count')}); "
        f"use pure visual structure ({visual.get('structure')})."
    )


def _action_hints(primary: str, semantic: Dict, visual: Dict) -> List[Dict[str, Any]]:
    hints = []
    for name in (semantic.get("links") or [])[:8]:
        hints.append({"action": "click_name", "name": name, "reason": "link from semantic UI"})
    for name in (semantic.get("buttons") or [])[:6]:
        hints.append({"action": "click_name", "name": name, "reason": "button from semantic UI"})
    if primary == "pure_visual":
        for b in (visual.get("busiest_regions") or [])[:3]:
            hints.append(
                {
                    "action": "click_xy",
                    "x": b["center"][0],
                    "y": b["center"][1],
                    "reason": f"busy visual region {b['id']}",
                }
            )
        hints.append({"action": "scroll_down", "reason": "explore more of visual layout"})
    return hints[:20]


def translate_to_text_only() -> Dict[str, Any]:
    """Force pixel→text (semantic + OCR), still report if visual is better."""
    u = understand(want_visual=True, want_ocr=True, want_semantic=True)
    text_bits = []
    sem = u["modalities"]["semantic_ui_text"]
    ocr = u["modalities"]["ocr"]
    if sem.get("plain_text"):
        text_bits.append("=== UI TEXT ===\n" + sem["plain_text"])
    if ocr.get("plain_text"):
        text_bits.append("=== OCR TEXT ===\n" + ocr["plain_text"])
    if not text_bits:
        text_bits.append(
            "(No reliable text — pure visual recommended)\n"
            + (u["modalities"]["pure_visual"].get("summary") or "")
        )
    return {
        "ok": True,
        "primary_modality": u["primary_modality"],
        "text": "\n\n".join(text_bits),
        "brief": u["brief"],
        "why_primary": u["why_primary"],
        "action_hints": u["action_hints"],
        "page_hint": u.get("page_hint"),
    }
