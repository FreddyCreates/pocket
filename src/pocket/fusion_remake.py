"""Fusion remake — symbol graph → IR → HTML rebuild + 3D-ready scene.

Uses OCULUS page symbols (UIA + OCR + visual) to reconstruct structure agents
can remake, animate, and feed into Imagine Studio / viral device scenes.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "imagine"
REMAKES = ROOT / "remakes"
SCENES = ROOT / "scenes"
for d in (ROOT, REMAKES, SCENES):
    d.mkdir(parents=True, exist_ok=True)


def _kind_css(kind: str) -> str:
    k = (kind or "control").lower()
    if k == "button":
        return "btn"
    if k == "link":
        return "link"
    if k == "input":
        return "input"
    if k == "text":
        return "txt"
    if k == "tab":
        return "tab"
    if k in ("list", "list_item"):
        return "list"
    if k == "menu":
        return "menu"
    if k == "image":
        return "img"
    if k == "ocr_line":
        return "ocr"
    if k == "region":
        return "region"
    return "ctrl"


def symbols_to_ir(
    page: Optional[Dict[str, Any]] = None,
    *,
    max_nodes: int = 400,
) -> Dict[str, Any]:
    """Build ScreenIR from a page render payload (or last page_render.json)."""
    if page is None:
        from pocket.page_renderer import PAGE_PATH

        if PAGE_PATH.exists():
            page = json.loads(PAGE_PATH.read_text(encoding="utf-8"))
        else:
            from pocket.page_renderer import render_full_page

            page = render_full_page(max_ui=500, visual_grid=4)

    size = page.get("size") or [1920, 1080]
    nodes: List[Dict[str, Any]] = []
    for s in (page.get("symbols") or [])[:max_nodes]:
        if s.get("source") == "visual" and not s.get("busy"):
            # keep only busy visual regions to reduce noise
            if not s.get("busy"):
                continue
        text = (s.get("text") or "").strip()
        bbox = s.get("bbox")
        if not text and not bbox:
            continue
        nodes.append(
            {
                "id": s.get("id"),
                "kind": s.get("kind") or "control",
                "source": s.get("source"),
                "text": text[:200],
                "bbox": bbox,
                "click": s.get("click"),
                "enabled": s.get("enabled", True),
                "invokable": s.get("invokable"),
                "automation_id": s.get("automation_id") or "",
                "class_name": s.get("class_name") or "",
                "css": _kind_css(s.get("kind") or ""),
            }
        )

    # reading order: top-to-bottom, left-to-right when bbox exists
    def _key(n: Dict[str, Any]):
        b = n.get("bbox")
        if isinstance(b, list) and len(b) >= 2:
            return (int(b[1]), int(b[0]))
        return (10_000, 10_000)

    reading = sorted(nodes, key=_key)

    ir = {
        "ok": True,
        "product": "POCKET Fusion Remake IR",
        "at": time.time(),
        "size": size,
        "page_hint": page.get("page_hint") or "",
        "window_titles": page.get("window_titles") or [],
        "primary_modality": page.get("primary_modality"),
        "counts": page.get("counts") or {"nodes": len(nodes)},
        "nodes": nodes,
        "reading_order_ids": [n["id"] for n in reading if n.get("id")],
        "action_hints": page.get("action_hints") or [],
        "palette": (page.get("visual") or {}).get("palette") or [],
        "levels": {
            "L0": "observe",
            "L1": "wireframe_html",
            "L2": "styled_remake",
            "L3": "scene_3d",
            "L4": "motion",
        },
    }
    return ir


def ir_to_html(ir: Dict[str, Any], *, styled: bool = True) -> str:
    """Remake a simplified HTML page from ScreenIR (wireframe or styled)."""
    W, H = (ir.get("size") or [1920, 1080])[:2]
    scale = 1.0
    # fit to 1200-wide preview
    if W > 1200:
        scale = 1200 / float(W)
    pw, ph = int(W * scale), int(H * scale)

    css = """
    * { box-sizing: border-box; }
    body { margin:0; font-family: Segoe UI, system-ui, sans-serif; background:#0b0b0f; color:#e8e8ed; }
    .stage { position:relative; width:%dpx; height:%dpx; margin:24px auto; background:#14141a;
             border:1px solid #2a2a32; border-radius:12px; overflow:hidden; box-shadow:0 20px 60px #000a; }
    .node { position:absolute; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
            font-size:11px; padding:2px 6px; border:1px solid #3a3a44; border-radius:6px; background:#1c1c24cc; }
    .btn { background:#10b98133; border-color:#34d399; color:#d1fae5; }
    .link { background:#3b82f633; border-color:#60a5fa; color:#dbeafe; text-decoration:underline; }
    .input { background:#27272a; border-color:#52525b; min-height:22px; }
    .txt, .ocr { background:transparent; border-style:dashed; color:#a1a1aa; }
    .tab { background:#27272a; border-radius:8px 8px 0 0; }
    .region { background:#f59e0b11; border-color:#f59e0b55; }
    .meta { max-width:%dpx; margin:12px auto; color:#a1a1aa; font-size:13px; }
    h1 { font-size:18px; color:#fff; margin:0 0 6px; }
    """ % (pw, ph, pw)

    parts = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>Fusion Remake</title>",
        f"<style>{css}</style></head><body>",
        f"<div class='meta'><h1>Fusion Remake — { _esc(ir.get('page_hint') or 'screen') }</h1>",
        f"<div>nodes={len(ir.get('nodes') or [])} · primary={_esc(ir.get('primary_modality') or '')} · "
        f"scale={scale:.2f}</div></div>",
        f"<div class='stage' data-src-w='{W}' data-src-h='{H}'>",
    ]

    for n in ir.get("nodes") or []:
        b = n.get("bbox")
        if not isinstance(b, list) or len(b) < 4:
            continue
        # bbox may be x,y,w,h or x0,y0,x1,y1
        x, y, a, b2 = [float(v) for v in b[:4]]
        if a > W or b2 > H:  # likely x1,y1
            w, h = a - x, b2 - y
        else:
            w, h = a, b2
        if w < 2 or h < 2:
            continue
        left, top = int(x * scale), int(y * scale)
        ww, hh = max(4, int(w * scale)), max(4, int(h * scale))
        cls = n.get("css") or "ctrl"
        label = _esc((n.get("text") or n.get("kind") or "")[:80])
        if not styled and cls not in ("btn", "link", "input"):
            cls = "ctrl"
        parts.append(
            f"<div class='node {cls}' style='left:{left}px;top:{top}px;width:{ww}px;height:{hh}px' "
            f"title='{_esc(n.get('id') or '')}'>{label}</div>"
        )

    parts.append("</div></body></html>")
    return "\n".join(parts)


def _esc(s: str) -> str:
    return (
        (s or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def ir_to_scene3d(ir: Dict[str, Any]) -> Dict[str, Any]:
    """Lightweight 3D-ready scene graph for device mock / Three.js later."""
    W, H = (ir.get("size") or [1920, 1080])[:2]
    planes = []
    for n in ir.get("nodes") or []:
        if n.get("kind") in ("button", "link", "input", "tab") and n.get("bbox"):
            planes.append(
                {
                    "id": n.get("id"),
                    "kind": n.get("kind"),
                    "text": n.get("text"),
                    "bbox": n.get("bbox"),
                    "click": n.get("click"),
                }
            )
    scene = {
        "format": "pocket.scene3d.v1",
        "camera": {"fov": 35, "position": [0, 0.2, 2.4], "look_at": [0, 0, 0]},
        "lights": [
            {"type": "ambient", "intensity": 0.45},
            {"type": "directional", "intensity": 0.9, "position": [2, 3, 4]},
            {"type": "rim", "intensity": 0.35, "position": [-2, 1, -1]},
        ],
        "environment": {"gradient": ["#0f0c29", "#302b63", "#24243e"], "style": "studio"},
        "device": {
            "type": "iphone_pro",
            "tilt_deg": [-8, 12, 0],
            "screen_aspect": round(W / max(1, H), 4),
            "shadow": True,
            "reflection": 0.18,
        },
        "ui_plane": {
            "width": W,
            "height": H,
            "texture": "from_capture_or_remake",
            "interactive_nodes": planes[:80],
        },
        "motion_presets": ["float_idle", "slow_orbit", "push_in", "scroll_demo"],
        "page_hint": ir.get("page_hint"),
    }
    return scene


def remake(
    *,
    refresh_page: bool = False,
    max_ui: int = 500,
    styled: bool = True,
) -> Dict[str, Any]:
    """Full pipeline: page → IR → HTML remake + 3D scene. Delegates to RFE-v1 when available."""
    emit("imagine", "fusion remake start", agent="OCULUS", role="python")
    t0 = time.time()
    # Production path: Recursive Fusion Engine materialization
    try:
        from pocket.rfe_kernel import materialize

        rfe = materialize(
            instruction_set="FULL_SYNTHESIS",
            refresh=refresh_page,
            max_ui=max_ui,
        )
        paths = rfe.get("paths") or {}
        out = {
            "ok": rfe.get("ok"),
            "product": "POCKET Fusion Remake (RFE-v1)",
            "agent": "OCULUS",
            "rfe": True,
            "archival_code": "RFE-2023-X1",
            "ms": int((time.time() - t0) * 1000),
            "nodes": (rfe.get("metadata") or {}).get("density"),
            "page_hint": (rfe.get("metadata") or {}).get("page_hint"),
            "primary_modality": (rfe.get("metadata") or {}).get("primary_modality"),
            "paths": {
                "ir": paths.get("ir"),
                "html": paths.get("html"),
                "scene3d": paths.get("scene3d"),
                "glsl": paths.get("glsl"),
                "packet": paths.get("packet"),
            },
            "fusion_packet": rfe.get("fusion_packet"),
            "signature_valid": rfe.get("signature_valid"),
            "scene_preview": {
                "device": "iphone_pro",
                "rfe_uuid": rfe.get("uuid"),
                "complexity_index": (rfe.get("metadata") or {}).get("complexity_index"),
            },
            "how_to_use": {
                "open_html": paths.get("html"),
                "rfe": "POST /v1/rfe/synthesize",
                "feed_studio": "POST /v1/studio/render preset rotato_phone",
                "agents": "Use fusion_packet + IR nodes; GLSL in scene for WebGL preview",
            },
            "api": {
                "remake": "POST /v1/fusion/remake",
                "rfe": "POST /v1/rfe/synthesize",
                "page": "GET /v1/vision/page",
                "studio": "POST /v1/studio/render",
            },
            "brief": rfe.get("brief"),
        }
        emit("imagine", out.get("brief") or "remake done", agent="OCULUS", role="python")
        return out
    except Exception as e:
        emit("imagine", f"RFE fallback: {e}", agent="OCULUS", role="python")

    page = None
    if refresh_page:
        from pocket.page_renderer import render_full_page

        page = render_full_page(max_ui=max_ui, visual_grid=5)

    ir = symbols_to_ir(page, max_nodes=500)
    html = ir_to_html(ir, styled=styled)
    scene = ir_to_scene3d(ir)

    stamp = int(time.time())
    base = f"remake_{stamp}"
    ir_path = REMAKES / f"{base}.ir.json"
    html_path = REMAKES / f"{base}.html"
    scene_path = SCENES / f"{base}.scene.json"

    ir_path.write_text(json.dumps(ir, indent=2, default=str)[:800000], encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    scene_path.write_text(json.dumps(scene, indent=2, default=str)[:400000], encoding="utf-8")

    out = {
        "ok": True,
        "product": "POCKET Fusion Remake",
        "agent": "OCULUS",
        "ms": int((time.time() - t0) * 1000),
        "nodes": len(ir.get("nodes") or []),
        "page_hint": ir.get("page_hint"),
        "primary_modality": ir.get("primary_modality"),
        "paths": {
            "ir": str(ir_path),
            "html": str(html_path),
            "scene3d": str(scene_path),
        },
        "scene_preview": {
            "device": scene["device"]["type"],
            "tilt_deg": scene["device"]["tilt_deg"],
            "interactive": len(scene["ui_plane"]["interactive_nodes"]),
            "motion_presets": scene["motion_presets"],
        },
        "how_to_use": {
            "open_html": str(html_path),
            "feed_studio": "POST /v1/studio/render with preset rotato_phone after capture",
            "agents": "Read IR nodes + click fields; rebuild or animate from scene3d",
        },
        "api": {
            "remake": "POST /v1/fusion/remake",
            "page": "GET /v1/vision/page",
            "studio": "POST /v1/studio/render",
            "imagine": "POST /v1/imagine/compose",
        },
        "brief": (
            f"Remake: {len(ir.get('nodes') or [])} nodes → HTML + 3D scene · "
            f"{ir.get('page_hint') or 'screen'}"
        ),
    }
    emit("imagine", out["brief"], agent="OCULUS", role="python")
    return out
