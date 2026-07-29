"""Imagine Studio — image / composition product bridge for the POCKET platform.

Product home (not stuffed into desk UI):
  C:\\Users\\Medin\\OneDrive\\imagine-studio\\

Seeds:
  seed-creative-muse/  (from organism-ai creative-muse.zip)

Runtime jobs:
  · still compositions (studio gradient + device glass + content)
  · fusion remake handoff
  · layer-ish edits agents can call via API
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit

HOME = Path.home() / ".pocket" / "imagine"
EXPORTS = HOME / "exports"
COMPOSITES = HOME / "composites"
for d in (HOME, EXPORTS, COMPOSITES):
    d.mkdir(parents=True, exist_ok=True)

PRODUCT_DIR = Path.home() / "OneDrive" / "imagine-studio"
RESEARCH_DIR = (
    Path.home()
    / "OneDrive"
    / "Documents"
    / "POCKET_Research"
    / "ImagineStudio_ViralDemos_FusionRemake"
)


def status() -> Dict[str, Any]:
    seed = PRODUCT_DIR / "seed-creative-muse"
    return {
        "ok": True,
        "product": "Imagine Studio",
        "product_dir": str(PRODUCT_DIR),
        "research_dir": str(RESEARCH_DIR),
        "seed_creative_muse": seed.is_dir(),
        "exports": str(EXPORTS),
        "composites": str(COMPOSITES),
        "api": {
            "status": "GET /v1/imagine",
            "compose": "POST /v1/imagine/compose",
            "remake": "POST /v1/fusion/remake",
            "studio_render": "POST /v1/studio/render",
        },
        "note": "Full image studio product — use API + product folder; not desk UI clutter.",
    }


def _gradient(size: Tuple[int, int], colors=None):
    from PIL import Image

    w, h = size
    colors = colors or [(15, 12, 41), (48, 43, 99), (36, 36, 62)]
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
            # subtle horizontal vignette
            vx = 1.0 - abs(x / w - 0.5) * 0.35
            px[x, y] = (int(r * vx), int(g * vx), int(b * vx))
    return img


def _fit_contain(src, box_w: int, box_h: int, fill=(8, 8, 12)):
    """Letterbox content into box — never stretch to destroy UI."""
    from PIL import Image

    src = src.convert("RGB")
    sw, sh = src.size
    scale = min(box_w / sw, box_h / sh)
    nw, nh = max(1, int(sw * scale)), max(1, int(sh * scale))
    resized = src.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGB", (box_w, box_h), fill)
    canvas.paste(resized, ((box_w - nw) // 2, (box_h - nh) // 2))
    return canvas


def _draw_phone_chassis(draw, x0, y0, x1, y1, *, radius=48):
    # body
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=(18, 18, 22), outline=(70, 70, 78), width=3)
    # inner rim
    draw.rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], radius=radius - 6, outline=(40, 40, 48), width=2)
    # dynamic island
    iw = int((x1 - x0) * 0.28)
    ih = 22
    ix = (x0 + x1 - iw) // 2
    draw.rounded_rectangle([ix, y0 + 14, ix + iw, y0 + 14 + ih], radius=12, fill=(5, 5, 8))
    # home bar
    bw = int((x1 - x0) * 0.28)
    draw.rounded_rectangle(
        [(x0 + x1 - bw) // 2, y1 - 22, (x0 + x1 + bw) // 2, y1 - 14],
        radius=4,
        fill=(220, 220, 230),
    )


def compose_device_still(
    image_path: Optional[str] = None,
    *,
    mode: str = "rotato_phone",
    title: str = "POCKET",
    subtitle: str = "Host co-pilot",
    width: int = 1080,
    height: int = 1920,
) -> Dict[str, Any]:
    """Compose a Rotato-style still: studio bg + real letterboxed screen + chassis."""
    from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

    emit("imagine", f"compose {mode}", agent="STUDIO", role="python")
    t0 = time.time()

    # source image: path or live capture
    if image_path and Path(image_path).is_file():
        content = Image.open(image_path).convert("RGB")
    else:
        from pocket.pixel_translator import _capture_pil

        content = _capture_pil(max_width=1600)

    bg = _gradient((width, height))
    draw = ImageDraw.Draw(bg)

    # soft floor glow
    glow = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    if mode in ("rotato_phone", "phone"):
        # phone glass region (portrait device floating)
        margin_x = int(width * 0.14)
        margin_y = int(height * 0.10)
        px0, py0 = margin_x, margin_y
        px1, py1 = width - margin_x, height - margin_y
        # shadow ellipse under device
        gd.ellipse([px0 + 40, py1 - 40, px1 - 40, py1 + 50], fill=(0, 0, 0, 110))
        glow = glow.filter(ImageFilter.GaussianBlur(28))
        bg = Image.alpha_composite(bg.convert("RGBA"), glow).convert("RGB")
        draw = ImageDraw.Draw(bg)

        # chassis + screen inset
        _draw_phone_chassis(draw, px0, py0, px1, py1, radius=56)
        inset = 18
        sx0, sy0 = px0 + inset, py0 + 42
        sx1, sy1 = px1 - inset, py1 - 36
        sw, sh = sx1 - sx0, sy1 - sy0
        screen = _fit_contain(content, sw, sh, fill=(10, 10, 14))
        bg.paste(screen, (sx0, sy0))

        # glass highlight
        hi = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        hd = ImageDraw.Draw(hi)
        hd.polygon(
            [(sx0, sy0), (sx0 + int(sw * 0.35), sy0), (sx0, sy0 + int(sh * 0.55))],
            fill=(255, 255, 255, 28),
        )
        bg = Image.alpha_composite(bg.convert("RGBA"), hi).convert("RGB")
        draw = ImageDraw.Draw(bg)

    elif mode in ("macbook_web", "web"):
        # laptop body
        lx0, ly0 = int(width * 0.06), int(height * 0.12)
        lx1, ly1 = int(width * 0.94), int(height * 0.78)
        gd.ellipse([lx0 + 80, ly1 - 10, lx1 - 80, ly1 + 70], fill=(0, 0, 0, 100))
        glow = glow.filter(ImageFilter.GaussianBlur(24))
        bg = Image.alpha_composite(bg.convert("RGBA"), glow).convert("RGB")
        draw = ImageDraw.Draw(bg)
        draw.rounded_rectangle([lx0, ly0, lx1, ly1], radius=18, fill=(28, 28, 32), outline=(80, 80, 88), width=3)
        # screen
        sx0, sy0 = lx0 + 16, ly0 + 16
        sx1, sy1 = lx1 - 16, ly1 - 40
        # browser chrome bar
        draw.rectangle([sx0, sy0, sx1, sy0 + 36], fill=(40, 40, 46))
        for i, col in enumerate([(255, 95, 87), (254, 188, 46), (40, 200, 64)]):
            draw.ellipse([sx0 + 12 + i * 18, sy0 + 12, sx0 + 22 + i * 18, sy0 + 22], fill=col)
        sw, sh = sx1 - sx0, sy1 - (sy0 + 36)
        screen = _fit_contain(content, sw, sh, fill=(20, 20, 24))
        bg.paste(screen, (sx0, sy0 + 36))
        # base
        draw.rounded_rectangle([lx0 - 20, ly1, lx1 + 20, ly1 + 28], radius=6, fill=(50, 50, 56))

    else:
        # clean still: content letterboxed on gradient
        pad = 48
        screen = _fit_contain(content, width - pad * 2, height - pad * 2)
        bg.paste(screen, (pad, pad))

    # titles
    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\segoeuib.ttf", 42)
        font_s = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
        font_s = font
    draw = ImageDraw.Draw(bg)
    draw.text((48, height - 100), title[:40], fill=(255, 255, 255), font=font)
    draw.text((48, height - 52), subtitle[:60], fill=(52, 211, 153), font=font_s)

    out = COMPOSITES / f"compose_{mode}_{uuid.uuid4().hex[:8]}.png"
    bg.save(out, "PNG", optimize=True)

    return {
        "ok": True,
        "product": "Imagine Studio",
        "mode": mode,
        "path": str(out),
        "name": out.name,
        "size": [width, height],
        "ms": int((time.time() - t0) * 1000),
        "message": f"Compose {mode}: {out.name}",
        "api": {"compose": "POST /v1/imagine/compose", "studio": "POST /v1/studio/render"},
    }


def compose(
    *,
    mode: str = "rotato_phone",
    image: str = "",
    title: str = "POCKET",
    subtitle: str = "Host co-pilot",
    width: int = 0,
    height: int = 0,
) -> Dict[str, Any]:
    mode = (mode or "rotato_phone").lower()
    if mode in ("rotato_phone", "phone", "viral_phone"):
        w, h = width or 1080, height or 1920
        return compose_device_still(image or None, mode="rotato_phone", title=title, subtitle=subtitle, width=w, height=h)
    if mode in ("macbook_web", "web", "viral_web"):
        w, h = width or 1920, height or 1080
        return compose_device_still(image or None, mode="macbook_web", title=title, subtitle=subtitle, width=w, height=h)
    w, h = width or 1920, height or 1080
    return compose_device_still(image or None, mode="clean", title=title, subtitle=subtitle, width=w, height=h)
