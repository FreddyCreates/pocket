"""POCKET Video Studio — polish SPECULUM recordings into viral marketing demos.

Presets (real X-style, not flat nonsense crops):
  · rotato_phone  — 9:16 floating phone, letterboxed glass, studio gradient (DEFAULT viral)
  · x_screencast  — 16:9 Notion/Figma-style clean screencast polish
  · macbook_web   — 16:9 laptop + browser chrome, content contain
  · viral_phone   — alias → rotato_phone
  · viral_web     — alias → macbook_web
  · clean_demo    — 16:9 crisp recut with intro/outro cards
  · story_stack   — 9:16 multi-beat vertical story

Rule: never force-cover-crop the product UI into a bezel. CONTAIN into glass.
All renders use local ffmpeg. Inputs ~/.pocket/recordings/ → ~/.pocket/studio/exports/
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit

REC_DIR = Path.home() / ".pocket" / "recordings"
STUDIO = Path.home() / ".pocket" / "studio"
EXPORTS = STUDIO / "exports"
ASSETS = STUDIO / "assets"
JOBS = STUDIO / "jobs"
for d in (REC_DIR, EXPORTS, ASSETS, JOBS):
    d.mkdir(parents=True, exist_ok=True)

PRESETS: Dict[str, Dict[str, Any]] = {
    "rotato_phone": {
        "id": "rotato_phone",
        "label": "Rotato-style 3D Phone (viral)",
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "desc": "Studio gradient, floating phone chassis, CONTAIN letterbox glass, shadow, captions",
        "style": "rotato_phone",
    },
    "x_screencast": {
        "id": "x_screencast",
        "label": "X Screencast Polish (Notion/Figma style)",
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "desc": "Full readable UI, soft pad, hook caption, CTA — no fake phone",
        "style": "x_screencast",
    },
    "macbook_web": {
        "id": "macbook_web",
        "label": "MacBook / Browser Viral Web",
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "desc": "Laptop frame + browser dots, content contain into screen",
        "style": "macbook_web",
    },
    "viral_phone": {
        "id": "viral_phone",
        "label": "Viral iPhone (alias rotato_phone)",
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "desc": "Alias of rotato_phone — real glass letterbox, not flat crop",
        "style": "rotato_phone",
    },
    "viral_web": {
        "id": "viral_web",
        "label": "Viral Web (alias macbook_web)",
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "desc": "Alias of macbook_web",
        "style": "macbook_web",
    },
    "clean_demo": {
        "id": "clean_demo",
        "label": "Clean Product Demo",
        "aspect": "16:9",
        "width": 1920,
        "height": 1080,
        "desc": "Intro bar + source + lower third — fundraise / site embed",
        "style": "clean",
    },
    "story_stack": {
        "id": "story_stack",
        "label": "Story Stack 9:16",
        "aspect": "9:16",
        "width": 1080,
        "height": 1920,
        "desc": "Hook → proof → CTA vertical story",
        "style": "story",
    },
    "square_social": {
        "id": "square_social",
        "label": "Square Social 1:1",
        "aspect": "1:1",
        "width": 1080,
        "height": 1080,
        "desc": "LinkedIn / IG feed square contain + caption",
        "style": "square",
    },
}


def _ffmpeg() -> str:
    w = shutil.which("ffmpeg")
    if w:
        return w
    root = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if root.is_dir():
        for p in root.rglob("ffmpeg.exe"):
            return str(p)
    return ""


def _ffprobe() -> str:
    ff = _ffmpeg()
    if not ff:
        return ""
    p = Path(ff).with_name("ffprobe.exe" if ff.lower().endswith(".exe") else "ffprobe")
    return str(p) if p.exists() else shutil.which("ffprobe") or ""


def list_recordings(limit: int = 40) -> List[Dict[str, Any]]:
    files = sorted(REC_DIR.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for f in files[:limit]:
        st = f.stat()
        out.append(
            {
                "name": f.name,
                "path": str(f),
                "bytes": st.st_size,
                "mtime": st.st_mtime,
                "size_mb": round(st.st_size / 1e6, 2),
            }
        )
    return out


def list_exports(limit: int = 40) -> List[Dict[str, Any]]:
    files = sorted(EXPORTS.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for f in files[:limit]:
        st = f.stat()
        out.append(
            {
                "name": f.name,
                "path": str(f),
                "bytes": st.st_size,
                "mtime": st.st_mtime,
                "size_mb": round(st.st_size / 1e6, 2),
            }
        )
    return out


def list_presets() -> List[Dict[str, Any]]:
    return list(PRESETS.values())


def _probe_duration(path: Path) -> float:
    probe = _ffprobe()
    if not probe:
        return 0.0
    try:
        r = subprocess.run(
            [probe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return float((r.stdout or "0").strip() or 0)
    except Exception:
        return 0.0


def _escape_drawtext(s: str) -> str:
    # ffmpeg drawtext escaping for Windows
    s = (s or "").replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    s = s.replace("%", "\\%")
    return s[:120]


def _ensure_studio_bg(w: int, h: int) -> Path:
    """Studio gradient used behind floating devices (Rotato-class)."""
    path = ASSETS / f"studio_bg_{w}x{h}.png"
    if path.exists():
        return path
    from PIL import Image

    colors = [(15, 12, 41), (48, 43, 99), (36, 36, 62)]
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        if t < 0.5:
            u = t * 2
            c0, c1 = colors[0], colors[1]
        else:
            u = (t - 0.5) * 2
            c0, c1 = colors[1], colors[2]
        r = int(c0[0] + (c1[0] - c0[0]) * u)
        g = int(c0[1] + (c1[1] - c0[1]) * u)
        b = int(c0[2] + (c1[2] - c0[2]) * u)
        for x in range(w):
            vx = 1.0 - abs(x / w - 0.5) * 0.3
            px[x, y] = (int(r * vx), int(g * vx), int(b * vx))
    img.save(path, "PNG")
    return path


def _ensure_phone_chassis_overlay(w: int = 1080, h: int = 1920) -> Tuple[Path, Dict[str, int]]:
    """Phone chrome with TRANSPARENT glass hole — content shows through correctly.

    Open-source mockup craft (Rotato / Screen Studio class): device is a stage;
    glass is letterboxed content, never a stretched fill-crop of the desktop.
    """
    path = ASSETS / f"phone_chassis_v2_{w}x{h}.png"
    mx = int(w * 0.12)
    my = int(h * 0.09)
    inset = 18
    glass = {
        "x": mx + inset,
        "y": my + 44,
        "w": w - 2 * (mx + inset),
        "h": h - 2 * my - 44 - 36,
    }
    if path.exists():
        return path, glass

    from PIL import Image, ImageDraw, ImageFilter

    x0, y0, x1, y1 = mx, my, w - mx, h - my
    gx, gy, gw, gh = glass["x"], glass["y"], glass["w"], glass["h"]

    # shadow layer
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([x0 + 40, y1 - 45, x1 - 40, y1 + 60], fill=(0, 0, 0, 130))
    shadow = shadow.filter(ImageFilter.GaussianBlur(30))

    # body with alpha mask: draw opaque body, clear glass via mask
    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([x0, y0, x1, y1], radius=54, fill=(22, 22, 28, 255))
    # punch glass (fully transparent)
    clear = Image.new("L", (w, h), 0)
    cd = ImageDraw.Draw(clear)
    cd.rounded_rectangle([x0, y0, x1, y1], radius=54, fill=255)
    cd.rounded_rectangle([gx, gy, gx + gw, gy + gh], radius=10, fill=0)
    body.putalpha(clear)

    # chrome details on separate layer (island + home + rim) — only on non-glass
    chrome = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ch = ImageDraw.Draw(chrome)
    ch.rounded_rectangle([x0, y0, x1, y1], radius=54, outline=(110, 110, 120, 255), width=5)
    # inner rim
    ch.rounded_rectangle([x0 + 5, y0 + 5, x1 - 5, y1 - 5], radius=50, outline=(50, 50, 58, 200), width=2)
    # dynamic island
    iw = int((x1 - x0) * 0.30)
    ch.rounded_rectangle(
        [(x0 + x1 - iw) // 2, y0 + 16, (x0 + x1 + iw) // 2, y0 + 40],
        radius=12,
        fill=(6, 6, 10, 255),
    )
    # home indicator
    bw = int((x1 - x0) * 0.28)
    ch.rounded_rectangle(
        [(x0 + x1 - bw) // 2, y1 - 28, (x0 + x1 + bw) // 2, y1 - 16],
        radius=4,
        fill=(235, 235, 245, 230),
    )
    # glass edge
    ch.rounded_rectangle([gx - 1, gy - 1, gx + gw + 1, gy + gh + 1], radius=10, outline=(70, 70, 80, 160), width=2)

    # subtle top specular on body (not glass)
    spec = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sp = ImageDraw.Draw(spec)
    sp.polygon(
        [(x0 + 20, y0 + 20), (x0 + int((x1 - x0) * 0.45), y0 + 20), (x0 + 20, y0 + int((y1 - y0) * 0.4))],
        fill=(255, 255, 255, 22),
    )

    img = Image.alpha_composite(shadow, body)
    img = Image.alpha_composite(img, chrome)
    img = Image.alpha_composite(img, spec)
    img.save(path, "PNG")
    return path, glass


def _ensure_phone_frame(w: int = 1080, h: int = 1920) -> Path:
    """Legacy name → chassis overlay path."""
    p, _ = _ensure_phone_chassis_overlay(w, h)
    return p


def _ensure_font() -> str:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\seguisb.ttf",
    ]
    for c in candidates:
        if Path(c).exists():
            # ffmpeg on Windows wants escaped colons in path for drawtext
            return c.replace("\\", "/").replace(":", "\\:")
    return ""


def render(
    source: str,
    *,
    preset: str = "rotato_phone",
    title: str = "POCKET",
    subtitle: str = "Host co-pilot demo",
    caption: str = "",
    cta: str = "Try POCKET",
    brand: str = "ItsNotAI Labs",
    max_seconds: float = 0,
    start_seconds: float = 0,
    speed: float = 1.0,
) -> Dict[str, Any]:
    """Render one polished export from a raw recording."""
    ff = _ffmpeg()
    if not ff:
        return {"ok": False, "error": "ffmpeg not found"}

    src = Path(source)
    if not src.is_file():
        # allow basename from recordings dir
        cand = REC_DIR / source
        if cand.is_file():
            src = cand
        else:
            return {"ok": False, "error": f"source not found: {source}"}

    # normalize aliases
    preset = (preset or "rotato_phone").lower()
    if preset == "viral_phone":
        preset = "rotato_phone"
    if preset == "viral_web":
        preset = "macbook_web"

    pr = PRESETS.get(preset) or PRESETS["rotato_phone"]
    W, H = int(pr["width"]), int(pr["height"])
    style = pr.get("style") or "rotato_phone"
    job_id = f"job-{uuid.uuid4().hex[:8]}"
    out_name = f"{src.stem}__{preset}__{int(time.time())}.mp4"
    out = EXPORTS / out_name

    title = title or "POCKET"
    subtitle = subtitle or "Real host demo"
    caption = caption or subtitle
    cta = cta or "Built with POCKET"
    brand = brand or "ItsNotAI Labs"
    font = _ensure_font()
    font_opt = f":fontfile='{font}'" if font else ""

    emit("studio", f"Render {preset} ← {src.name}", agent="STUDIO", role="python")

    # duration trim
    ss = ["-ss", str(max(0, start_seconds))] if start_seconds > 0 else []
    t_args = ["-t", str(max_seconds)] if max_seconds and max_seconds > 0 else []
    speed_f = f",setpts={1.0/speed}*PTS" if abs(speed - 1.0) > 0.05 else ""

    cmd: List[str] = [ff, "-y"]
    cmd += ss
    cmd += ["-i", str(src)]
    cmd += t_args

    # ----- Rotato-style phone: bg + contain content into glass + chassis -----
    if style == "rotato_phone":
        bg = _ensure_studio_bg(W, H)
        chassis, glass = _ensure_phone_chassis_overlay(W, H)
        gx, gy, gw, gh = glass["x"], glass["y"], glass["w"], glass["h"]
        # contain (letterbox) into glass — NEVER cover-crop the product UI
        # pad color near black for glass
        fc = (
            f"[0:v]scale={gw}:{gh}:force_original_aspect_ratio=decrease{speed_f},"
            f"pad={gw}:{gh}:(ow-iw)/2:(oh-ih)/2:color=0x0a0a0e[scr];"
            f"[1:v]scale={W}:{H}[bg];"
            f"[bg][scr]overlay={gx}:{gy}[mid];"
            f"[2:v]format=rgba[ch];"
            f"[mid][ch]overlay=0:0:format=auto,"
            f"drawtext=text='{_escape_drawtext(title)}'{font_opt}:fontsize=48:fontcolor=white:"
            f"x=(w-text_w)/2:y=36:borderw=2:bordercolor=black@0.5,"
            f"drawtext=text='{_escape_drawtext(caption)}'{font_opt}:fontsize=28:fontcolor=0x34d399:"
            f"x=(w-text_w)/2:y=h-130:borderw=1:bordercolor=black@0.5,"
            f"drawtext=text='{_escape_drawtext(cta)}'{font_opt}:fontsize=32:fontcolor=white:"
            f"x=(w-text_w)/2:y=h-78:box=1:boxcolor=0x10b981@0.9:boxborderw=12[v]"
        )
        cmd += ["-i", str(bg), "-i", str(chassis), "-filter_complex", fc, "-map", "[v]"]

    # ----- X screencast polish: readable full UI, no fake phone -----
    elif style == "x_screencast":
        # contain into frame with soft dark pad (product stays readable)
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=decrease{speed_f},"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0c0c10,"
            f"drawbox=x=0:y=0:w=iw:h=72:color=black@0.55:t=fill,"
            f"drawtext=text='{_escape_drawtext(title)}'{font_opt}:fontsize=36:fontcolor=white:x=40:y=22,"
            f"drawtext=text='{_escape_drawtext(brand)}'{font_opt}:fontsize=22:fontcolor=0x34d399:x=w-text_w-40:y=28,"
            f"drawbox=x=0:y=ih-88:w=iw:h=88:color=black@0.55:t=fill,"
            f"drawtext=text='{_escape_drawtext(subtitle)}'{font_opt}:fontsize=30:fontcolor=white:x=40:y=h-62,"
            f"drawtext=text='{_escape_drawtext(cta)}'{font_opt}:fontsize=26:fontcolor=0x052e16:"
            f"x=w-text_w-40:y=h-58:box=1:boxcolor=0x34d399@0.95:boxborderw=10"
        )
        cmd += ["-vf", vf]

    # ----- MacBook / browser web viral -----
    elif style == "macbook_web":
        bg = _ensure_studio_bg(W, H)
        # screen region inside laptop-ish frame
        sx, sy, sw, sh = int(W * 0.08), int(H * 0.12), int(W * 0.84), int(H * 0.68)
        # chrome height
        ch = 36
        fc = (
            f"[0:v]scale={sw}:{sh - ch}:force_original_aspect_ratio=decrease{speed_f},"
            f"pad={sw}:{sh - ch}:(ow-iw)/2:(oh-ih)/2:color=0x141418[scr];"
            f"[1:v]scale={W}:{H},"
            f"drawbox=x={sx - 10}:y={sy - 10}:w={sw + 20}:h={sh + 40}:color=0x1c1c22@1:t=fill,"
            f"drawbox=x={sx}:y={sy}:w={sw}:h={ch}:color=0x2a2a30@1:t=fill,"
            f"drawbox=x={sx + 14}:y={sy + 12}:w=12:h=12:color=0xff5f57@1:t=fill,"
            f"drawbox=x={sx + 34}:y={sy + 12}:w=12:h=12:color=0xfebc2e@1:t=fill,"
            f"drawbox=x={sx + 54}:y={sy + 12}:w=12:h=12:color=0x28c840@1:t=fill,"
            f"drawtext=text='{_escape_drawtext(brand + ' · ' + title)}'{font_opt}:fontsize=18:fontcolor=white:"
            f"x={sx + 90}:y={sy + 10}[frame];"
            f"[frame][scr]overlay={sx}:{sy + ch},"
            f"drawbox=x=0:y=ih-80:w=iw:h=80:color=black@0.5:t=fill,"
            f"drawtext=text='{_escape_drawtext(subtitle)}'{font_opt}:fontsize=32:fontcolor=white:x=48:y=h-55,"
            f"drawtext=text='{_escape_drawtext(cta)}'{font_opt}:fontsize=26:fontcolor=0x052e16:"
            f"x=w-text_w-48:y=h-52:box=1:boxcolor=0x34d399@0.95:boxborderw=10[v]"
        )
        cmd += ["-i", str(bg), "-filter_complex", fc, "-map", "[v]"]

    elif style == "story":
        # vertical story with CONTAIN not cover
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=decrease{speed_f},"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0c0c10,"
            f"drawbox=x=0:y=0:w=iw:h=140:color=black@0.5:t=fill,"
            f"drawtext=text='{_escape_drawtext(title)}'{font_opt}:fontsize=52:fontcolor=white:x=(w-text_w)/2:y=50,"
            f"drawtext=text='{_escape_drawtext(caption)}'{font_opt}:fontsize=30:fontcolor=0x34d399:x=(w-text_w)/2:y=h-180,"
            f"drawtext=text='{_escape_drawtext(cta)}'{font_opt}:fontsize=34:fontcolor=white:"
            f"x=(w-text_w)/2:y=h-110:box=1:boxcolor=0x10b981@0.85:boxborderw=12"
        )
        cmd += ["-vf", vf]

    elif style == "square":
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=decrease{speed_f},"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x0c0c10,"
            f"drawbox=x=0:y=h-140:w=iw:h=140:color=black@0.55:t=fill,"
            f"drawtext=text='{_escape_drawtext(title)}'{font_opt}:fontsize=44:fontcolor=white:x=40:y=h-100,"
            f"drawtext=text='{_escape_drawtext(cta)}'{font_opt}:fontsize=26:fontcolor=0x34d399:x=40:y=h-50"
        )
        cmd += ["-vf", vf]

    else:  # clean
        vf = (
            f"scale={W}:{H}:force_original_aspect_ratio=decrease{speed_f},"
            f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=0x09090b,"
            f"drawbox=x=0:y=0:w=iw:h=64:color=0x09090b@0.75:t=fill,"
            f"drawtext=text='{_escape_drawtext(title)}'{font_opt}:fontsize=32:fontcolor=white:x=32:y=18,"
            f"drawtext=text='{_escape_drawtext(brand)}'{font_opt}:fontsize=22:fontcolor=0x34d399:x=w-text_w-32:y=22,"
            f"drawbox=x=0:y=ih-56:w=iw:h=56:color=0x09090b@0.7:t=fill,"
            f"drawtext=text='{_escape_drawtext(caption or subtitle)}'{font_opt}:fontsize=24:fontcolor=white:x=32:y=h-40"
        )
        cmd += ["-vf", vf]

    cmd += [
        "-an",  # mute for clean marketing loops
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out),
    ]

    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        ok = r.returncode == 0 and out.exists() and out.stat().st_size > 1000
        job = {
            "id": job_id,
            "ok": ok,
            "preset": preset,
            "source": str(src),
            "output": str(out) if ok else "",
            "bytes": out.stat().st_size if ok else 0,
            "ms": int((time.time() - t0) * 1000),
            "duration_src": _probe_duration(src),
            "title": title,
            "stderr_tail": (r.stderr or "")[-1500:],
            "cmd": " ".join(cmd[:8]) + " …",
        }
        (JOBS / f"{job_id}.json").write_text(json.dumps(job, indent=2), encoding="utf-8")
        if not ok:
            return {"ok": False, "error": "ffmpeg failed", **job}
        emit("studio", f"Export ready {out.name}", agent="STUDIO", role="python")
        return {
            "ok": True,
            "job_id": job_id,
            "preset": preset,
            "preset_label": pr.get("label"),
            "source": str(src),
            "output": str(out),
            "name": out.name,
            "bytes": out.stat().st_size,
            "size_mb": round(out.stat().st_size / 1e6, 2),
            "message": f"Studio export: {out.name} ({pr.get('label')})",
            "agent": "STUDIO",
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def render_batch(
    source: str,
    *,
    presets: Optional[List[str]] = None,
    title: str = "POCKET",
    subtitle: str = "Host co-pilot",
    caption: str = "",
    cta: str = "Try POCKET",
) -> Dict[str, Any]:
    """Render multiple viral formats from one recording (phone + web + clean)."""
    presets = presets or ["rotato_phone", "x_screencast", "macbook_web"]
    results = []
    for p in presets:
        results.append(
            render(
                source,
                preset=p,
                title=title,
                subtitle=subtitle,
                caption=caption or subtitle,
                cta=cta,
            )
        )
    ok_n = sum(1 for r in results if r.get("ok"))
    return {
        "ok": ok_n > 0,
        "count": ok_n,
        "total": len(results),
        "exports": results,
        "message": f"Batch studio: {ok_n}/{len(results)} formats from {Path(source).name}",
    }


def auto_viral_pack(source: str = "", **meta) -> Dict[str, Any]:
    """Product pack: lifelike phone remake + web still + work screencast.

    Research rule: viral glass is product-remade frames in a lifelike iPhone,
    not a desktop recording force-cropped into a flat bezel.
    """
    if not source:
        recs = list_recordings(1)
        if not recs:
            return {"ok": False, "error": "no recordings in ~/.pocket/recordings"}
        source = recs[0]["path"]
    title = meta.get("title") or "POCKET"
    subtitle = meta.get("subtitle") or "Host co-pilot"
    caption = meta.get("caption") or subtitle
    exports: List[Dict[str, Any]] = []
    try:
        from pocket.device_remake import product_phone_from_recording, product_web_from_image

        exports.append(
            product_phone_from_recording(
                source,
                title=title,
                caption=caption,
                max_seconds=float(meta.get("max_seconds") or 12),
                n_frames=int(meta.get("n_frames") or 10),
            )
        )
        exports.append(
            product_web_from_image(None, title=title, brand=meta.get("brand") or "pocket.local")
        )
    except Exception as e:
        exports.append({"ok": False, "error": f"product remake: {e}"})
    exports.append(
        render(
            source,
            preset="x_screencast",
            title=title,
            subtitle=subtitle,
            caption=caption,
            cta=meta.get("cta") or "ItsNotAI Labs",
            max_seconds=float(meta.get("max_seconds") or 12),
        )
    )
    ok_n = sum(1 for r in exports if r.get("ok"))
    return {
        "ok": ok_n > 0,
        "count": ok_n,
        "total": len(exports),
        "exports": exports,
        "source": source,
        "message": f"Product pack {ok_n}/{len(exports)} (phone remake + web + screencast)",
        "method": "device_remake + x_screencast",
    }


def studio_status() -> Dict[str, Any]:
    return {
        "ok": True,
        "ffmpeg": bool(_ffmpeg()),
        "ffmpeg_path": _ffmpeg(),
        "recordings": len(list_recordings(100)),
        "exports": len(list_exports(100)),
        "presets": list(PRESETS.keys()),
        "dirs": {"recordings": str(REC_DIR), "exports": str(EXPORTS), "assets": str(ASSETS)},
        "agent": "STUDIO",
    }
