"""Workspace file / zip uploads for POCKET desk."""

from __future__ import annotations

import base64
import re
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from pocket.executor import resolve_cwd
from pocket.tokenomics import burn

MAX_BYTES = 25 * 1024 * 1024  # 25MB
SAFE_NAME = re.compile(r"^[\w.\- ()\[\]]+$")


def upload_file(
    *,
    workspace: str = "workspace",
    filename: str = "",
    content_base64: str = "",
    size: int = 0,
) -> Dict[str, Any]:
    name = (filename or "upload.bin").replace("\\", "/").split("/")[-1].strip()
    if not name or not SAFE_NAME.match(name) or ".." in name:
        return {"ok": False, "error": "invalid filename"}
    if size and size > MAX_BYTES:
        return {"ok": False, "error": f"file too large (max {MAX_BYTES} bytes)"}

    try:
        raw = base64.b64decode(content_base64 or "", validate=False)
    except Exception:
        return {"ok": False, "error": "bad base64"}
    if len(raw) > MAX_BYTES:
        return {"ok": False, "error": f"file too large (max {MAX_BYTES} bytes)"}

    root = Path(resolve_cwd({"workspace": workspace, "cwd": ""}))
    up = root / "uploads"
    up.mkdir(parents=True, exist_ok=True)
    dest = up / name
    dest.write_bytes(raw)

    extracted = []
    if name.lower().endswith(".zip"):
        try:
            with zipfile.ZipFile(BytesIO(raw)) as zf:
                for info in zf.infolist():
                    # zip-slip guard
                    target = (up / info.filename).resolve()
                    if not str(target).startswith(str(up.resolve())):
                        continue
                    if info.is_dir():
                        target.mkdir(parents=True, exist_ok=True)
                    else:
                        target.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(info) as src, open(target, "wb") as out:
                            out.write(src.read())
                        extracted.append(str(target.relative_to(root)).replace("\\", "/"))
        except zipfile.BadZipFile:
            return {
                "ok": True,
                "path": str(dest.relative_to(root)).replace("\\", "/"),
                "bytes": len(raw),
                "warning": "saved zip but could not extract",
                "workspace": workspace,
            }

    burn("job_shell", meta={"upload": name, "bytes": len(raw)})  # small meter
    return {
        "ok": True,
        "workspace": workspace,
        "path": str(dest.relative_to(root)).replace("\\", "/"),
        "bytes": len(raw),
        "extracted": extracted[:50],
        "extract_count": len(extracted),
    }
