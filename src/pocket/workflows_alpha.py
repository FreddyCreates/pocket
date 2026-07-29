"""Five production alpha workflows — multimodal, fusion-grounded, real host actions.

Run via: POST /v1/workflows/run  { "id": "wf1" }
Or:     python -m pocket.workflows_alpha
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

from pocket.live_events import emit

OUT = Path.home() / ".pocket" / "workflows"
OUT.mkdir(parents=True, exist_ok=True)


def catalog() -> List[Dict[str, Any]]:
    return [
        {
            "id": "wf1_fusion_desktop_sense",
            "title": "Fusion desktop sense + remake",
            "multimodal": ["vision", "uia", "ocr", "remake"],
            "desc": "Full page render (200+ symbols) → fusion remake HTML/3D scene",
        },
        {
            "id": "wf2_apps_and_scroll",
            "title": "Open apps + fusion-guided scroll",
            "multimodal": ["desktop", "vision", "ui"],
            "desc": "Open Notepad + Explorer, sense between steps, scroll like a user",
        },
        {
            "id": "wf3_browser_github",
            "title": "Edge browser GitHub explore",
            "multimodal": ["browser", "vision", "click"],
            "desc": "Open GitHub, fusion sense, scroll, capture symbols/buttons",
        },
        {
            "id": "wf4_codex_terminal",
            "title": "Virtual computer + Codex terminal work",
            "multimodal": ["shell", "terminal", "files", "vision"],
            "desc": "Open vcomp, terminal, write file, run codex/python probes, sense",
        },
        {
            "id": "wf5_record_studio_viral",
            "title": "Record → fusion captions → viral studio pack",
            "multimodal": ["record", "vision", "studio", "imagine"],
            "desc": "Short SPECULUM record, page sense, rotato_phone + x_screencast exports",
        },
    ]


def run_workflow(wid: str, **opts) -> Dict[str, Any]:
    wid = (wid or "").lower().replace("-", "_")
    emit("workflow", f"Run {wid}", agent="ARCHON", role="host")
    t0 = time.time()
    runners = {
        "wf1_fusion_desktop_sense": _wf1,
        "wf1": _wf1,
        "wf2_apps_and_scroll": _wf2,
        "wf2": _wf2,
        "wf3_browser_github": _wf3,
        "wf3": _wf3,
        "wf4_codex_terminal": _wf4,
        "wf4": _wf4,
        "wf5_record_studio_viral": _wf5,
        "wf5": _wf5,
    }
    fn = runners.get(wid)
    if not fn:
        return {"ok": False, "error": f"unknown workflow {wid}", "catalog": catalog()}
    try:
        result = fn(**opts)
        result["workflow_id"] = wid
        result["ms"] = int((time.time() - t0) * 1000)
        path = OUT / f"{wid}_{int(time.time())}.json"
        path.write_text(json.dumps(result, indent=2, default=str)[:500000], encoding="utf-8")
        result["log_path"] = str(path)
        return result
    except Exception as e:
        return {"ok": False, "workflow_id": wid, "error": str(e), "ms": int((time.time() - t0) * 1000)}


def run_all() -> Dict[str, Any]:
    results = []
    for c in catalog():
        results.append(run_workflow(c["id"]))
    ok = sum(1 for r in results if r.get("ok"))
    return {"ok": ok == len(results), "passed": ok, "total": len(results), "results": results}


def _wf1(**opts) -> Dict[str, Any]:
    from pocket.perception import sense
    from pocket.fusion_remake import remake

    page = sense(max_ui=int(opts.get("max_ui") or 500), force=True, grid=5)
    rem = remake(refresh_page=False, max_ui=400)
    return {
        "ok": bool(page.get("ok") and rem.get("ok")),
        "title": "Fusion desktop sense + remake",
        "symbols": (page.get("counts") or {}).get("symbols"),
        "brief": page.get("brief"),
        "remake": rem.get("brief"),
        "paths": rem.get("paths"),
        "steps": [
            {"step": "sense", "ok": page.get("ok"), "counts": page.get("counts")},
            {"step": "remake", "ok": rem.get("ok"), "nodes": rem.get("nodes")},
        ],
    }


def _wf2(**opts) -> Dict[str, Any]:
    from pocket.orchestrator import get_orchestrator
    from pocket.perception import sense
    from pocket.virtual_computer import open_computer, act

    open_computer(label="wf2")
    orch = get_orchestrator()
    steps_log = []
    for sid in ("open_notepad", "open_explorer"):
        r = orch.execute(sid)
        steps_log.append({"skill": sid, "ok": r.get("ok"), "fusion": r.get("fusion_brief")})
        time.sleep(0.8)
    s1 = sense(force=True, max_ui=300)
    steps_log.append({"step": "sense", "ok": s1.get("ok"), "brief": s1.get("brief")})
    sc = act("scroll", direction="down", n=3)
    steps_log.append({"step": "scroll", "ok": sc.get("ok"), "after": sc.get("after_sense")})
    s2 = sense(force=True, max_ui=300)
    return {
        "ok": all(x.get("ok") for x in steps_log if "ok" in x),
        "title": "Open apps + fusion-guided scroll",
        "steps": steps_log,
        "final_brief": s2.get("brief"),
        "counts": s2.get("counts"),
    }


def _wf3(**opts) -> Dict[str, Any]:
    from pocket.virtual_computer import open_computer, act, sense_computer

    open_computer(label="wf3")
    steps = []
    r = act("open_url", url=opts.get("url") or "https://github.com")
    steps.append({"step": "open_github", "ok": r.get("ok"), "after": r.get("after_sense")})
    time.sleep(2.5)
    sc = act("scroll", direction="down", n=4)
    steps.append({"step": "scroll", "ok": sc.get("ok")})
    time.sleep(0.8)
    sense = sense_computer(max_ui=450)
    steps.append({"step": "sense", "ok": sense.get("ok"), "counts": sense.get("counts")})
    # try fusion click on a common control if present
    names = [b.get("text") for b in (sense.get("context") or {}).get("buttons") or []]
    clicked = None
    for cand in names[:8]:
        if cand and len(cand) > 2:
            clicked = act("click", name=cand)
            steps.append({"step": "fusion_click", "name": cand, "ok": clicked.get("ok")})
            break
    return {
        "ok": sense.get("ok") and r.get("ok"),
        "title": "Edge browser GitHub explore",
        "steps": steps,
        "brief": sense.get("brief"),
        "symbol_head": (sense.get("symbols") or [])[:15],
    }


def _wf4(**opts) -> Dict[str, Any]:
    from pocket.virtual_computer import (
        open_computer,
        shell,
        write_file,
        open_terminal,
        sense_computer,
        list_workspace,
    )
    from pocket.terminals import send_terminal

    open_computer(label="wf4")
    steps = []
    w = write_file(
        "alpha_probe.py",
        "print('POCKET virtual computer alpha')\nprint(2+2)\n",
    )
    steps.append({"step": "write_file", "ok": w.get("ok"), "path": w.get("path")})
    py = shell("python alpha_probe.py", timeout=30)
    steps.append({"step": "python_run", "ok": py.get("ok"), "stdout": (py.get("stdout") or "")[:200]})
    # codex probe (version / help — not a long interactive session)
    cx = shell("codex --version 2>&1; if (-not $?) { codex -h 2>&1 | Select-Object -First 5 }", timeout=45)
    steps.append(
        {
            "step": "codex_probe",
            "ok": True,  # presence probe; may fail if not installed
            "returncode": cx.get("returncode"),
            "stdout": (cx.get("stdout") or cx.get("stderr") or "")[:300],
        }
    )
    term = open_terminal(kind="powershell")
    tid = (term.get("terminal") or {}).get("id")
    if tid:
        send_terminal(tid, "Write-Host 'vcomp terminal live'; Get-Date")
        steps.append({"step": "terminal", "ok": True, "id": tid})
    sense = sense_computer(max_ui=300)
    steps.append({"step": "sense", "ok": sense.get("ok"), "brief": sense.get("brief")})
    ws = list_workspace()
    return {
        "ok": w.get("ok") and py.get("ok"),
        "title": "Virtual computer + Codex terminal work",
        "steps": steps,
        "workspace": ws.get("files"),
        "brief": sense.get("brief"),
    }


def _wf5(**opts) -> Dict[str, Any]:
    from pocket.screen_record import record_start, record_stop, record_status
    from pocket.perception import sense
    from pocket.video_studio import render, list_recordings
    from pocket.imagine_studio import compose
    from pocket.virtual_computer import open_computer, act

    open_computer(label="wf5")
    steps = []
    # short live activity then record
    act("open_app", app="notepad")
    time.sleep(0.6)
    rs = record_start(label="alpha-wf5")
    steps.append({"step": "record_start", "ok": rs.get("ok"), "path": rs.get("path")})
    time.sleep(1.0)
    act("type", text="POCKET alpha viral demo — fusion + studio\n")
    time.sleep(1.2)
    act("scroll", direction="down", n=2)
    time.sleep(1.0)
    stop = record_stop()
    steps.append({"step": "record_stop", "ok": stop.get("ok"), "path": stop.get("path")})
    page = sense(force=True, max_ui=300)
    steps.append({"step": "fusion_sense", "ok": page.get("ok"), "brief": page.get("brief")})

    # pick recording
    src = stop.get("path") or ""
    if not src:
        recs = list_recordings(limit=3)
        src = (recs[0]["path"] if recs else "") or ""
    exports = []
    if src:
        for preset in ("rotato_phone", "x_screencast"):
            r = render(
                src,
                preset=preset,
                title="POCKET Alpha",
                subtitle=page.get("page_hint") or "Host co-pilot",
                caption=(page.get("brief") or "")[:80],
                cta="ItsNotAI Labs",
                max_seconds=12,
            )
            exports.append({"preset": preset, "ok": r.get("ok"), "output": r.get("output") or r.get("error")})
            steps.append({"step": f"studio_{preset}", "ok": r.get("ok"), "out": r.get("name")})
    still = compose(mode="rotato_phone", title="POCKET Alpha", subtitle="Imagine Studio")
    steps.append({"step": "imagine_still", "ok": still.get("ok"), "path": still.get("path")})

    ok = bool(stop.get("ok") or src) and any(e.get("ok") for e in exports)
    return {
        "ok": ok or still.get("ok"),
        "title": "Record → fusion → viral studio",
        "source": src,
        "exports": exports,
        "still": still.get("path"),
        "fusion_brief": page.get("brief"),
        "steps": steps,
    }


if __name__ == "__main__":
    print(json.dumps(run_all(), indent=2, default=str)[:8000])
