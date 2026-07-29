"""Video watch for agents — local files + YouTube/HTTP.

Not full multimodal VLM by default: extracts frames + optional OCR + metadata
so Grok/Codex/Claude can *use* video evidence via the platform API.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.request import urlopen, Request

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "video_watch"
FRAMES = ROOT / "frames"
NOTES = ROOT / "notes"
for d in (ROOT, FRAMES, NOTES):
    d.mkdir(parents=True, exist_ok=True)


def _ffmpeg() -> str:
    w = shutil.which("ffmpeg")
    if w:
        return w
    root = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if root.is_dir():
        for p in root.rglob("ffmpeg.exe"):
            return str(p)
    return ""


def _yt_dlp() -> str:
    return shutil.which("yt-dlp") or shutil.which("youtube-dl") or ""


def youtube_meta(url: str) -> Dict[str, Any]:
    """Lightweight YouTube/oEmbed metadata without download."""
    u = (url or "").strip()
    if not u:
        return {"ok": False, "error": "empty url"}
    # oEmbed
    try:
        oembed = f"https://www.youtube.com/oembed?url={u}&format=json"
        req = Request(oembed, headers={"User-Agent": "POCKET/2.0"})
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode("utf-8", errors="replace"))
        return {
            "ok": True,
            "url": u,
            "title": data.get("title"),
            "author": data.get("author_name"),
            "thumbnail": data.get("thumbnail_url"),
            "provider": data.get("provider_name"),
            "method": "oembed",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "url": u}


def extract_frames_local(path: str, *, n: int = 8, max_seconds: float = 60) -> Dict[str, Any]:
    ff = _ffmpeg()
    p = Path(path)
    if not p.is_file():
        return {"ok": False, "error": f"not found: {path}"}
    if not ff:
        return {"ok": False, "error": "ffmpeg missing"}
    out_dir = FRAMES / f"v_{uuid.uuid4().hex[:8]}"
    out_dir.mkdir(parents=True, exist_ok=True)
    fps = max(0.2, min(1.5, n / max(1.0, max_seconds)))
    pattern = str(out_dir / "f_%03d.jpg")
    cmd = [ff, "-y", "-t", str(max_seconds), "-i", str(p), "-vf", f"fps={fps}", "-frames:v", str(n), "-q:v", "4", pattern]
    try:
        subprocess.run(cmd, capture_output=True, timeout=120)
    except Exception as e:
        return {"ok": False, "error": str(e)}
    files = sorted(out_dir.glob("f_*.jpg"))
    return {"ok": bool(files), "frames": [str(f) for f in files], "count": len(files), "dir": str(out_dir)}


def ocr_frames(frame_paths: List[str], *, limit: int = 6) -> Dict[str, Any]:
    lines_all: List[str] = []
    try:
        from pocket.pixel_translator import ocr_pixels
        from PIL import Image
    except Exception as e:
        return {"ok": False, "error": str(e), "lines": []}
    for fp in frame_paths[:limit]:
        try:
            img = Image.open(fp).convert("RGB")
            # downscale for OCR speed
            if img.width > 1100:
                r = 1100 / img.width
                img = img.resize((1100, int(img.height * r)))
            o = ocr_pixels(img)
            if o.get("plain_text"):
                lines_all.append(o["plain_text"][:2000])
        except Exception:
            continue
    plain = "\n---\n".join(lines_all)
    return {"ok": bool(plain), "plain_text": plain[:12000], "segments": len(lines_all)}


def watch(
    source: str,
    *,
    n_frames: int = 8,
    max_seconds: float = 45,
    want_ocr: bool = True,
) -> Dict[str, Any]:
    """Watch a local video path or YouTube URL — return meta + frames + OCR brief."""
    emit("vision", f"video_watch {source[:80]}", agent="OCULUS", role="python")
    t0 = time.time()
    src = (source or "").strip()
    out: Dict[str, Any] = {"ok": False, "source": src, "product": "POCKET Video Watch"}

    is_url = src.startswith("http://") or src.startswith("https://")
    local_path: Optional[Path] = None

    if is_url and ("youtube.com" in src or "youtu.be" in src):
        meta = youtube_meta(src)
        out["meta"] = meta
        # try yt-dlp download short clip if available
        ytd = _yt_dlp()
        if ytd:
            dest = ROOT / f"yt_{uuid.uuid4().hex[:8]}.mp4"
            try:
                subprocess.run(
                    [ytd, "-f", "mp4[height<=720]/best[height<=720]", "-o", str(dest), "--max-filesize", "40M", src],
                    capture_output=True,
                    timeout=180,
                )
                if dest.exists():
                    local_path = dest
                    out["downloaded"] = str(dest)
            except Exception as e:
                out["download_error"] = str(e)
        if not local_path:
            # no download — still useful meta for agents
            out["ok"] = bool(meta.get("ok"))
            out["brief"] = f"YouTube: {meta.get('title') or src} · {meta.get('author') or ''}"
            out["ms"] = int((time.time() - t0) * 1000)
            out["note"] = "Install yt-dlp for frame OCR on YouTube; oEmbed meta always works"
            return out
    elif is_url:
        out["meta"] = {"ok": True, "url": src, "method": "url_only"}
        out["brief"] = f"URL noted (non-YouTube): {src}"
        out["ok"] = True
        out["ms"] = int((time.time() - t0) * 1000)
        return out
    else:
        local_path = Path(src)
        if not local_path.is_file():
            # try recordings
            cand = Path.home() / ".pocket" / "recordings" / src
            if cand.is_file():
                local_path = cand
            else:
                return {"ok": False, "error": f"file not found: {src}"}

    fr = extract_frames_local(str(local_path), n=n_frames, max_seconds=max_seconds)
    out["frames"] = fr
    ocr = {"ok": False}
    if want_ocr and fr.get("frames"):
        ocr = ocr_frames(fr["frames"])
        out["ocr"] = {"ok": ocr.get("ok"), "plain_head": (ocr.get("plain_text") or "")[:2500]}
    brief_parts = [f"Watched {local_path.name if local_path else src}"]
    if out.get("meta", {}).get("title"):
        brief_parts.append(f"title={out['meta']['title']}")
    if ocr.get("plain_text"):
        brief_parts.append("OCR:\n" + ocr["plain_text"][:1200])
    out["brief"] = "\n".join(brief_parts)
    out["ok"] = True
    out["ms"] = int((time.time() - t0) * 1000)
    note_path = NOTES / f"watch_{int(time.time())}.md"
    note_path.write_text(out["brief"], encoding="utf-8")
    out["note_path"] = str(note_path)
    return out
