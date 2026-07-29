"""Four *real* user tasks — actual work products, not open/move toys.

1) Research pack: web+fusion notes written to Documents
2) Project bootstrap: real folder + README + runnable script in vcomp
3) Inbox triage note: desktop sense → structured markdown task list
4) Product marketing pack: product-phone remake from latest recording + web still
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from pocket.live_events import emit

OUT = Path.home() / ".pocket" / "workflows_real"
DOCS = Path.home() / "OneDrive" / "Documents" / "POCKET_Work"
OUT.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)


def catalog() -> List[Dict[str, Any]]:
    return [
        {
            "id": "real1_research_pack",
            "title": "Research pack to Documents",
            "user_story": "I researched a topic and need a dated markdown brief I can open in Explorer.",
        },
        {
            "id": "real2_project_bootstrap",
            "title": "Bootstrap a real project folder",
            "user_story": "Create a project with README + runnable Python and verify it runs.",
        },
        {
            "id": "real3_desktop_triage",
            "title": "Desktop triage note",
            "user_story": "Sense what's on glass and produce a task list from real buttons/links.",
        },
        {
            "id": "real4_marketing_pack",
            "title": "Product marketing pack",
            "user_story": "Turn latest work recording into lifelike phone + web product stills/video.",
        },
    ]


def run(wid: str, **opts) -> Dict[str, Any]:
    wid = (wid or "").lower().replace("-", "_")
    emit("workflow", f"real {wid}", agent="ARCHON", role="host")
    t0 = time.time()
    fn = {
        "real1_research_pack": _real1,
        "real1": _real1,
        "real2_project_bootstrap": _real2,
        "real2": _real2,
        "real3_desktop_triage": _real3,
        "real3": _real3,
        "real4_marketing_pack": _real4,
        "real4": _real4,
    }.get(wid)
    if not fn:
        return {"ok": False, "error": f"unknown {wid}", "catalog": catalog()}
    try:
        r = fn(**opts)
        r["workflow_id"] = wid
        r["ms"] = int((time.time() - t0) * 1000)
        p = OUT / f"{wid}_{int(time.time())}.json"
        p.write_text(json.dumps(r, indent=2, default=str)[:400000], encoding="utf-8")
        r["log_path"] = str(p)
        return r
    except Exception as e:
        return {"ok": False, "error": str(e), "workflow_id": wid}


def run_all_real() -> Dict[str, Any]:
    results = [run(c["id"]) for c in catalog()]
    ok = sum(1 for r in results if r.get("ok"))
    return {"ok": ok == len(results), "passed": ok, "total": len(results), "results": results}


def _real1(**opts) -> Dict[str, Any]:
    """Research pack: optional URL meta + fusion brief + written file."""
    from pocket.perception import sense
    from pocket.video_watch import youtube_meta, watch

    topic = opts.get("topic") or opts.get("prompt") or "Agentic interface synthesis and host co-pilots"
    url = opts.get("url") or ""
    page = sense(max_ui=350, force=True)
    meta = {}
    if url:
        if "youtube" in url or "youtu.be" in url:
            meta = youtube_meta(url)
        else:
            meta = {"url": url}
    # write real deliverable
    day = time.strftime("%Y-%m-%d")
    path = DOCS / f"Research_Pack_{day}.md"
    body = [
        f"# Research pack — {topic}",
        f"",
        f"**Date:** {time.strftime('%Y-%m-%d %H:%M')}",
        f"**Source:** POCKET Fusion Sense + platform",
        f"",
        f"## Live host context",
        f"- Page: {page.get('page_hint')}",
        f"- Symbols: {(page.get('counts') or {}).get('symbols')}",
        f"- Primary: {page.get('primary_modality')}",
        f"- Brief: {page.get('brief')}",
        f"",
        f"## Buttons (actionable)",
        *[f"- {b.get('text')}" for b in (page.get("buttons") or [])[:25]],
        f"",
        f"## OCR head",
        (page.get("ocr_plain") or "")[:2000],
        f"",
        f"## External",
        json.dumps(meta, indent=2) if meta else "(none)",
        f"",
        f"## Next actions",
        f"1. Review fusion remake: POST /v1/rfe/synthesize",
        f"2. Continue mission if multi-hour research",
        f"",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    return {
        "ok": path.is_file(),
        "title": "Research pack",
        "deliverable": str(path),
        "symbols": (page.get("counts") or {}).get("symbols"),
        "brief": page.get("brief"),
        "open": f"explorer /select,\"{path}\"",
    }


def _real2(**opts) -> Dict[str, Any]:
    """Bootstrap real project under vcomp workspace + Documents."""
    from pocket.virtual_computer import open_computer, write_file, shell, list_workspace

    open_computer(label="real2")
    name = opts.get("name") or f"pocket_project_{time.strftime('%Y%m%d')}"
    rel = f"projects/{name}"
    readme = f"""# {name}

Bootstrapped by POCKET real workflow (real2).

## Run

```
python main.py
```

## API

Host co-pilot: GET /v1/api
"""
    main_py = '''"""Minimal project entry — created by POCKET real workflow."""
def main():
    print("POCKET project bootstrap OK")
    print("2+2 =", 2 + 2)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
'''
    w1 = write_file(f"{rel}/README.md", readme)
    w2 = write_file(f"{rel}/main.py", main_py)
    # also copy-ish to Documents for user visibility
    doc_dir = DOCS / name
    doc_dir.mkdir(parents=True, exist_ok=True)
    (doc_dir / "README.md").write_text(readme, encoding="utf-8")
    (doc_dir / "main.py").write_text(main_py, encoding="utf-8")
    run = shell(f"python projects/{name}/main.py", timeout=30)
    ws = list_workspace()
    return {
        "ok": bool(w1.get("ok") and w2.get("ok") and run.get("ok")),
        "title": "Project bootstrap",
        "project_vcomp": w2.get("path"),
        "project_docs": str(doc_dir),
        "run_stdout": (run.get("stdout") or "")[:500],
        "files": [f for f in (ws.get("files") or []) if name in f.get("path", "")],
    }


def _real3(**opts) -> Dict[str, Any]:
    """Desktop triage: real task list from fusion symbols."""
    from pocket.perception import sense
    from pocket.rfe_kernel import materialize

    page = sense(max_ui=450, force=True)
    rfe = materialize(page=page, instruction_set="FULL_SYNTHESIS", refresh=False)
    day = time.strftime("%Y-%m-%d_%H%M")
    path = DOCS / f"Desktop_Triage_{day}.md"
    buttons = page.get("buttons") or []
    links = page.get("links") or []
    lines = [
        f"# Desktop triage — {time.strftime('%Y-%m-%d %H:%M')}",
        f"",
        f"**Window:** {page.get('page_hint')}",
        f"**Symbols:** {(page.get('counts') or {}).get('symbols')}",
        f"**RFE:** {rfe.get('brief')}",
        f"",
        f"## Suggested tasks (from live UI)",
    ]
    for i, b in enumerate(buttons[:20], 1):
        lines.append(f"{i}. [ ] Click/review **{b.get('text')}**")
    if links:
        lines.append("")
        lines.append("## Links seen")
        for L in links[:15]:
            lines.append(f"- {L.get('text')}")
    lines += [
        "",
        "## RFE outputs",
        f"- packet: {(rfe.get('paths') or {}).get('packet')}",
        f"- html: {(rfe.get('paths') or {}).get('html')}",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return {
        "ok": path.is_file() and rfe.get("ok"),
        "title": "Desktop triage",
        "deliverable": str(path),
        "tasks": min(20, len(buttons)),
        "rfe_uuid": rfe.get("uuid"),
        "symbols": (page.get("counts") or {}).get("symbols"),
    }


def _real4(**opts) -> Dict[str, Any]:
    """Marketing pack: product phone + web remake from latest recording."""
    from pocket.video_studio import list_recordings
    from pocket.device_remake import (
        product_phone_from_recording,
        product_phone_from_image,
        product_web_from_image,
    )

    recs = list_recordings(limit=5)
    src = opts.get("source") or (recs[0]["path"] if recs else "")
    phone_vid = None
    if src:
        phone_vid = product_phone_from_recording(
            src,
            title=opts.get("title") or "POCKET",
            caption=opts.get("caption") or "Host co-pilot",
            max_seconds=float(opts.get("max_seconds") or 10),
            n_frames=int(opts.get("n_frames") or 8),
        )
    phone_still = product_phone_from_image(None, title="POCKET", caption="Product stage")
    web_still = product_web_from_image(None, title="POCKET", brand="pocket.local")
    # index file for user
    idx = DOCS / f"Marketing_Pack_{time.strftime('%Y%m%d_%H%M')}.md"
    idx.write_text(
        "\n".join(
            [
                "# Marketing pack",
                "",
                f"- Phone video: {(phone_vid or {}).get('output') or (phone_vid or {}).get('path')}",
                f"- Phone still: {phone_still.get('path')}",
                f"- Web still: {web_still.get('path')}",
                f"- Method: mobile remake inside lifelike iPhone (not desktop crop)",
                f"- Source recording: {src or '(live still only)'}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    ok = bool(phone_still.get("ok") and web_still.get("ok") and (phone_vid is None or phone_vid.get("ok") or phone_still.get("ok")))
    return {
        "ok": ok,
        "title": "Marketing pack",
        "deliverable": str(idx),
        "phone_video": phone_vid,
        "phone_still": phone_still.get("path"),
        "web_still": web_still.get("path"),
        "source": src,
    }
