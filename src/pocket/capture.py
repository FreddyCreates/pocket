"""Screen capture & snip — paste back into the desk (no folder save required).

Returns base64 PNG for transcript embedding + optional clipboard paste.
"""

from __future__ import annotations

import base64
import io
import os
import subprocess
import time
from typing import Any, Dict, Optional, Tuple

from pocket.live_events import emit


def _clipboard_png(png_bytes: bytes) -> bool:
    try:
        import win32clipboard  # type: ignore
        from PIL import Image

        img = Image.open(io.BytesIO(png_bytes))
        # CF_DIB for clipboard
        out = io.BytesIO()
        img.convert("RGB").save(out, "BMP")
        data = out.getvalue()[14:]  # strip BMP header
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        return True
    except Exception:
        try:
            # fallback: set as image via PowerShell temp is discouraged; skip
            return False
        except Exception:
            return False


def capture_screen(*, max_width: int = 1280) -> Dict[str, Any]:
    """Full-screen (primary) capture → base64 PNG for paste-back. Does not require a save folder."""
    t0 = time.time()
    emit("capture", "Capturing screen…", agent="capture", role="python")
    try:
        from PIL import ImageGrab

        img = ImageGrab.grab(all_screens=False)
        if img.width > max_width:
            ratio = max_width / float(img.width)
            img = img.resize((max_width, int(img.height * ratio)))
        buf = io.BytesIO()
        img.save(buf, format="PNG", optimize=True)
        raw = buf.getvalue()
        # keep under ~1.5MB for JSON transcript
        if len(raw) > 1_500_000:
            img = img.convert("RGB")
            q = 70
            while len(raw) > 1_200_000 and q > 30:
                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=q)
                raw = buf.getvalue()
                q -= 10
            b64 = base64.b64encode(raw).decode("ascii")
            mime = "image/jpeg"
        else:
            b64 = base64.b64encode(raw).decode("ascii")
            mime = "image/png"
        clip = _clipboard_png(raw if mime == "image/png" else buf.getvalue())
        emit(
            "capture",
            f"Screen captured ({len(raw)} bytes) · clipboard={clip}",
            agent="capture",
            role="python",
            meta={"bytes": len(raw), "mime": mime},
        )
        return {
            "ok": True,
            "kind": "screenshot",
            "mime": mime,
            "base64": b64,
            "bytes": len(raw),
            "width": img.width,
            "height": img.height,
            "clipboard": clip,
            "saved_to_disk": False,
            "ms": int((time.time() - t0) * 1000),
            "message": "Screenshot ready — pasted to clipboard and returned to desk (not saved to a folder)",
            "markdown": f"![screenshot](data:{mime};base64,{b64})",
        }
    except Exception as e:
        emit("capture", f"Capture failed: {e}", agent="capture", role="python", level="error")
        return {"ok": False, "error": str(e), "kind": "screenshot"}


def open_snipping_tool() -> Dict[str, Any]:
    """Open Windows Snipping Tool for interactive snip; user still pastes if needed."""
    emit("snip", "Opening Snipping Tool…", agent="capture", role="python")
    try:
        # Win11: ms-screenclip: or SnippingTool
        for cmd in (
            ["cmd", "/c", "start", "", "ms-screenclip:"],
            ["snippingtool.exe"],
            ["cmd", "/c", "start", "snippingtool:"],
        ):
            try:
                subprocess.Popen(cmd, shell=False, cwd=os.path.expanduser("~"))
                emit("snip", f"Launched: {' '.join(cmd)}", agent="capture", role="python")
                return {
                    "ok": True,
                    "kind": "snip_tool",
                    "message": "Snipping Tool / Screen clip opened — snip then use `screenshot` to paste desk view, or paste into chat apps yourself",
                    "cmd": cmd,
                }
            except Exception:
                continue
        return {"ok": False, "error": "could not launch snipping tool"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def run_capture_job(prompt: str) -> Tuple[str, str, str]:
    low = (prompt or "").strip().lower()
    if low in ("help", "", "capture help"):
        return (
            "## Capture tools\n\n"
            "- `screenshot` / `capture` — full screen → base64 paste-back + clipboard (no folder)\n"
            "- `snip` / `snipping tool` — open Windows Snipping Tool\n",
            "",
            "capture",
        )
    if low in ("snip", "snipping tool", "open snip", "open snipping tool", "screenclip"):
        r = open_snipping_tool()
        return f"## Snip\n\n**{r.get('message') or r.get('error')}**\n", "" if r.get("ok") else r.get("error", ""), "capture"
    if low in ("screenshot", "capture", "screen", "shot", "grab screen"):
        r = capture_screen()
        if not r.get("ok"):
            return "", r.get("error") or "capture failed", "capture"
        # Embed image in result for live UI
        md = (
            f"## Screenshot\n\n"
            f"**{r.get('message')}** · {r.get('width')}×{r.get('height')} · {r.get('bytes')} bytes · "
            f"clipboard={r.get('clipboard')}\n\n"
            f"{r.get('markdown')}\n"
        )
        return md, "", "capture"
    return "Unknown capture command. Try `screenshot` or `snip`.", "unknown", "capture"
