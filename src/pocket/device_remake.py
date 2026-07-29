"""Product-native device demos — lifelike phone/web, NOT desktop-in-a-bezel.

Industry truth (Rotato / App Store / X demos):
  · Content is *designed for* the device frame (app screens / screenshots)
  · Screen recording of a whole desktop is for work capture — not the viral glass
  · Pipeline: capture product surface → remake layout for phone or web → sit in lifelike chrome

This module:
  1) Pulls frames from a SPECULUM recording (or live capture)
  2) Remakes each frame as a *mobile app surface* (or web product surface)
  3) Composites into a photoreal-ish iPhone / browser stage
  4) Emits stills + optional MP4 via ffmpeg
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "studio"
EXPORTS = ROOT / "exports"
ASSETS = ROOT / "assets"
REMAKE = ROOT / "device_remake"
for d in (EXPORTS, ASSETS, REMAKE):
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


def _extract_frames(video: Path, *, n: int = 12, max_seconds: float = 20) -> List[Path]:
    ff = _ffmpeg()
    if not ff or not video.is_file():
        return []
    out_dir = REMAKE / f"frames_{uuid.uuid4().hex[:8]}"
    out_dir.mkdir(parents=True, exist_ok=True)
    # sample ~n frames across first max_seconds
    fps = max(0.3, min(2.0, n / max(1.0, max_seconds)))
    pattern = str(out_dir / "f_%03d.png")
    cmd = [
        ff, "-y", "-t", str(max_seconds), "-i", str(video),
        "-vf", f"fps={fps}", "-frames:v", str(n), pattern,
    ]
    try:
        subprocess.run(cmd, capture_output=True, timeout=120)
    except Exception:
        return []
    return sorted(out_dir.glob("f_*.png"))


def remake_mobile_surface(img, *, title: str = "POCKET", w: int = 390, h: int = 844):
    """Reframe any capture as a *native app* surface (what viral demos actually show)."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

    img = img.convert("RGB")
    # Focus: center-weighted crop to phone aspect (product UI often center-left on desktop)
    tw, th = w, h - 100  # content under status + above home chrome
    src = ImageOps.fit(img, (tw, th), method=Image.Resampling.LANCZOS, centering=(0.5, 0.42))

    canvas = Image.new("RGB", (w, h), (10, 10, 14))
    draw = ImageDraw.Draw(canvas)
    # status bar
    draw.rectangle([0, 0, w, 54], fill=(12, 12, 16))
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 15)
        font_s = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 12)
    except Exception:
        font = ImageFont.load_default()
        font_s = font
    draw.text((20, 18), time.strftime("%H:%M"), fill=(255, 255, 255), font=font)
    draw.text((w - 90, 18), "5G  ■■■", fill=(200, 200, 210), font=font_s)
    # app header
    draw.rectangle([0, 54, w, 100], fill=(18, 18, 24))
    draw.text((16, 68), (title or "App")[:28], fill=(255, 255, 255), font=font)
    # content
    canvas.paste(src, (0, 100))
    # soft vignette bottom for depth
    return canvas


def _lifelike_iphone_stage(
    surface,
    *,
    out_w: int = 1080,
    out_h: int = 1920,
    title: str = "POCKET",
    caption: str = "",
) -> "Image.Image":
    """Photoreal-leaning iPhone stage: studio light, titanium frame, glass, shadow."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont

    # Studio background
    bg = Image.new("RGB", (out_w, out_h), (12, 10, 28))
    px = bg.load()
    for y in range(out_h):
        t = y / max(1, out_h - 1)
        r = int(12 + 40 * t)
        g = int(10 + 25 * (1 - abs(t - 0.4)))
        b = int(28 + 50 * (1 - t))
        for x in range(out_w):
            v = 1.0 - abs(x / out_w - 0.5) * 0.35
            px[x, y] = (int(r * v), int(g * v), int(b * v))

    # Device geometry (centered)
    dw, dh = 560, 1140
    dx = (out_w - dw) // 2
    dy = (out_h - dh) // 2 - 20

    # Shadow
    shadow = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([dx + 40, dy + dh - 30, dx + dw - 40, dy + dh + 70], fill=(0, 0, 0, 140))
    shadow = shadow.filter(ImageFilter.GaussianBlur(36))
    bg = Image.alpha_composite(bg.convert("RGBA"), shadow).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # Titanium outer frame
    draw.rounded_rectangle([dx, dy, dx + dw, dy + dh], radius=78, fill=(48, 48, 52))
    draw.rounded_rectangle([dx + 3, dy + 3, dx + dw - 3, dy + dh - 3], radius=75, fill=(28, 28, 32))
    # Side buttons (volume / power) hints
    draw.rounded_rectangle([dx - 6, dy + 180, dx + 2, dy + 260], radius=3, fill=(60, 60, 64))
    draw.rounded_rectangle([dx - 6, dy + 290, dx + 2, dy + 360], radius=3, fill=(60, 60, 64))
    draw.rounded_rectangle([dx + dw - 2, dy + 240, dx + dw + 6, dy + 340], radius=3, fill=(60, 60, 64))

    # Inner black bezel
    inset = 18
    sx0, sy0 = dx + inset, dy + inset
    sx1, sy1 = dx + dw - inset, dy + dh - inset
    draw.rounded_rectangle([sx0, sy0, sx1, sy1], radius=62, fill=(0, 0, 0))

    # Dynamic Island
    iw = 140
    draw.rounded_rectangle(
        [(dx + dw - iw) // 2, dy + 36, (dx + dw + iw) // 2, dy + 68],
        radius=18,
        fill=(5, 5, 8),
    )

    # Glass content area
    gx0, gy0 = sx0 + 6, sy0 + 8
    gx1, gy1 = sx1 - 6, sy1 - 8
    gw, gh = gx1 - gx0, gy1 - gy0
    phone_surface = surface.resize((gw, gh), Image.Resampling.LANCZOS)
    bg.paste(phone_surface, (gx0, gy0))

    # Specular gloss on glass
    gloss = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(gloss)
    gd.polygon(
        [(gx0, gy0), (gx0 + int(gw * 0.4), gy0), (gx0, gy0 + int(gh * 0.55))],
        fill=(255, 255, 255, 22),
    )
    bg = Image.alpha_composite(bg.convert("RGBA"), gloss).convert("RGB")
    draw = ImageDraw.Draw(bg)

    # Home indicator
    bw = 140
    draw.rounded_rectangle(
        [(out_w - bw) // 2, dy + dh - 36, (out_w + bw) // 2, dy + dh - 24],
        radius=4,
        fill=(230, 230, 240),
    )

    # Captions outside device (marketing)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 42)
        font_s = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
        font_s = font
    draw.text((48, out_h - 110), (title or "POCKET")[:36], fill=(255, 255, 255), font=font)
    if caption:
        draw.text((48, out_h - 58), caption[:50], fill=(52, 211, 153), font=font_s)

    return bg


def remake_web_surface(img, *, title: str = "POCKET", brand: str = "app.local"):
    """Product web surface — browser content as if it were the product site, not raw desktop."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps

    W, H = 1600, 1000
    img = img.convert("RGB")
    content = ImageOps.fit(img, (W, H - 48), method=Image.Resampling.LANCZOS, centering=(0.5, 0.4))
    canvas = Image.new("RGB", (W, H), (24, 24, 28))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle([0, 0, W, 48], fill=(40, 40, 46))
    for i, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
        draw.ellipse([14 + i * 20, 16, 26 + i * 20, 28], fill=col)
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    draw.rounded_rectangle([100, 10, W - 40, 38], radius=8, fill=(55, 55, 62))
    draw.text((112, 14), f"{brand}  ·  {title}"[:60], fill=(220, 220, 230), font=font)
    canvas.paste(content, (0, 48))
    return canvas


def product_phone_from_image(
    image_path: Optional[str] = None,
    *,
    title: str = "POCKET",
    caption: str = "Host co-pilot",
) -> Dict[str, Any]:
    """Single still: live or file → mobile remake → lifelike iPhone stage."""
    from PIL import Image
    from pocket.pixel_translator import _capture_pil

    t0 = time.time()
    if image_path and Path(image_path).is_file():
        raw = Image.open(image_path).convert("RGB")
    else:
        raw = _capture_pil(max_width=1400)
    mobile = remake_mobile_surface(raw, title=title)
    stage = _lifelike_iphone_stage(mobile, title=title, caption=caption)
    out = EXPORTS / f"product_phone_{uuid.uuid4().hex[:8]}.png"
    stage.save(out, "PNG", optimize=True)
    return {
        "ok": True,
        "kind": "product_phone_still",
        "path": str(out),
        "name": out.name,
        "ms": int((time.time() - t0) * 1000),
        "message": "Lifelike iPhone product still (mobile remake, not desktop crop)",
    }


def product_phone_from_recording(
    source: str,
    *,
    title: str = "POCKET",
    caption: str = "Product demo",
    max_seconds: float = 12,
    n_frames: int = 10,
) -> Dict[str, Any]:
    """
    Viral phone video the right way:
    recording frames → each remade as mobile app UI → lifelike iPhone stage → MP4.
    """
    ff = _ffmpeg()
    if not ff:
        return {"ok": False, "error": "ffmpeg not found"}
    src = Path(source)
    if not src.is_file():
        cand = Path.home() / ".pocket" / "recordings" / source
        if cand.is_file():
            src = cand
        else:
            return {"ok": False, "error": f"recording not found: {source}"}

    emit("studio", f"Product phone remake ← {src.name}", agent="STUDIO", role="python")
    t0 = time.time()
    frames = _extract_frames(src, n=n_frames, max_seconds=max_seconds)
    if not frames:
        # fallback single still from first second
        still = product_phone_from_image(None, title=title, caption=caption)
        return {**still, "ok": still.get("ok"), "note": "frame extract failed; still only"}

    from PIL import Image

    staged_dir = REMAKE / f"staged_{uuid.uuid4().hex[:8]}"
    staged_dir.mkdir(parents=True, exist_ok=True)
    staged_paths = []
    for i, fp in enumerate(frames):
        raw = Image.open(fp).convert("RGB")
        mobile = remake_mobile_surface(raw, title=title)
        stage = _lifelike_iphone_stage(mobile, title=title, caption=caption if i == 0 else "")
        op = staged_dir / f"s_{i:03d}.png"
        stage.save(op, "PNG")
        staged_paths.append(op)

    out = EXPORTS / f"{src.stem}__product_phone__{int(time.time())}.mp4"
    # 8 fps slideshow of product frames
    pattern = str(staged_dir / "s_%03d.png")
    cmd = [
        ff, "-y", "-framerate", "8", "-i", pattern,
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18",
        "-movflags", "+faststart", str(out),
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    ok = r.returncode == 0 and out.exists() and out.stat().st_size > 1000
    return {
        "ok": ok,
        "kind": "product_phone_video",
        "source": str(src),
        "output": str(out) if ok else "",
        "name": out.name if ok else "",
        "frames": len(staged_paths),
        "ms": int((time.time() - t0) * 1000),
        "error": None if ok else (r.stderr or "")[-800:],
        "message": "Product phone demo: mobile remake inside lifelike iPhone (not raw desktop bezel)",
        "method": "frame→mobile_surface→iphone_stage→mp4",
    }


def product_web_from_image(
    image_path: Optional[str] = None,
    *,
    title: str = "POCKET",
    brand: str = "pocket.local",
) -> Dict[str, Any]:
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    from pocket.pixel_translator import _capture_pil

    t0 = time.time()
    if image_path and Path(image_path).is_file():
        raw = Image.open(image_path).convert("RGB")
    else:
        raw = _capture_pil(max_width=1600)
    web = remake_web_surface(raw, title=title, brand=brand)
    # stage on dark marketing canvas 1920x1080
    W, H = 1920, 1080
    bg = Image.new("RGB", (W, H), (14, 12, 30))
    # scale web surface
    scale = min((W - 160) / web.width, (H - 160) / web.height)
    nw, nh = int(web.width * scale), int(web.height * scale)
    web_r = web.resize((nw, nh), Image.Resampling.LANCZOS)
    x0, y0 = (W - nw) // 2, (H - nh) // 2 - 10
    # shadow
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle([x0 + 20, y0 + nh - 10, x0 + nw - 20, y0 + nh + 40], radius=20, fill=(0, 0, 0, 120))
    sh = sh.filter(ImageFilter.GaussianBlur(20))
    bg = Image.alpha_composite(bg.convert("RGBA"), sh).convert("RGB")
    bg.paste(web_r, (x0, y0))
    out = EXPORTS / f"product_web_{uuid.uuid4().hex[:8]}.png"
    bg.save(out, "PNG", optimize=True)
    return {
        "ok": True,
        "kind": "product_web_still",
        "path": str(out),
        "name": out.name,
        "ms": int((time.time() - t0) * 1000),
        "message": "Product web still (browser surface remake, not raw desktop)",
    }
