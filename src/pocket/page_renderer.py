"""Full page renderer — pixels → symbols for agents (API-first).

Builds a complete *page model* the outer agent can read and act on:

  · micro UI objects (UIA deep: Name, AutomationId, ClassName, help)
  · OCR text lines with optional bounding boxes
  · pure visual micro-grid regions
  · unified symbol list (type, text, bbox, click target)
  · optional real-time stream of understanding frames

Everything is exposed on one API surface so Grok / Codex / Claude / UI share it.
"""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "vision"
ROOT.mkdir(parents=True, exist_ok=True)
PAGE_PATH = ROOT / "page_render.json"
STREAM_DIR = ROOT / "stream"
STREAM_DIR.mkdir(parents=True, exist_ok=True)

_stream_lock = threading.Lock()
_stream: Deque[Dict[str, Any]] = deque(maxlen=120)
_stream_thread: Optional[threading.Thread] = None
_stream_stop = threading.Event()
_stream_on = False
_stream_seq = 0

# Deep defaults: agents need micro detail, not a 50-element skim
DEFAULT_MAX_UI = 900
DEFAULT_STREAM_UI = 550
SYMBOL_PAYLOAD_CAP = 1400


def _deep_ui_map(*, max_elements: int = 800) -> Dict[str, Any]:
    """Higher-fidelity UI map: Name, AutomationId, ClassName, help, focus."""
    emit("vision", f"Deep UI map max={max_elements}", agent="OCULUS", role="python")
    import subprocess

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
    $aid = ''
    try {{ $aid = $e.Current.AutomationId }} catch {{}}
    $ht = ''
    try {{ $ht = $e.Current.HelpText }} catch {{}}
    $cls = ''
    try {{ $cls = $e.Current.ClassName }} catch {{}}
    if ((-not $n -or $n.Length -lt 1) -and (-not $aid) -and (-not $cls)) {{ continue }}
    if ($n -and $n.Length -gt 160) {{ $n = $n.Substring(0,160) }}
    $ct = $e.Current.ControlType.ProgrammaticName
    $rect = $e.Current.BoundingRectangle
    if ($rect.Width -lt 1 -or $rect.Height -lt 1) {{ continue }}
    if ($rect.X -lt -20000 -or $rect.Y -lt -20000) {{ continue }}
    $off = $false
    try {{ $off = $e.Current.IsOffscreen }} catch {{}}
    if ($off) {{ continue }}
    $en = $true
    try {{ $en = $e.Current.IsEnabled }} catch {{}}
    $kb = $false
    try {{ $kb = $e.Current.IsKeyboardFocusable }} catch {{}}
    $inv = $false
    try {{ $inv = $e.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern) -ne $null }} catch {{}}
    $i++
    $cx = [int]($rect.X + $rect.Width/2)
    $cy = [int]($rect.Y + $rect.Height/2)
    $nn = ($n -replace '[|`]', ' ')
    $aa = ($aid -replace '[|`]', ' ')
    $hh = ($ht -replace '[|`]', ' ')
    $cc = ($cls -replace '[|`]', ' ')
    if ($hh.Length -gt 60) {{ $hh = $hh.Substring(0,60) }}
    if ($cc.Length -gt 40) {{ $cc = $cc.Substring(0,40) }}
    $line = $nn + '|' + $ct + '|' + $cx + '|' + $cy + '|' + [int]$rect.Width + '|' + [int]$rect.Height + '|' + $en + '|' + $aa + '|' + $kb + '|' + $hh + '|' + $cc + '|' + $inv
    $out.Add($line)
  }} catch {{}}
}}
$out -join "`n"
"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "[Console]::OutputEncoding=[Text.UTF8Encoding]::UTF8; " + ps],
            capture_output=True,
            timeout=100,
        )
        raw = (r.stdout or b"").decode("utf-8", errors="replace")
        elements = []
        for line in raw.splitlines():
            parts = line.split("|")
            if len(parts) < 6:
                continue
            name = parts[0].strip()
            ctype = parts[1]
            x = int(float(parts[2]))
            y = int(float(parts[3]))
            ww = int(float(parts[4]))
            hh = int(float(parts[5]))
            aid = parts[7] if len(parts) > 7 else ""
            elements.append(
                {
                    "id": f"u{len(elements)}",
                    "name": name,
                    "type": ctype,
                    "x": x,
                    "y": y,
                    "w": ww,
                    "h": hh,
                    "enabled": (parts[6].lower() == "true") if len(parts) > 6 else True,
                    "automation_id": aid,
                    "focusable": (parts[8].lower() == "true") if len(parts) > 8 else False,
                    "help": parts[9] if len(parts) > 9 else "",
                    "class_name": parts[10] if len(parts) > 10 else "",
                    "invokable": (parts[11].lower() == "true") if len(parts) > 11 else False,
                    "kind": _classify_type(ctype, name),
                    "symbol": name or aid or (parts[10] if len(parts) > 10 else ""),
                    "click": {"x": x, "y": y},
                }
            )
        return {"ok": True, "count": len(elements), "elements": elements, "source": "uia_deep"}
    except Exception as e:
        return {"ok": False, "error": str(e), "count": 0, "elements": []}


def _classify_type(ctype: str, name: str) -> str:
    t = (ctype or "").lower()
    n = (name or "").lower()
    if "hyperlink" in t or "link" in t:
        return "link"
    if "button" in t:
        return "button"
    if "edit" in t or "document" in t:
        return "input"
    if "menu" in t:
        return "menu"
    if "tab" in t:
        return "tab"
    if "check" in t:
        return "checkbox"
    if "radio" in t:
        return "radio"
    if "combo" in t or "spinner" in t:
        return "select"
    if "listitem" in t or "dataitem" in t:
        return "list_item"
    if "list" in t or "tree" in t:
        return "list"
    if "text" in t or "label" in t:
        return "text"
    if "image" in t:
        return "image"
    if "pane" in t or "window" in t:
        return "pane"
    if "toolbar" in t or "tool bar" in t:
        return "toolbar"
    if "status" in t:
        return "status"
    if "http" in n or "www" in n:
        return "link"
    return "control"


def find_symbols(query: str, page: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Search symbol graph by text / automation_id (for agents + API)."""
    q = (query or "").lower().strip()
    if not q:
        return []
    if page is None:
        if not PAGE_PATH.exists():
            return []
        try:
            page = json.loads(PAGE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return []
    hits = []
    for s in page.get("symbols") or []:
        blob = " ".join(
            str(s.get(k) or "") for k in ("text", "type", "kind", "automation_id", "class_name")
        ).lower()
        if q in blob:
            hits.append(s)
    return hits[:40]


def render_full_page(
    *,
    max_ui: int = DEFAULT_MAX_UI,
    include_ocr: bool = True,
    include_visual: bool = True,
    include_image: bool = False,
    visual_grid: int = 5,
) -> Dict[str, Any]:
    """Full page model: every micro detail we can extract, fused as symbols."""
    from pocket.pixel_translator import (
        _capture_pil,
        pure_visual_analyze,
        ocr_pixels,
        _img_to_b64,
        _pick_optimal,
    )

    t0 = time.time()
    max_ui = max(50, min(int(max_ui or DEFAULT_MAX_UI), 1500))
    visual_grid = max(3, min(int(visual_grid or 5), 8))
    emit(
        "vision",
        f"Full page render micro→symbols max_ui={max_ui} grid={visual_grid}",
        agent="OCULUS",
        role="python",
    )

    img = _capture_pil(max_width=1920)
    w, h = img.size

    ui = _deep_ui_map(max_elements=max_ui)
    visual = pure_visual_analyze(img, grid=visual_grid) if include_visual else {}
    ocr = ocr_pixels(img) if include_ocr else {"ok": False, "lines": [], "count": 0}

    # Window titles
    titles: List[str] = []
    try:
        import subprocess

        r = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Process | Where-Object {$_.MainWindowTitle} | "
                "Select-Object -First 40 -ExpandProperty MainWindowTitle",
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

    # Build unified symbol graph (pixels → symbols agents can act on)
    symbols: List[Dict[str, Any]] = []
    # 1) UI micro symbols
    for el in ui.get("elements") or []:
        symbols.append(
            {
                "id": el.get("id"),
                "source": "uia",
                "kind": el.get("kind"),
                "text": el.get("name") or el.get("automation_id") or el.get("class_name") or "",
                "type": el.get("type"),
                "automation_id": el.get("automation_id") or "",
                "class_name": el.get("class_name") or "",
                "help": el.get("help") or "",
                "bbox": [
                    el.get("x") - el.get("w", 0) // 2,
                    el.get("y") - el.get("h", 0) // 2,
                    el.get("w"),
                    el.get("h"),
                ],
                "click": el.get("click"),
                "enabled": el.get("enabled"),
                "focusable": el.get("focusable"),
                "invokable": el.get("invokable"),
            }
        )
    # 2) OCR symbols (with bbox/click when engine provides them)
    for i, ln in enumerate(ocr.get("lines") or []):
        if isinstance(ln, dict):
            txt = ln.get("text") or ""
            bbox = ln.get("bbox")
            click = ln.get("click")
            if not click and bbox and len(bbox) >= 4:
                # bbox as x,y,w,h or x0,y0,x1,y1
                if bbox[2] > bbox[0] and bbox[3] > bbox[1] and bbox[2] > 50:
                    click = {"x": (bbox[0] + bbox[2]) // 2, "y": (bbox[1] + bbox[3]) // 2}
                else:
                    click = {"x": bbox[0] + bbox[2] // 2, "y": bbox[1] + bbox[3] // 2}
        else:
            txt = str(ln)
            bbox = None
            click = None
        if not txt:
            continue
        symbols.append(
            {
                "id": f"ocr{i}",
                "source": "ocr",
                "kind": "ocr_line",
                "text": txt,
                "type": "ocr",
                "bbox": bbox,
                "click": click,
            }
        )
    # 3) Visual region symbols (micro grid)
    for reg in visual.get("regions") or []:
        symbols.append(
            {
                "id": reg.get("id"),
                "source": "visual",
                "kind": "region",
                "text": f"region {reg.get('id')} edge={reg.get('edge_density')}",
                "type": "visual_region",
                "bbox": reg.get("bbox"),
                "click": {"x": reg["center"][0], "y": reg["center"][1]} if reg.get("center") else None,
                "busy": reg.get("busy"),
                "edge_density": reg.get("edge_density"),
            }
        )

    by_kind: Dict[str, int] = {}
    for s in symbols:
        k = s.get("kind") or "other"
        by_kind[k] = by_kind.get(k, 0) + 1

    links = [s for s in symbols if s.get("kind") == "link" and s.get("text")]
    buttons = [s for s in symbols if s.get("kind") == "button" and s.get("text")]
    inputs = [s for s in symbols if s.get("kind") == "input"]
    menus = [s for s in symbols if s.get("kind") == "menu"]
    ocr_text = ocr.get("plain_text") or "\n".join(
        (ln.get("text") if isinstance(ln, dict) else str(ln)) for ln in (ocr.get("lines") or [])
    )

    # Full agent-readable page dump (stream + poll both use this)
    uia_names = [
        (s.get("text") or "")[:80]
        for s in symbols
        if s.get("source") == "uia" and (s.get("text") or "").strip()
    ]
    page_text_parts = [
        f"# Page render @ {time.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Windows: {'; '.join(titles[:8]) or '(none)'}",
        (
            f"Symbols: {len(symbols)} "
            f"(uia={ui.get('count')}, ocr={ocr.get('count') or 0}, "
            f"visual_regions={len(visual.get('regions') or [])})"
        ),
        f"Kinds: {json.dumps(by_kind, sort_keys=True)}",
        f"Visual: {visual.get('summary') or ''}",
        "",
        "## Buttons",
        *[f"- {b.get('text')} @ {b.get('click')}" for b in buttons[:80]],
        "",
        "## Links",
        *[f"- {L.get('text')} @ {L.get('click')}" for L in links[:50]],
        "",
        "## Inputs",
        *[f"- {inp.get('text') or inp.get('type')} @ {inp.get('click')}" for inp in inputs[:30]],
        "",
        "## Menus / chrome",
        *[f"- {m.get('text')}" for m in menus[:30]],
        "",
        "## OCR body (full readable text)",
        ocr_text[:10000] if ocr_text else "(no OCR text)",
        "",
        "## All UI symbols (micro detail)",
        "\n".join(f"- [{i}] {n}" for i, n in enumerate(uia_names[:400])),
        "",
        "## Visual hotspots",
        *[
            f"- {r.get('id')} center={r.get('center')} edge={r.get('edge_density')} busy={r.get('busy')}"
            for r in (visual.get("busiest_regions") or [])[:8]
        ],
    ]
    page_text = "\n".join(page_text_parts)

    primary = _pick_optimal(visual or {}, {"count": ui.get("count") or 0}, ocr or {})

    out: Dict[str, Any] = {
        "ok": True,
        "product": "POCKET Page Renderer",
        "agent": "OCULUS",
        "at": time.time(),
        "ms": int((time.time() - t0) * 1000),
        "size": [w, h],
        "window_titles": titles,
        "page_hint": titles[0] if titles else "",
        "primary_modality": primary,
        "counts": {
            "symbols": len(symbols),
            "uia": ui.get("count") or 0,
            "ocr_lines": ocr.get("count") or 0,
            "visual_regions": len(visual.get("regions") or []),
            "by_kind": by_kind,
            "links": len(links),
            "buttons": len(buttons),
            "inputs": len(inputs),
        },
        "symbols": symbols[:SYMBOL_PAYLOAD_CAP],
        "links": [{"text": L.get("text"), "click": L.get("click"), "id": L.get("id")} for L in links[:60]],
        "buttons": [{"text": b.get("text"), "click": b.get("click"), "id": b.get("id")} for b in buttons[:100]],
        "inputs": [{"text": i.get("text"), "click": i.get("click"), "id": i.get("id")} for i in inputs[:40]],
        "ocr_plain": (ocr_text or "")[:12000],
        "visual": {
            k: visual.get(k)
            for k in (
                "summary",
                "brightness",
                "contrast",
                "mood",
                "structure",
                "busiest_regions",
                "palette",
                "grid",
            )
            if k in visual
        },
        "page_text": page_text[:40000],
        "brief": (
            f"Full page: {len(symbols)} symbols · primary={primary} · "
            f"uia={ui.get('count')} ocr={ocr.get('count') or 0} visual={len(visual.get('regions') or [])} · "
            f"{titles[0] if titles else 'desktop'}"
        ),
        "action_hints": _hints(links, buttons, visual, inputs),
        "how_to_use": {
            "read": "Use page_text + symbols for full understanding",
            "act": "POST /v1/vision/click with name, or click_xy from symbol.click",
            "stream": "POST /v1/vision/stream/start then poll GET /v1/vision/stream?after=N",
            "clients": "Grok, Codex, Claude, any HTTP client — same /v1/api surface",
        },
        "api": {
            "catalog": "GET /v1/api",
            "render": "GET|POST /v1/vision/page",
            "stream": "GET /v1/vision/stream?after=0",
            "stream_start": "POST /v1/vision/stream/start",
            "stream_stop": "POST /v1/vision/stream/stop",
            "click": "POST /v1/vision/click",
            "understand": "GET /v1/vision/understand",
            "pixel_text": "GET /v1/pixel/text",
            "find": "POST /v1/vision/find",
        },
    }

    if include_image:
        b64, mime, _ = _img_to_b64(img, quality=50)
        out["image_b64"] = b64
        out["mime"] = mime

    slim = {k: v for k, v in out.items() if k != "image_b64"}
    slim["symbols"] = (slim.get("symbols") or [])[:600]
    PAGE_PATH.write_text(json.dumps(slim, indent=2, default=str)[:600000], encoding="utf-8")
    (STREAM_DIR / "latest_page_text.md").write_text(page_text, encoding="utf-8")

    emit(
        "vision",
        f"page render symbols={len(symbols)} primary={primary}",
        agent="OCULUS",
        role="python",
    )
    return out


def _hints(links, buttons, visual, inputs=None) -> List[Dict[str, Any]]:
    hints: List[Dict[str, Any]] = []
    for L in links[:12]:
        hints.append({"action": "click_name", "name": L.get("text"), "reason": "link symbol"})
    for b in buttons[:12]:
        hints.append({"action": "click_name", "name": b.get("text"), "reason": "button symbol"})
    for inp in (inputs or [])[:5]:
        if inp.get("text"):
            hints.append({"action": "click_name", "name": inp.get("text"), "reason": "input field"})
    for reg in (visual.get("busiest_regions") or [])[:4]:
        if reg.get("center"):
            hints.append(
                {
                    "action": "click_xy",
                    "x": reg["center"][0],
                    "y": reg["center"][1],
                    "reason": f"visual hotspot {reg.get('id')}",
                }
            )
    hints.append({"action": "scroll_down", "reason": "read more of page"})
    return hints[:30]


# ---------------------------------------------------------------------------
# Real-time stream — continuous full-page understanding for agents
# ---------------------------------------------------------------------------

def stream_start(*, interval_sec: float = 1.5, max_ui: int = DEFAULT_STREAM_UI) -> Dict[str, Any]:
    """Background loop: full page render snapshots for agents to poll."""
    global _stream_on, _stream_thread
    with _stream_lock:
        if _stream_on and _stream_thread and _stream_thread.is_alive():
            return {"ok": True, "already": True, "seq": _stream_seq, "streaming": True}
        _stream_stop.clear()
        _stream_on = True
        _stream_thread = threading.Thread(
            target=_stream_loop,
            args=(max(0.8, float(interval_sec)), max(100, int(max_ui or DEFAULT_STREAM_UI))),
            daemon=True,
            name="pocket-page-stream",
        )
        _stream_thread.start()
    emit("vision", "Page understanding stream ON", agent="OCULUS", role="python")
    return {"ok": True, "streaming": True, "interval_sec": interval_sec, "max_ui": max_ui}


def stream_stop() -> Dict[str, Any]:
    global _stream_on
    _stream_stop.set()
    _stream_on = False
    return {"ok": True, "streaming": False}


def _stream_loop(interval: float, max_ui: int = DEFAULT_STREAM_UI) -> None:
    global _stream_seq
    while not _stream_stop.is_set():
        try:
            page = render_full_page(
                max_ui=max_ui,
                include_ocr=True,
                include_visual=True,
                include_image=False,
                visual_grid=4,
            )
            with _stream_lock:
                _stream_seq += 1
                seq = _stream_seq
                frame = {
                    "seq": seq,
                    "at": time.time(),
                    "brief": page.get("brief"),
                    "page_hint": page.get("page_hint"),
                    "primary_modality": page.get("primary_modality"),
                    "counts": page.get("counts"),
                    "links": page.get("links"),
                    "buttons": (page.get("buttons") or [])[:40],
                    "inputs": (page.get("inputs") or [])[:20],
                    "symbols_head": (page.get("symbols") or [])[:80],
                    "ocr_plain": (page.get("ocr_plain") or "")[:3000],
                    "action_hints": page.get("action_hints"),
                    "page_text_head": (page.get("page_text") or "")[:4000],
                    "how_to_use": page.get("how_to_use"),
                }
                _stream.append(frame)
                (STREAM_DIR / "latest.json").write_text(
                    json.dumps(frame, indent=2, default=str)[:150000], encoding="utf-8"
                )
        except Exception as e:
            with _stream_lock:
                _stream_seq += 1
                _stream.append({"seq": _stream_seq, "error": str(e), "at": time.time()})
        _stream_stop.wait(interval)


def stream_latest(*, after_seq: int = 0, limit: int = 20) -> Dict[str, Any]:
    with _stream_lock:
        items = [f for f in _stream if int(f.get("seq") or 0) > int(after_seq or 0)]
        return {
            "ok": True,
            "streaming": _stream_on,
            "seq": _stream_seq,
            "frames": items[-limit:],
            "latest": _stream[-1] if _stream else None,
        }


def stream_status() -> Dict[str, Any]:
    with _stream_lock:
        return {
            "ok": True,
            "streaming": _stream_on,
            "seq": _stream_seq,
            "buffer": len(_stream),
            "latest_path": str(STREAM_DIR / "latest.json"),
            "page_path": str(PAGE_PATH),
            "page_text_path": str(STREAM_DIR / "latest_page_text.md"),
        }
