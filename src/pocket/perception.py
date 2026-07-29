"""Unified perception — every agent path uses the same fusion surface.

Page renderer (UIA + OCR + visual → 200–900+ symbols) is the host sensory layer.
This module is the single import for workers, virtual computer, missions, studio.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

_last: Dict[str, Any] = {}
_last_at = 0.0


def sense(
    *,
    max_ui: int = 600,
    grid: int = 5,
    force: bool = False,
    cache_sec: float = 2.0,
    include_image: bool = False,
) -> Dict[str, Any]:
    """Full fusion page model. Cached briefly so multi-step loops stay fast."""
    global _last, _last_at
    now = time.time()
    if not force and _last and (now - _last_at) < cache_sec:
        return {**_last, "cached": True}

    emit("perception", f"sense max_ui={max_ui}", agent="OCULUS", role="python")
    from pocket.page_renderer import render_full_page

    page = render_full_page(
        max_ui=max_ui,
        include_ocr=True,
        include_visual=True,
        include_image=include_image,
        visual_grid=grid,
    )
    _last = page
    _last_at = now
    page["cached"] = False
    return page


def symbol_names(page: Optional[Dict[str, Any]] = None) -> List[str]:
    p = page or _last or sense(force=False)
    out = []
    for s in p.get("symbols") or []:
        t = (s.get("text") or "").strip()
        if t and s.get("source") == "uia":
            out.append(t)
    return out


def find_symbol(query: str, page: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    from pocket.page_renderer import find_symbols

    q = (query or "").strip()
    if not q:
        return []
    # search last page; refresh if empty
    hits = find_symbols(q, page)
    if not hits:
        p = sense(force=True, max_ui=400)
        hits = find_symbols(q, p)
    return hits


def act_on_symbol(query: str) -> Dict[str, Any]:
    """Click first matching fusion symbol (grounded action)."""
    hits = find_symbol(query)
    if not hits:
        from pocket.vision_core import click_by_name

        return {"ok": False, "error": f"no symbol matching {query!r}", "fallback": click_by_name(query)}
    h = hits[0]
    click = h.get("click") or {}
    x, y = click.get("x"), click.get("y")
    if x is None or y is None:
        from pocket.vision_core import click_by_name

        return click_by_name(h.get("text") or query)
    from pocket.vision_core import click_xy

    r = click_xy(int(x), int(y))
    return {
        "ok": r.get("ok"),
        "method": "fusion_symbol_click",
        "matched": h.get("text"),
        "kind": h.get("kind"),
        "source": h.get("source"),
        "id": h.get("id"),
        **r,
    }


def agent_context(*, max_ui: int = 350) -> Dict[str, Any]:
    """Compact context every long-run agent step should see."""
    page = sense(max_ui=max_ui, grid=4, force=False)
    return {
        "brief": page.get("brief"),
        "page_hint": page.get("page_hint"),
        "primary_modality": page.get("primary_modality"),
        "counts": page.get("counts"),
        "buttons": (page.get("buttons") or [])[:25],
        "links": (page.get("links") or [])[:20],
        "action_hints": (page.get("action_hints") or [])[:15],
        "ocr_head": (page.get("ocr_plain") or "")[:800],
        "page_text_head": (page.get("page_text") or "")[:1500],
        "symbol_sample": [
            {"text": s.get("text"), "kind": s.get("kind"), "click": s.get("click")}
            for s in (page.get("symbols") or [])[:40]
            if s.get("source") == "uia" and s.get("text")
        ],
    }
