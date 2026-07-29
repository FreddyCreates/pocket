"""Live vision — continuous screen frames for desk + agents (real-time eyes).

Writes latest frame under ~/.pocket/live/ and serves via API.
Does NOT start competing video recorders (user's recorder stays alone).
"""

from __future__ import annotations

import base64
import io
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

from pocket.live_events import emit

LIVE = Path.home() / ".pocket" / "live"
LIVE.mkdir(parents=True, exist_ok=True)
FRAME_PATH = LIVE / "frame.jpg"
META_PATH = LIVE / "frame.json"

_lock = threading.Lock()
_thread: Optional[threading.Thread] = None
_stop = threading.Event()
_started = False
_latest_b64 = ""
_seq = 0


def ensure_vision(*, interval: float = 1.2) -> None:
    global _started, _thread
    with _lock:
        if _started and _thread and _thread.is_alive():
            return
        _stop.clear()
        _thread = threading.Thread(target=_loop, args=(interval,), name="pocket-vision", daemon=True)
        _thread.start()
        _started = True
        emit("vision", "Live vision online (frame feed)", agent="OCULUS", role="python")


def _loop(interval: float) -> None:
    global _latest_b64, _seq
    while not _stop.is_set():
        try:
            from PIL import ImageGrab

            img = ImageGrab.grab(all_screens=False)
            # scale for bandwidth
            max_w = 960
            if img.width > max_w:
                ratio = max_w / float(img.width)
                img = img.resize((max_w, int(img.height * ratio)))
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=55)
            raw = buf.getvalue()
            FRAME_PATH.write_bytes(raw)
            b64 = base64.b64encode(raw).decode("ascii")
            with _lock:
                _latest_b64 = b64
                _seq += 1
                seq = _seq
            META_PATH.write_text(
                f'{{"seq":{seq},"at":{time.time()},"bytes":{len(raw)},"w":{img.width},"h":{img.height}}}',
                encoding="utf-8",
            )
        except Exception:
            pass
        _stop.wait(interval)


def latest_frame(*, include_image: bool = True) -> Dict[str, Any]:
    ensure_vision()
    with _lock:
        b64 = _latest_b64
        seq = _seq
    out: Dict[str, Any] = {
        "ok": True,
        "seq": seq,
        "path": str(FRAME_PATH) if FRAME_PATH.exists() else None,
        "agent": "OCULUS",
        "message": "Latest screen frame for desk + agents",
    }
    if include_image and b64:
        out["mime"] = "image/jpeg"
        out["base64"] = b64
        out["markdown"] = f"![live](data:image/jpeg;base64,{b64})"
    elif FRAME_PATH.exists():
        raw = FRAME_PATH.read_bytes()
        b64 = base64.b64encode(raw).decode("ascii")
        out["mime"] = "image/jpeg"
        out["base64"] = b64
        out["markdown"] = f"![live](data:image/jpeg;base64,{b64})"
    return out


def stop_vision() -> None:
    global _started
    _stop.set()
    _started = False
