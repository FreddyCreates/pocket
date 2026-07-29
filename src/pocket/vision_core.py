"""First-class vision: frames + UI map + optional OCR.

This is not a screenshot toy — it is the host sensory layer every worker uses.
"""

from __future__ import annotations

import base64
import io
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit
from pocket.live_vision import ensure_vision, latest_frame, LIVE

VISION_ROOT = Path.home() / ".pocket" / "vision"
VISION_ROOT.mkdir(parents=True, exist_ok=True)
UI_MAP_PATH = VISION_ROOT / "ui_map.json"
LAST_OBS = VISION_ROOT / "last_observation.json"


def grab_frame(*, max_width: int = 1280) -> Dict[str, Any]:
    """Capture current screen as structured observation input."""
    ensure_vision(interval=0.8)
    from pocket.capture import capture_screen

    shot = capture_screen(max_width=max_width)
    live = latest_frame(include_image=True)
    return {
        "ok": bool(shot.get("ok") or live.get("base64")),
        "screenshot": shot,
        "live": {k: live.get(k) for k in ("seq", "path", "mime") if k in live},
        "base64": shot.get("base64") or live.get("base64"),
        "mime": shot.get("mime") or live.get("mime") or "image/jpeg",
        "at": time.time(),
    }


def build_ui_map(*, max_elements: int = 250) -> Dict[str, Any]:
    """Enumerate named interactive UI elements via UI Automation (true interface map)."""
    emit("vision", "Building UI map…", agent="OCULUS", role="python")
    ps = rf"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root = [System.Windows.Automation.AutomationElement]::RootElement
$all = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
$out = New-Object System.Collections.Generic.List[string]
$i = 0
foreach ($e in $all) {{
  if ($i -ge {int(max_elements)}) {{ break }}
  try {{
    $n = $e.Current.Name
    if (-not $n -or $n.Length -lt 2 -or $n.Length -gt 80) {{ continue }}
    $ct = $e.Current.ControlType.ProgrammaticName
    $rect = $e.Current.BoundingRectangle
    if ($rect.Width -lt 4 -or $rect.Height -lt 4) {{ continue }}
    if ($rect.X -lt -10000) {{ continue }}
    $en = $e.Current.IsEnabled
    $off = $e.Current.IsOffscreen
    if ($off) {{ continue }}
    $i++
    $cx = [int]($rect.X + $rect.Width/2)
    $cy = [int]($rect.Y + $rect.Height/2)
    $line = ($n -replace '[|`]', ' ') + '|' + $ct + '|' + $cx + '|' + $cy + '|' + [int]$rect.Width + '|' + [int]$rect.Height + '|' + $en
    $out.Add($line)
  }} catch {{}}
}}
$out -join "`n"
"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", "[Console]::OutputEncoding=[Text.UTF8Encoding]::UTF8; " + ps],
            capture_output=True,
            timeout=55,
        )
        raw_out = (r.stdout or b"").decode("utf-8", errors="replace")
        if not raw_out.strip():
            raw_out = (r.stderr or b"").decode("utf-8", errors="replace")
        elements: List[Dict[str, Any]] = []
        for line in raw_out.splitlines():
            parts = line.split("|")
            if len(parts) < 6:
                continue
            elements.append(
                {
                    "name": parts[0].strip(),
                    "type": parts[1],
                    "x": int(parts[2]),
                    "y": int(parts[3]),
                    "w": int(parts[4]),
                    "h": int(parts[5]),
                    "enabled": parts[6].lower() == "true" if len(parts) > 6 else True,
                }
            )
        payload = {
            "ok": True,
            "count": len(elements),
            "elements": elements,
            "at": time.time(),
            "source": "ui_automation",
        }
        UI_MAP_PATH.write_text(json.dumps(payload, indent=2)[:500000], encoding="utf-8")
        emit("vision", f"UI map: {len(elements)} elements", agent="OCULUS", role="python")
        return payload
    except Exception as e:
        return {"ok": False, "error": str(e), "elements": []}


def find_in_map(query: str, ui_map: Optional[Dict] = None) -> List[Dict[str, Any]]:
    q = (query or "").lower().strip()
    m = ui_map or (json.loads(UI_MAP_PATH.read_text(encoding="utf-8")) if UI_MAP_PATH.exists() else {})
    hits = []
    for el in m.get("elements") or []:
        name = (el.get("name") or "").lower()
        if q in name or name in q:
            hits.append(el)
    return hits[:20]


def click_xy(x: int, y: int) -> Dict[str, Any]:
    ps = rf"""
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point({int(x)},{int(y)})
Add-Type @"
using System; using System.Runtime.InteropServices;
public class MC {{
  [DllImport("user32.dll")] public static extern void mouse_event(int f,int a,int b,int c,int d);
}}
"@
[MC]::mouse_event(0x02,0,0,0,0); Start-Sleep -Milliseconds 40; [MC]::mouse_event(0x04,0,0,0,0)
'clicked:{int(x)},{int(y)}'
"""
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True, timeout=10)
        emit("vision", f"Click ({x},{y})", agent="OCULUS", role="python")
        return {"ok": True, "x": x, "y": y, "out": (r.stdout or "").strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def click_by_name(name: str, *, rebuild: bool = True) -> Dict[str, Any]:
    """Vision→action: map UI, find name, click center. First-class path."""
    ui = build_ui_map() if rebuild else (
        json.loads(UI_MAP_PATH.read_text(encoding="utf-8")) if UI_MAP_PATH.exists() else build_ui_map()
    )
    hits = find_in_map(name, ui)
    if not hits:
        # fallback existing click_named_element
        from pocket.ui_click import click_named_element

        r = click_named_element(name)
        return {"ok": r.get("ok"), "method": "uia_invoke_fallback", "query": name, **r}
    el = hits[0]
    r = click_xy(int(el["x"]), int(el["y"]))
    return {
        "ok": r.get("ok"),
        "method": "vision_map_click",
        "query": name,
        "matched": el.get("name"),
        "candidates": len(hits),
        **r,
    }


def windows_ocr_lines() -> Dict[str, Any]:
    """OCR via pixel_translator (Windows OCR / tesseract when available)."""
    try:
        from pocket.pixel_translator import ocr_pixels, _capture_pil

        return ocr_pixels(_capture_pil(max_width=1100))
    except Exception as e:
        return {"ok": False, "error": str(e), "lines": []}


def observe(
    *,
    with_ui_map: bool = True,
    with_ocr: bool = False,
    with_understand: bool = True,
) -> Dict[str, Any]:
    """Full first-class observation — pixel_translator.understand is default."""
    emit("vision", "observe()", agent="OCULUS", role="python")
    if with_understand:
        try:
            from pocket.pixel_translator import understand

            u = understand(
                want_ocr=bool(with_ocr or True),
                want_semantic=with_ui_map,
                want_visual=True,
                include_image=False,
            )
            sem = (u.get("modalities") or {}).get("semantic_ui_text") or {}
            ocr = (u.get("modalities") or {}).get("ocr") or {}
            vis = (u.get("modalities") or {}).get("pure_visual") or {}
            obs = {
                "ok": True,
                "at": time.time(),
                "source": "pixel_translator",
                "primary_modality": u.get("primary_modality"),
                "why_primary": u.get("why_primary"),
                "brief": u.get("brief"),
                "page_hint": u.get("page_hint"),
                "window_titles": u.get("window_titles") or [],
                "ui_map_count": sem.get("count") or 0,
                "ui_names": [
                    x.get("text")
                    for x in (sem.get("lines") or [])[:50]
                    if isinstance(x, dict)
                ],
                "links_on_page": sem.get("links") or [],
                "buttons": sem.get("buttons") or [],
                "ocr_plain": (ocr.get("plain_text") or "")[:2000],
                "ocr_lines": ocr.get("lines") or [],
                "visual": vis,
                "action_hints": u.get("action_hints") or [],
                "has_image": False,
            }
            LAST_OBS.write_text(json.dumps(obs, indent=2, default=str)[:100000], encoding="utf-8")
            return obs
        except Exception as e:
            emit("vision", f"understand fallback: {e}", agent="OCULUS", role="python", level="error")

    frame = grab_frame()
    ui = build_ui_map() if with_ui_map else {"ok": False, "elements": []}
    ocr = windows_ocr_lines() if with_ocr else {"ok": False, "lines": [], "skipped": True}
    titles = []
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process | Where-Object {$_.MainWindowTitle} | Select-Object -First 25 -ExpandProperty MainWindowTitle"],
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
    obs = {
        "ok": True,
        "at": time.time(),
        "source": "legacy_observe",
        "frame": {k: frame.get(k) for k in ("ok", "mime", "live") if k in frame},
        "has_image": bool(frame.get("base64")),
        "ui_map_count": ui.get("count") or len(ui.get("elements") or []),
        "ui_names": [e.get("name") for e in (ui.get("elements") or [])[:40]],
        "window_titles": titles,
        "ocr_lines": ocr.get("lines") or [],
        "clickable_sample": (ui.get("elements") or [])[:15],
    }
    LAST_OBS.write_text(json.dumps(obs, indent=2, default=str)[:100000], encoding="utf-8")
    if frame.get("screenshot", {}).get("base64"):
        obs["image_b64_len"] = len(frame["screenshot"]["base64"])
    obs["_frame_b64"] = frame.get("base64")
    return obs
