"""POCKET Desktop Electron releases — catalog + file paths for web download.

Artifacts live under repo `releases/desktop/` (copied from electron-builder output).
The web edge app serves these so users can download a Windows .exe installer/portable
shell that attaches to the local host (or starts it).
"""

from __future__ import annotations

import json
import os
import platform
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket import __version__, LAB, PRODUCT

# pocket-os/releases/desktop
ROOT = Path(__file__).resolve().parents[2]
RELEASES_DIR = ROOT / "releases" / "desktop"
MANIFEST_NAME = "manifest.json"


def releases_dir() -> Path:
    custom = (os.environ.get("POCKET_RELEASES_DIR") or "").strip()
    if custom:
        return Path(custom)
    return RELEASES_DIR


def ensure_releases_dir() -> Path:
    d = releases_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _file_meta(fp: Path) -> Dict[str, Any]:
    st = fp.stat()
    return {
        "name": fp.name,
        "size": st.st_size,
        "size_mb": round(st.st_size / (1024 * 1024), 2),
        "mtime": st.st_mtime,
        "mtime_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(st.st_mtime)),
        "url": f"/download/files/{fp.name}",
        "download_url": f"/download/files/{fp.name}",
    }


def _kind_for_name(name: str) -> str:
    n = name.lower()
    if n.endswith(".exe") and ("setup" in n or "install" in n):
        return "nsis"
    if n.endswith(".exe"):
        return "portable"
    if n.endswith(".msi"):
        return "msi"
    if n.endswith(".zip"):
        return "zip"
    return "other"


def _arch_for_name(name: str) -> str:
    n = name.lower()
    if "arm64" in n or "aarch64" in n:
        return "arm64"
    if "x64" in n or "x86_64" in n or "amd64" in n:
        return "x64"
    if "ia32" in n or "x86" in n:
        return "ia32"
    return "unknown"


def list_artifacts() -> List[Dict[str, Any]]:
    d = releases_dir()
    if not d.is_dir():
        return []
    out: List[Dict[str, Any]] = []
    for fp in sorted(d.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
        if not fp.is_file():
            continue
        if fp.name.startswith(".") or fp.name == MANIFEST_NAME:
            continue
        if fp.suffix.lower() not in {".exe", ".msi", ".zip", ".7z"}:
            continue
        meta = _file_meta(fp)
        meta["kind"] = _kind_for_name(fp.name)
        meta["arch"] = _arch_for_name(fp.name)
        meta["platform"] = "win32"
        out.append(meta)
    return out


def preferred_artifact(*, arch: Optional[str] = None, kind: str = "portable") -> Optional[Dict[str, Any]]:
    """Pick best Windows download for this host or requested arch."""
    arts = list_artifacts()
    if not arts:
        return None
    want_arch = (arch or "").lower() or _host_arch()
    # Prefer: matching arch + kind, then matching arch any, then any portable, then any
    def score(a: Dict[str, Any]) -> tuple:
        arch_ok = 2 if a.get("arch") == want_arch else (1 if a.get("arch") == "unknown" else 0)
        kind_ok = 2 if a.get("kind") == kind else (1 if a.get("kind") == "portable" else 0)
        return (arch_ok, kind_ok, a.get("mtime") or 0)

    ranked = sorted(arts, key=score, reverse=True)
    return ranked[0] if ranked else None


def _host_arch() -> str:
    m = (platform.machine() or "").lower()
    if m in ("arm64", "aarch64"):
        return "arm64"
    if m in ("amd64", "x86_64", "x64"):
        return "x64"
    return "unknown"


def resolve_file(name: str) -> Optional[Path]:
    """Safe resolve under releases dir (basename only)."""
    safe = Path(name).name
    if not safe or safe in (".", "..") or ".." in safe:
        return None
    d = releases_dir()
    fp = (d / safe).resolve()
    try:
        if not str(fp).startswith(str(d.resolve())):
            return None
    except Exception:
        return None
    if fp.is_file():
        return fp
    return None


def catalog() -> Dict[str, Any]:
    arts = list_artifacts()
    pref = preferred_artifact()
    return {
        "ok": True,
        "product": PRODUCT,
        "lab": LAB,
        "version": __version__,
        "channel": "desktop-electron",
        "app_id": "com.medinatech.pocket",
        "product_name": "POCKET",
        "releases_dir": str(releases_dir()),
        "host_arch": _host_arch(),
        "artifacts": arts,
        "recommended": pref,
        "download": {
            "page": "/download",
            "windows": "/download/desktop",
            "windows_portable": "/download/desktop?kind=portable",
            "windows_installer": "/download/desktop?kind=nsis",
            "api": "/v1/desktop/releases",
        },
        "notes": [
            "Electron shell wraps the stable web edge desk (same UI as /desk).",
            "Requires the POCKET host runtime on the machine (auto-starts if python -m pocket is available).",
            "Prefer portable .exe for one-file trial; NSIS installer for Start Menu + shortcuts.",
        ],
        "stable_surface": {
            "web": "http://127.0.0.1:8787/desk",
            "public_hint": "https://pocket.medinatechlabs.net/desk",
            "why": "Web edge desk is the most stable surface; Electron packages that same UI as a downloadable .exe",
        },
    }


def write_manifest() -> Path:
    """Refresh releases/desktop/manifest.json from on-disk artifacts."""
    d = ensure_releases_dir()
    cat = catalog()
    path = d / MANIFEST_NAME
    path.write_text(json.dumps(cat, indent=2), encoding="utf-8")
    return path


def download_page_html() -> str:
    from pocket.product_shell import SHELL_CSS, shell_nav

    cat = catalog()
    arts = cat.get("artifacts") or []
    pref = cat.get("recommended") or {}
    rows = ""
    for a in arts:
        rows += (
            f'<tr><td>{a.get("name")}</td><td>{a.get("kind")}</td>'
            f'<td>{a.get("arch")}</td><td>{a.get("size_mb")} MB</td>'
            f'<td><a class="btn btn-primary" href="{a.get("url")}">Download</a></td></tr>'
        )
    if not rows:
        rows = (
            '<tr><td colspan="5" class="empty">No packaged .exe yet. '
            "On the host run: <code>cd desktop-electron && npm run dist</code> "
            "then <code>python -m pocket desktop-pack</code></td></tr>"
        )
    pref_btn = ""
    if pref.get("url"):
        pref_btn = (
            f'<a class="btn btn-primary" href="{pref["url"]}">'
            f'Download recommended ({pref.get("name", "Windows")})</a>'
        )
    else:
        pref_btn = (
            '<a class="btn btn-primary" href="/download/desktop">Download Windows app</a>'
        )

    nav = shell_nav(active="download")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Download POCKET Desktop — Windows .exe</title>
<meta name="description" content="Download the POCKET Electron desktop shell for Windows. Same stable web desk, packaged as .exe."/>
<meta name="theme-color" content="#09090b"/>
<style>
:root{{--bg:#09090b;--panel:#141416;--line:rgba(255,255,255,.1);--text:#e4e4e7;--muted:#a1a1aa;--fg:#fafafa;--accent:#10a37f;--accent2:#0d8c6c}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);line-height:1.55;-webkit-font-smoothing:antialiased}}
a{{color:inherit;text-decoration:none}}
{SHELL_CSS}
.wrap{{max-width:920px;margin:0 auto;padding:48px 22px 80px}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:12px}}
h1{{font-size:clamp(28px,4vw,40px);letter-spacing:-.04em;margin:0 0 12px;color:var(--fg)}}
.lead{{color:var(--muted);max-width:560px;margin:0 0 24px;font-size:16px}}
.cta-row{{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:28px}}
.btn{{display:inline-flex;align-items:center;padding:12px 18px;border-radius:10px;font-weight:700;font-size:14px;border:1px solid transparent}}
.btn-primary{{background:var(--accent);color:#041}}
.btn-primary:hover{{background:var(--accent2)}}
.btn-ghost{{border-color:var(--line);color:var(--fg)}}
.btn-ghost:hover{{background:rgba(255,255,255,.06)}}
.card{{border:1px solid var(--line);border-radius:16px;padding:22px;background:var(--panel);margin-bottom:20px}}
.card h2{{margin:0 0 8px;font-size:18px;color:var(--fg)}}
.card p{{margin:0 0 10px;color:var(--muted);font-size:14px}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}
th,td{{text-align:left;padding:10px 8px;border-bottom:1px solid var(--line)}}
th{{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}
.empty{{color:var(--muted);font-size:13px}}
code{{color:var(--accent);font-size:12px}}
.note{{font-size:13px;color:var(--muted);margin-top:18px}}
.pill{{display:inline-block;font-size:11px;border:1px solid var(--line);padding:4px 10px;border-radius:999px;color:var(--muted);margin-right:6px}}
</style>
</head>
<body>
{nav}
<main class="wrap">
  <div class="eyebrow">Desktop package · Windows</div>
  <h1>Download POCKET Desktop</h1>
  <p class="lead">Get the Electron .exe shell. It opens the same stable web edge desk you already use — as a real Windows app with shortcuts and a proper window.</p>
  <div class="cta-row">
    {pref_btn}
    <a class="btn btn-ghost" href="/desk">Open web desk (stable)</a>
    <a class="btn btn-ghost" href="/v1/desktop/releases">JSON catalog</a>
  </div>
  <div class="card">
    <h2>What you get</h2>
    <p>Portable or installer builds of <strong>POCKET</strong> (app id <code>com.medinatech.pocket</code>). The shell loads <code>/desk</code> on the local host and can start the runtime if Python + POCKET are installed.</p>
    <span class="pill">v{__version__}</span>
    <span class="pill">host arch: {cat.get("host_arch")}</span>
    <span class="pill">channel: desktop-electron</span>
  </div>
  <div class="card">
    <h2>Available packages</h2>
    <table>
      <thead><tr><th>File</th><th>Kind</th><th>Arch</th><th>Size</th><th></th></tr></thead>
      <tbody>{rows}</tbody>
    </table>
    <p class="note">Tip: on ARM Windows prefer <em>arm64</em> portable. On Intel/AMD prefer <em>x64</em>.</p>
  </div>
</main>
</body>
</html>
"""
