"""Copy electron-builder artifacts into releases/desktop for the web download surface."""

from __future__ import annotations

import platform
import shutil
from pathlib import Path
from typing import Any, Dict, List

from pocket.desktop_releases import ensure_releases_dir, list_artifacts, write_manifest

ROOT = Path(__file__).resolve().parents[2]
ELECTRON_DIST = ROOT / "desktop-electron" / "dist"


def _host_arch_token() -> str:
    m = (platform.machine() or "").lower()
    if m in ("arm64", "aarch64"):
        return "arm64"
    if m in ("amd64", "x86_64", "x64"):
        return "x64"
    return "unknown"


def pack_releases(*, source: Path | None = None) -> Dict[str, Any]:
    """
    Scan desktop-electron/dist for .exe/.msi/.zip and copy into releases/desktop
    with stable names including arch when possible.
    """
    src = source or ELECTRON_DIST
    dest = ensure_releases_dir()
    copied: List[Dict[str, str]] = []
    missing = not src.is_dir()

    if not missing:
        # Only top-level dist artifacts (portable/NSIS), never unpacked trees
        candidates: List[Path] = []
        for fp in sorted(src.iterdir()) if src.is_dir() else []:
            if fp.is_file() and fp.suffix.lower() in {".exe", ".msi", ".zip"}:
                candidates.append(fp)
        # Also allow one-level nested builders (e.g. dist/nsis/*.exe) but skip *unpacked*
        for fp in sorted(src.rglob("*")):
            if not fp.is_file():
                continue
            if fp.suffix.lower() not in {".exe", ".msi", ".zip"}:
                continue
            parts_l = [p.lower() for p in fp.parts]
            if any("unpacked" in p for p in parts_l):
                continue
            if fp.name.lower() in {"electron.exe", "elevate.exe", "squirrel.exe"}:
                continue
            if fp not in candidates:
                candidates.append(fp)

        for fp in candidates:
            parts_l = [p.lower() for p in fp.parts]
            if any("unpacked" in p for p in parts_l):
                continue
            if fp.name.lower() in {"electron.exe", "elevate.exe", "squirrel.exe"}:
                continue
            name = fp.name
            # Prefer builder names; if no arch token, append host arch for portable
            lower = name.lower()
            if lower.endswith(".exe") and "arm64" not in lower and "x64" not in lower and "ia32" not in lower:
                stem = fp.stem
                arch = _host_arch_token()
                if arch != "unknown" and arch not in stem.lower():
                    name = f"{stem}-{arch}{fp.suffix}"
            target = dest / name
            shutil.copy2(fp, target)
            copied.append({"from": str(fp), "to": str(target), "bytes": str(target.stat().st_size)})

    manifest = write_manifest()
    arts = list_artifacts()
    return {
        "ok": bool(arts),
        "source": str(src),
        "source_exists": src.is_dir(),
        "dest": str(dest),
        "copied": copied,
        "artifacts": arts,
        "manifest": str(manifest),
        "hint": None
        if arts
        else "No packages found. Run: cd desktop-electron && npm.cmd run dist",
        "download_page": "/download",
        "download_windows": "/download/desktop",
    }
