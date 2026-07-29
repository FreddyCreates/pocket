"""Recursive Fusion Engine (RFE-v1) — production kernel.

Implements the research journal architecture:
  Ingestion → Vector normalization → Spatial mapping → Materialization
  Outputs: fusion_packet (signed), HTML5, scene3d, GLSL fragment

Gold standard path: sense (200–900 symbols) → FULL_SYNTHESIS.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import secrets
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "rfe"
PACKETS = ROOT / "packets"
OUT = ROOT / "materialized"
KEY_PATH = ROOT / "rfe_hmac.key"
for d in (ROOT, PACKETS, OUT):
    d.mkdir(parents=True, exist_ok=True)

SCHEMA = "pocket.rfe.fusion_packet.v1"


def _hmac_key() -> bytes:
    if KEY_PATH.exists():
        return KEY_PATH.read_bytes()
    k = secrets.token_bytes(32)
    KEY_PATH.write_bytes(k)
    try:
        KEY_PATH.chmod(0o600)
    except Exception:
        pass
    return k


def _canonical(obj: Dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def sign_packet(body: Dict[str, Any]) -> Dict[str, Any]:
    """HMAC-SHA256 integrity for multi-hour mission packet continuity."""
    # sign without nested signature field
    payload = {k: v for k, v in body.items() if k != "signature"}
    digest = hmac.new(_hmac_key(), _canonical(payload), hashlib.sha256).hexdigest()
    body["signature"] = {
        "alg": "HMAC-SHA256",
        "entropy_sources": ["time_ns", "symbol_density", "page_hint", "primary_modality"],
        "hmac": digest,
        "at": time.time(),
    }
    return body


def verify_packet(packet: Dict[str, Any]) -> bool:
    body = packet.get("fusion_packet") or packet
    sig = body.get("signature") or {}
    expected = sig.get("hmac")
    if not expected:
        return False
    payload = {k: v for k, v in body.items() if k != "signature"}
    digest = hmac.new(_hmac_key(), _canonical(payload), hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, expected)


def _centroid(nodes: List[Dict[str, Any]], size: List[int]) -> Dict[str, float]:
    pts = []
    for n in nodes:
        b = n.get("bbox")
        c = n.get("click")
        if c and c.get("x") is not None:
            pts.append((float(c["x"]), float(c["y"])))
        elif isinstance(b, list) and len(b) >= 2:
            pts.append((float(b[0]), float(b[1])))
    if not pts:
        w, h = size[0] if size else 1920, size[1] if len(size) > 1 else 1080
        return {"x": w / 2, "y": h / 2, "z": 0.0}
    sx = sum(p[0] for p in pts) / len(pts)
    sy = sum(p[1] for p in pts) / len(pts)
    return {"x": round(sx, 2), "y": round(sy, 2), "z": 0.0}


def _source_entropy(page: Dict[str, Any], density: int) -> float:
    """Lower entropy when structure is rich (UIA heavy); higher when sparse."""
    counts = page.get("counts") or {}
    uia = int(counts.get("uia") or 0)
    ocr = int(counts.get("ocr_lines") or 0)
    if density <= 0:
        return 1.0
    # structured UI → low entropy
    ratio = uia / max(1, density)
    ent = 1.0 - min(0.95, ratio * 0.85 + min(ocr, 50) / 200.0)
    return round(max(0.05, ent), 3)


def _complexity_index(page: Dict[str, Any]) -> float:
    counts = page.get("counts") or {}
    symbols = int(counts.get("symbols") or 0)
    uia = max(1, int(counts.get("uia") or 1))
    interactive = int(counts.get("buttons") or 0) + int(counts.get("links") or 0) + int(counts.get("inputs") or 0)
    interactive_ratio = interactive / uia
    return round(min(1.0, (symbols / 800.0) * max(0.3, min(1.2, interactive_ratio + 0.4))), 3)


def packet_from_page(
    page: Optional[Dict[str, Any]] = None,
    *,
    instruction_set: str = "FULL_SYNTHESIS",
    sign: bool = True,
) -> Dict[str, Any]:
    """Build a fusion_packet from a live or cached page render."""
    if page is None:
        from pocket.perception import sense

        page = sense(max_ui=500, force=False)

    size = page.get("size") or [1920, 1080]
    symbols = page.get("symbols") or []
    density = int((page.get("counts") or {}).get("symbols") or len(symbols))
    nodes_head = []
    for s in symbols[:60]:
        if not (s.get("text") or s.get("bbox")):
            continue
        nodes_head.append(
            {
                "id": s.get("id"),
                "kind": s.get("kind"),
                "source": s.get("source"),
                "text": (s.get("text") or "")[:120],
                "bbox": s.get("bbox"),
                "click": s.get("click"),
            }
        )

    vector = _centroid(nodes_head, size)
    meta = {
        "density": density,
        "source_entropy": _source_entropy(page, density),
        "compression_ratio": "optimal" if density >= 400 else ("high" if density >= 150 else "sparse"),
        "primary_modality": page.get("primary_modality"),
        "page_hint": page.get("page_hint") or "",
        "complexity_index": _complexity_index(page),
        "counts": page.get("counts"),
        "size": size,
    }

    body = {
        "uuid": f"rfe-{uuid.uuid4().hex[:10]}",
        "schema": SCHEMA,
        "vector": vector,
        "instruction_set": instruction_set or "FULL_SYNTHESIS",
        "metadata": meta,
        "nodes_head": nodes_head,
        "action_hints": (page.get("action_hints") or [])[:20],
        "at": time.time(),
        "product": "POCKET RFE-v1",
        "archival_code": "RFE-2023-X1",
    }
    if sign:
        body = sign_packet(body)
    return {"fusion_packet": body, "ok": True}


def glsl_fragment(*, density: int = 400, accent: Optional[Tuple[float, float, float]] = None) -> str:
    acc = accent or (0.1, 0.5, 0.8)
    u_density = min(1.0, density / 800.0)
    return f"""// GLSL Fragment Shader for RFE-v1 Rendering (POCKET-generated)
// archival: RFE-2023-X1 / INL-2026-POCKET.RFE.v1
precision highp float;
varying vec2 vUv;
uniform float uTime;
uniform vec3 uResolution;
uniform float uDensity;
// baked density hint: {u_density:.3f}
// accent rgb: {acc[0]:.2f}, {acc[1]:.2f}, {acc[2]:.2f}

void main() {{
    vec2 st = gl_FragCoord.xy / uResolution.xy;
    float dist = length(st - 0.5);
    float dens = max(uDensity, {u_density:.4f});
    vec3 accent = vec3({acc[0]:.3f}, {acc[1]:.3f}, {acc[2]:.3f});
    // Recursive Fusion Logic: Map distance to color density
    vec3 color = accent * (1.0 - smoothstep(0.0, 0.5 + dens * 0.2, dist));
    gl_FragColor = vec4(color + sin(uTime) * 0.05, 1.0);
}}
"""


def materialize(
    *,
    page: Optional[Dict[str, Any]] = None,
    instruction_set: str = "FULL_SYNTHESIS",
    refresh: bool = False,
    max_ui: int = 500,
) -> Dict[str, Any]:
    """Full RFE pipeline: sense → packet → HTML + scene3d + GLSL."""
    emit("rfe", f"synthesize {instruction_set}", agent="OCULUS", role="python")
    t0 = time.time()
    if page is None:
        from pocket.perception import sense

        page = sense(max_ui=max_ui, force=refresh, grid=5)

    packet_wrap = packet_from_page(page, instruction_set=instruction_set, sign=True)
    packet = packet_wrap["fusion_packet"]
    density = int((packet.get("metadata") or {}).get("density") or 0)
    uid = packet.get("uuid") or f"rfe-{int(time.time())}"

    paths: Dict[str, str] = {}
    html = None
    scene = None
    ir = None
    glsl = None

    instr = (instruction_set or "FULL_SYNTHESIS").upper()
    want_html = instr in ("FULL_SYNTHESIS", "GENERATE_HTML", "GENERATE_3D_SCENE")
    want_scene = instr in ("FULL_SYNTHESIS", "GENERATE_3D_SCENE")
    want_ir = instr in ("FULL_SYNTHESIS", "GENERATE_IR", "GENERATE_HTML", "GENERATE_3D_SCENE")
    want_glsl = want_scene

    if want_ir or want_html or want_scene:
        from pocket.fusion_remake import symbols_to_ir, ir_to_html, ir_to_scene3d

        ir = symbols_to_ir(page, max_nodes=500)
        if want_html:
            html = ir_to_html(ir, styled=True)
            hp = OUT / f"{uid}.html"
            hp.write_text(html, encoding="utf-8")
            paths["html"] = str(hp)
        if want_scene:
            scene = ir_to_scene3d(ir)
            # attach GLSL + packet vector into scene
            scene["rfe"] = {
                "uuid": uid,
                "vector": packet.get("vector"),
                "instruction_set": instr,
                "complexity_index": (packet.get("metadata") or {}).get("complexity_index"),
            }
            if want_glsl:
                glsl = glsl_fragment(density=density)
                scene["glsl_fragment"] = glsl
                gp = OUT / f"{uid}.frag.glsl"
                gp.write_text(glsl, encoding="utf-8")
                paths["glsl"] = str(gp)
            sp = OUT / f"{uid}.scene.json"
            sp.write_text(json.dumps(scene, indent=2, default=str)[:400000], encoding="utf-8")
            paths["scene3d"] = str(sp)
        if ir is not None:
            ip = OUT / f"{uid}.ir.json"
            ip.write_text(json.dumps(ir, indent=2, default=str)[:600000], encoding="utf-8")
            paths["ir"] = str(ip)

    pp = PACKETS / f"{uid}.json"
    pp.write_text(json.dumps(packet_wrap, indent=2, default=str)[:400000], encoding="utf-8")
    paths["packet"] = str(pp)

    out = {
        "ok": True,
        "product": "POCKET Recursive Fusion Engine RFE-v1",
        "archival_code": "RFE-2023-X1",
        "uuid": uid,
        "instruction_set": instr,
        "ms": int((time.time() - t0) * 1000),
        "fusion_packet": packet,
        "signature_valid": verify_packet(packet_wrap),
        "metadata": packet.get("metadata"),
        "paths": paths,
        "gold_standard": density >= 600,
        "brief": (
            f"RFE {instr}: density={density} entropy={(packet.get('metadata') or {}).get('source_entropy')} "
            f"complexity={(packet.get('metadata') or {}).get('complexity_index')} · "
            f"{(packet.get('metadata') or {}).get('page_hint') or 'screen'}"
        ),
        "api": {
            "synthesize": "POST /v1/rfe/synthesize",
            "status": "GET /v1/rfe",
            "verify": "POST /v1/rfe/verify",
            "remake": "POST /v1/fusion/remake",
            "sense": "GET /v1/vision/page",
        },
        "research": str(
            Path.home()
            / "OneDrive"
            / "Documents"
            / "POCKET_Research"
            / "RFE_Recursive_Fusion_Engine"
            / "RFE_v1_Architectural_Synthesis.md"
        ),
    }
    emit("rfe", out["brief"], agent="OCULUS", role="python")
    return out


def status() -> Dict[str, Any]:
    packets = sorted(PACKETS.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    mats = sorted(OUT.glob("*"), key=lambda p: p.stat().st_mtime, reverse=True)
    return {
        "ok": True,
        "product": "POCKET RFE-v1",
        "schema": SCHEMA,
        "archival_code": "RFE-2023-X1",
        "packets": len(list(PACKETS.glob("*.json"))),
        "latest_packet": str(packets[0]) if packets else None,
        "latest_materialized": str(mats[0]) if mats else None,
        "root": str(ROOT),
        "api": {
            "synthesize": "POST /v1/rfe/synthesize",
            "verify": "POST /v1/rfe/verify",
        },
        "gold_standard": "wf1 fusion sense + remake ≥ 600 symbols → HTML + 3D + GLSL",
    }
