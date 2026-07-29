"""Synchronous real-time bridge — open session for live observe → decide → act.

Outer agent (Grok / Codex / human) drives the loop via API:
  POST /v1/bridge/open
  POST /v1/bridge/{id}/observe
  POST /v1/bridge/{id}/act   {action, ...}
  GET  /v1/bridge/{id}
  POST /v1/bridge/{id}/close

This is NOT a prewritten demo script. Each act is chosen after seeing observe output.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "bridges"
ROOT.mkdir(parents=True, exist_ok=True)

_lock = Lock()
_BRIDGES: Dict[str, Dict[str, Any]] = {}


def open_bridge(*, title: str = "live", record: bool = True) -> Dict[str, Any]:
    bid = f"br-{uuid.uuid4().hex[:10]}"
    rec_path = None
    if record:
        try:
            from pocket.screen_record import record_start

            rs = record_start(label=f"bridge-{bid[-6:]}")
            rec_path = rs.get("path")
            time.sleep(0.6)
        except Exception as e:
            rec_path = None
            emit("bridge", f"record start fail: {e}", agent="BRIDGE", role="host")

    try:
        from pocket.live_vision import ensure_vision

        ensure_vision(interval=0.7)
    except Exception:
        pass

    br = {
        "id": bid,
        "title": title,
        "status": "open",
        "created_at": time.time(),
        "recording_path": rec_path,
        "steps": [],
        "last_observe": None,
    }
    with _lock:
        _BRIDGES[bid] = br
    _persist(br)
    emit("bridge", f"Bridge open {bid} record={bool(rec_path)}", agent="BRIDGE", role="host")
    return {"ok": True, **{k: br[k] for k in br if k != "last_observe"}}


def get_bridge(bid: str) -> Optional[Dict[str, Any]]:
    with _lock:
        br = _BRIDGES.get(bid)
    if br:
        return br
    p = ROOT / f"{bid}.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


def _persist(br: Dict[str, Any]) -> None:
    slim = {k: v for k, v in br.items() if k != "last_observe"}
    # keep last observe summary without huge b64
    lo = br.get("last_observe") or {}
    slim["last_observe_summary"] = {
        k: lo.get(k)
        for k in ("ok", "ui_map_count", "window_titles", "ui_names", "links_on_page", "at")
        if k in lo or k == "links_on_page"
    }
    if "links_on_page" in lo:
        slim["last_observe_summary"]["links_on_page"] = lo.get("links_on_page")
    try:
        (ROOT / f"{br['id']}.json").write_text(json.dumps(slim, indent=2, default=str)[:150000], encoding="utf-8")
    except Exception:
        pass


def observe_bridge(bid: str) -> Dict[str, Any]:
    """Full sensory snapshot for the outer agent to read and decide next act."""
    br = get_bridge(bid)
    if not br or br.get("status") != "open":
        return {"ok": False, "error": "bridge not open"}

    from pocket.vision_core import observe, grab_frame
    from pocket.live_vision import latest_frame

    obs = observe(with_ui_map=True, with_ocr=True, with_understand=True)
    # Extract likely link-like / navigational names from UI map
    names = obs.get("ui_names") or []
    links = []
    link_keywords = (
        "http", "www", "link", "open", "view", "read", "more", "repo", "issue",
        "pull", "file", "readme", "doc", "about", "explore", "trending", "follow",
        "profile", "home", "search", "notification", "post", "article", "code",
    )
    for n in names:
        nl = (n or "").lower()
        if any(k in nl for k in link_keywords) or (len(n) > 3 and n[:1].isupper()):
            links.append(n)
    # also full elements that look like hyperlinks
    try:
        from pocket.vision_core import UI_MAP_PATH
        import json as _json

        if UI_MAP_PATH.exists():
            um = _json.loads(UI_MAP_PATH.read_text(encoding="utf-8"))
            for el in um.get("elements") or []:
                t = (el.get("type") or "").lower()
                n = el.get("name") or ""
                if "hyperlink" in t or "link" in t or "text" in t:
                    if n and n not in links and 2 < len(n) < 60:
                        links.append(n)
    except Exception:
        pass

    frame = latest_frame(include_image=False)
    # small image preview for agent (optional length)
    grab = grab_frame(max_width=640)
    b64 = grab.get("base64") or ""
    # Don't send mega payloads; truncate note
    brief = obs.get("brief") or ""
    primary = obs.get("primary_modality") or ""
    result = {
        "ok": True,
        "bridge_id": bid,
        "at": time.time(),
        "window_titles": obs.get("window_titles") or [],
        "active_hint": obs.get("page_hint") or _active_page_hint(obs.get("window_titles") or []),
        "primary_modality": primary,
        "why_primary": obs.get("why_primary"),
        "brief": brief,
        "ui_map_count": obs.get("ui_map_count") or 0,
        "ui_names": (names or obs.get("ui_names") or [])[:50],
        "links_on_page": (obs.get("links_on_page") or links)[:40],
        "buttons": obs.get("buttons") or [],
        "ocr_plain": (obs.get("ocr_plain") or "")[:1500],
        "visual": obs.get("visual") or {},
        "action_hints": obs.get("action_hints") or [],
        "clickable_sample": (obs.get("clickable_sample") or [])[:20],
        "vision_seq": frame.get("seq"),
        "vision_path": frame.get("path"),
        "has_preview": bool(b64),
        "preview_b64_len": len(b64),
        "message": brief
        or (
            f"Page hint: {_active_page_hint(obs.get('window_titles') or [])}. "
            f"UI elements: {obs.get('ui_map_count')}. "
            f"Link-like names: {len(links)}."
        ),
    }
    # Attach limited preview for local tools (optional)
    if b64 and len(b64) < 120_000:
        result["preview_jpeg_b64"] = b64
        result["preview_mime"] = grab.get("mime") or "image/jpeg"

    br["last_observe"] = result
    br["steps"].append({"type": "observe", "at": time.time(), "summary": result["message"]})
    with _lock:
        _BRIDGES[bid] = br
    _persist(br)
    emit("bridge", f"observe: {result['message'][:120]}", agent="BRIDGE", role="python")
    return result


def _active_page_hint(titles: List[str]) -> str:
    for t in titles:
        tl = t.lower()
        if "x.com" in tl or "twitter" in tl:
            return f"X/Twitter — {t}"
        if "github" in tl:
            return f"GitHub — {t}"
        if "edge" in tl or "chrome" in tl:
            return f"Browser — {t}"
        if "tradingview" in tl:
            return f"TradingView — {t}"
    return titles[0] if titles else "(no window title)"


def act_bridge(bid: str, action: str, **kwargs) -> Dict[str, Any]:
    """Execute one real-time action chosen after observe."""
    br = get_bridge(bid)
    if not br or br.get("status") != "open":
        return {"ok": False, "error": "bridge not open"}

    action = (action or "").strip().lower().replace("-", "_")
    emit("bridge", f"act {action} {kwargs.get('name') or kwargs.get('url') or ''}"[:100], agent="BRIDGE", role="python")
    result: Dict[str, Any] = {"ok": False}

    try:
        if action in ("scroll", "scroll_down"):
            from pocket.ui_click import scroll_page

            result = scroll_page(int(kwargs.get("n") or 3), direction="down")
        elif action == "scroll_up":
            from pocket.ui_click import scroll_page

            result = scroll_page(int(kwargs.get("n") or 2), direction="up")
        elif action in ("click", "click_name", "click_link"):
            from pocket.vision_core import click_by_name

            name = kwargs.get("name") or kwargs.get("text") or kwargs.get("link") or ""
            # Prefer vision map click from last observe names
            result = click_by_name(name, rebuild=True)
            result["requested_name"] = name
        elif action == "click_xy":
            from pocket.vision_core import click_xy

            result = click_xy(int(kwargs.get("x") or 0), int(kwargs.get("y") or 0))
        elif action in ("open_url", "edge"):
            from pocket.browser_mode import open_edge_url

            result = open_edge_url(kwargs.get("url") or kwargs.get("prompt") or "https://x.com/home", new_window=True)
            time.sleep(1.5)
        elif action == "open_x":
            from pocket.browser_mode import open_edge_url

            result = open_edge_url("https://x.com/home", new_window=True)
            time.sleep(2.0)
        elif action == "open_app":
            from pocket.desktop import open_app

            result = open_app(kwargs.get("app") or "notepad")
        elif action == "maximize":
            from pocket.ui_click import maximize_foreground

            result = maximize_foreground()
        elif action == "focus":
            from pocket.ui_maneuver import focus_window_title

            result = focus_window_title(kwargs.get("title") or "Edge")
        elif action == "screenshot":
            from pocket.capture import capture_screen

            result = capture_screen(max_width=1000)
        elif action == "type":
            from pocket.ui_maneuver import set_clipboard, send_keys

            set_clipboard(kwargs.get("text") or "")
            result = send_keys("^v", settle_ms=300)
        elif action == "enter":
            from pocket.ui_maneuver import send_keys

            result = send_keys("{ENTER}", settle_ms=200)
        elif action == "wait":
            time.sleep(float(kwargs.get("sec") or 1.0))
            result = {"ok": True, "waited": kwargs.get("sec") or 1.0}
        else:
            result = {"ok": False, "error": f"unknown action: {action}"}
    except Exception as e:
        result = {"ok": False, "error": str(e)}

    br["steps"].append(
        {
            "type": "act",
            "action": action,
            "kwargs": {k: v for k, v in kwargs.items() if k != "preview_jpeg_b64"},
            "ok": result.get("ok"),
            "at": time.time(),
            "detail": {k: result.get(k) for k in ("message", "error", "matched", "method", "url") if k in result},
        }
    )
    with _lock:
        _BRIDGES[bid] = br
    _persist(br)
    return {"ok": bool(result.get("ok")), "bridge_id": bid, "action": action, "result": result}


def close_bridge(bid: str) -> Dict[str, Any]:
    br = get_bridge(bid)
    if not br:
        return {"ok": False, "error": "not found"}
    rec = None
    if br.get("recording_path"):
        try:
            from pocket.screen_record import record_stop

            rec = record_stop()
        except Exception as e:
            rec = {"ok": False, "error": str(e)}
    br["status"] = "closed"
    br["closed_at"] = time.time()
    br["recording_final"] = rec
    with _lock:
        _BRIDGES[bid] = br
    _persist(br)
    emit("bridge", f"Bridge closed {bid}", agent="BRIDGE", role="host")
    return {
        "ok": True,
        "id": bid,
        "steps": len(br.get("steps") or []),
        "recording": rec,
        "message": f"Bridge closed · steps={len(br.get('steps') or [])} · video={(rec or {}).get('path')}",
    }


def list_bridges() -> List[Dict[str, Any]]:
    with _lock:
        return [
            {"id": b["id"], "status": b["status"], "title": b.get("title"), "steps": len(b.get("steps") or [])}
            for b in _BRIDGES.values()
        ]
