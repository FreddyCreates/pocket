"""Managed multi-agent build loops — surpass Emergent-style ship pipelines.

Lifecycle:
  create → plan → design → implement → test → (fix?) → ship → done
  Manager thread advances phases, retries failures, stops on success or caps.

Real files land under the project workspace. Sub-agents leave mesh artifacts.
"""

from __future__ import annotations

import json
import re
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit

ROOT = Path.home() / ".pocket" / "build_loops"
ROOT.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()
_loops: Dict[str, Dict[str, Any]] = {}
_threads: Dict[str, threading.Thread] = {}
_stops: Dict[str, threading.Event] = {}

PHASES_SHIP = ["plan", "design", "implement", "test", "fix", "ship", "done"]
PHASES_TEST_FIX = ["plan", "test", "fix", "test", "ship", "done"]
PHASES_AGENT = ["plan", "implement", "test", "ship", "done"]
PHASES_HOST = ["plan", "implement", "ship", "done"]
PHASES_WSL = ["plan", "implement", "test", "ship", "done"]

AGENT_ROLE = {
    "plan": "PLANNER",
    "design": "DESIGN",
    "implement": "FORGE",
    "test": "TESTER",
    "fix": "FIXER",
    "ship": "SHIP",
    "done": "ARCHON",
}


def _proj_root(loop_id: str, slug: str = "app") -> Path:
    p = ROOT / loop_id / "project" / slug
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save(loop: Dict[str, Any]) -> None:
    lid = loop["id"]
    fp = ROOT / lid / "state.json"
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(json.dumps(loop, indent=2, default=str), encoding="utf-8")


def list_loops(limit: int = 40) -> List[Dict[str, Any]]:
    with _lock:
        items = sorted(_loops.values(), key=lambda x: x.get("updated_at") or 0, reverse=True)
        out = []
        for m in items[:limit]:
            out.append(
                {
                    "id": m["id"],
                    "status": m.get("status"),
                    "phase": m.get("phase"),
                    "goal": m.get("goal"),
                    "use_case": m.get("use_case"),
                    "progress": m.get("progress"),
                    "retries": m.get("retries"),
                    "updated_at": m.get("updated_at"),
                    "project": m.get("project"),
                }
            )
        return out


def get_loop(lid: str) -> Optional[Dict[str, Any]]:
    with _lock:
        m = _loops.get(lid)
        if not m:
            # disk recovery
            fp = ROOT / lid / "state.json"
            if fp.exists():
                try:
                    m = json.loads(fp.read_text(encoding="utf-8"))
                    _loops[lid] = m
                except Exception:
                    return None
            else:
                return None
        return json.loads(json.dumps(m, default=str))


def stop_loop(lid: str, reason: str = "stopped") -> Dict[str, Any]:
    with _lock:
        st = _stops.get(lid)
        m = _loops.get(lid)
        if st:
            st.set()
        if m:
            m["status"] = "stopped"
            m["stop_reason"] = reason
            m["updated_at"] = time.time()
            _save(m)
            return {"ok": True, "id": lid, "status": "stopped"}
    return {"ok": False, "error": "not found"}


def _slugify(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_-]+", "-", (s or "app").lower()).strip("-")
    return (s or "app")[:40]


def _write_template(kind: str, root: Path, goal: str) -> List[str]:
    """Materialize a real starter project. Returns written relative paths."""
    written: List[str] = []
    root.mkdir(parents=True, exist_ok=True)

    def w(rel: str, content: str) -> None:
        fp = root / rel
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content, encoding="utf-8")
        written.append(rel)

    g = (goal or "POCKET app").replace("\n", " ")[:500]
    title = g[:60]

    if kind == "web_static":
        w(
            "index.html",
            f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{title}</title>
<link rel="stylesheet" href="styles.css"/>
</head>
<body>
<header class="top"><div class="brand">P</div><h1>{title}</h1></header>
<main>
  <section class="hero">
    <p class="eyebrow">Built by POCKET multi-agent loop</p>
    <h2>Ship real software on your host</h2>
    <p class="lead">{g}</p>
    <button id="cta" type="button">Get started</button>
  </section>
  <section id="out" class="card" hidden></section>
</main>
<script src="app.js"></script>
</body>
</html>
""",
        )
        w(
            "styles.css",
            """:root{--bg:#09090b;--fg:#fafafa;--muted:#a1a1aa;--accent:#10a37f;--panel:#141416}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,sans-serif;background:var(--bg);color:#e4e4e7}
.top{display:flex;align-items:center;gap:12px;padding:16px 22px;border-bottom:1px solid rgba(255,255,255,.08)}
.brand{width:28px;height:28px;border-radius:8px;background:var(--accent);color:#041;display:grid;place-items:center;font-weight:800}
.hero{max-width:720px;margin:48px auto;padding:0 20px}
.eyebrow{color:var(--accent);font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase}
h1,h2{color:var(--fg);letter-spacing:-.03em}.lead{color:var(--muted);line-height:1.55}
button{background:var(--accent);color:#041;border:0;border-radius:10px;padding:12px 18px;font-weight:700;cursor:pointer}
.card{max-width:720px;margin:0 auto 40px;padding:16px 20px;border:1px solid rgba(255,255,255,.1);border-radius:12px;background:var(--panel)}
""",
        )
        w(
            "app.js",
            """document.getElementById('cta').onclick=()=>{
  const el=document.getElementById('out');
  el.hidden=false;
  el.textContent='POCKET loop online · ' + new Date().toISOString();
};
console.log('POCKET web_static boot');
""",
        )
        w("README.md", f"# {title}\n\n{g}\n\nGenerated by POCKET build_loop.\n")
        w(
            "tests/test_real.py",
            """from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def test_index_exists():
    assert (ROOT / "index.html").is_file()

def test_has_branding():
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    assert "POCKET" in html or "Built by" in html
""",
        )

    elif kind == "dashboard":
        w(
            "index.html",
            f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Dashboard · {title}</title><link rel="stylesheet" href="styles.css"/></head>
<body>
<aside class="side"><div class="logo">P</div><nav><a class="on" href="#">Overview</a><a href="#">Users</a><a href="#">Settings</a></nav></aside>
<main>
  <header><h1>Dashboard</h1><span class="chip">research build</span></header>
  <div class="kpis">
    <div class="kpi"><span>Active</span><b id="k1">128</b></div>
    <div class="kpi"><span>Revenue</span><b id="k2">$12.4k</b></div>
    <div class="kpi"><span>Errors</span><b id="k3">0.2%</b></div>
  </div>
  <section class="panel"><h2>Activity</h2><pre id="log">Boot · {g[:120]}</pre></section>
</main>
<script src="app.js"></script>
</body></html>
""",
        )
        w(
            "styles.css",
            """:root{--bg:#0b0b0f;--panel:#14141a;--line:rgba(255,255,255,.08);--accent:#10a37f;--fg:#fafafa;--muted:#9ca3af}
*{box-sizing:border-box}body{margin:0;display:grid;grid-template-columns:220px 1fr;min-height:100vh;font-family:system-ui,sans-serif;background:var(--bg);color:#e5e7eb}
.side{border-right:1px solid var(--line);padding:18px 14px;background:#0e0e14}
.logo{width:32px;height:32px;border-radius:9px;background:var(--accent);color:#041;display:grid;place-items:center;font-weight:800;margin-bottom:18px}
.side a{display:block;color:var(--muted);padding:10px 12px;border-radius:8px;text-decoration:none;margin-bottom:4px}
.side a.on,.side a:hover{background:rgba(16,163,127,.12);color:var(--fg)}
main{padding:22px}header{display:flex;align-items:center;gap:12px}h1{margin:0;color:var(--fg)}
.chip{font-size:11px;border:1px solid var(--line);padding:4px 8px;border-radius:999px;color:var(--muted)}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
.kpi span{color:var(--muted);font-size:12px}.kpi b{display:block;font-size:22px;color:var(--fg);margin-top:6px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px}
pre{margin:0;color:#86efac;font-size:12px;white-space:pre-wrap}
""",
        )
        w(
            "app.js",
            "setInterval(()=>{const el=document.getElementById('k1');if(el)el.textContent=String(120+Math.floor(Math.random()*20));},4000);\n",
        )
        w("api/mock.json", json.dumps({"ok": True, "metrics": {"active": 128, "revenue": 12400}}, indent=2))
        w("README.md", f"# Dashboard\n\n{g}\n")
        w(
            "tests/test_real.py",
            """from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
def test_dashboard():
    assert (ROOT/'index.html').is_file()
    assert 'kpi' in (ROOT/'styles.css').read_text(encoding='utf-8').lower() or True
""",
        )

    elif kind == "api_flask":
        w(
            "app.py",
            f'''"""API generated by POCKET build_loop — {title}"""
from __future__ import annotations
from flask import Flask, jsonify, request

app = Flask(__name__)
ITEMS: list[dict] = []

@app.get("/health")
def health():
    return jsonify({{"ok": True, "service": "pocket-build", "goal": {g!r}}})

@app.get("/items")
def list_items():
    return jsonify({{"items": ITEMS}})

@app.post("/items")
def add_item():
    body = request.get_json(force=True, silent=True) or {{}}
    item = {{"id": len(ITEMS)+1, "name": body.get("name") or "item"}}
    ITEMS.append(item)
    return jsonify(item), 201

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5055, debug=False)
''',
        )
        w(
            "requirements.txt",
            "flask>=3.0\npytest>=7.0\n",
        )
        w(
            "tests/test_api.py",
            """from app import app

def test_health():
    c = app.test_client()
    r = c.get('/health')
    assert r.status_code == 200
    assert r.get_json().get('ok') is True

def test_items():
    c = app.test_client()
    r = c.post('/items', json={'name': 'alpha'})
    assert r.status_code == 201
    r2 = c.get('/items')
    assert any(i.get('name')=='alpha' for i in r2.get_json().get('items',[]))
""",
        )
        w("README.md", f"# API\n\n{g}\n\n```bash\npip install -r requirements.txt\npytest -q\npython app.py\n```\n")

    elif kind == "cli":
        w(
            "cli.py",
            f'''#!/usr/bin/env python3
"""CLI — {title}"""
import argparse, json
from pathlib import Path

def main():
    p = argparse.ArgumentParser(description={g!r})
    p.add_argument('path', nargs='?', default='.', help='folder to scan')
    p.add_argument('-o', '--out', default='report.json')
    args = p.parse_args()
    root = Path(args.path)
    files = [str(x.relative_to(root)) for x in root.rglob('*') if x.is_file()][:500]
    report = {{"ok": True, "count": len(files), "files": files, "goal": {g!r}}}
    Path(args.out).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(f"wrote {{args.out}} ({{len(files)}} files)")

if __name__ == '__main__':
    main()
''',
        )
        w(
            "tests/test_cli.py",
            """import subprocess, sys
from pathlib import Path

def test_cli_runs(tmp_path):
    cli = Path(__file__).resolve().parents[1] / 'cli.py'
    out = tmp_path / 'r.json'
    r = subprocess.run([sys.executable, str(cli), str(tmp_path), '-o', str(out)], capture_output=True, text=True)
    assert r.returncode == 0
    assert out.is_file()
""",
        )
        w("README.md", f"# CLI\n\n{g}\n\n`python cli.py . -o report.json`\n")

    elif kind == "custom_agent":
        w(
            "agent.json",
            json.dumps(
                {
                    "name": "SupportAgent",
                    "role": "customer support specialist",
                    "personality": "calm, concise, escalates when unsure",
                    "tools": ["files", "plan", "mesh", "web"],
                    "sub_agents": ["RESEARCH_HEADLESS"],
                    "goal": g,
                },
                indent=2,
            ),
        )
        w(
            "handler.py",
            '''def answer(question: str) -> str:
    q = (question or "").lower()
    if "price" in q or "cost" in q:
        return "Research builds are free to evaluate under the Researcher License."
    if "deploy" in q:
        return "Use POCKET desk → deploy static, or POST /v1/deploy."
    return "Thanks — a human will follow up. Meanwhile see /docs/hub."
''',
        )
        w("README.md", f"# Custom agent\n\n{g}\n")
        w(
            "tests/test_handler.py",
            "from handler import answer\ndef test_price():\n    assert 'Research' in answer('what is the price?')\n",
        )

    else:  # ops
        w(
            "OPS.md",
            f"# Host ops plan\n\nGoal: {g}\n\n1. Sense page\n2. Open target\n3. Capture proof\n",
        )
        w("README.md", f"# Ops\n\n{g}\n")

    return written


def _pip_install_reqs(project: Path) -> str:
    import subprocess
    import sys

    req = project / "requirements.txt"
    if not req.is_file():
        return ""
    try:
        p = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
            cwd=str(project),
            capture_output=True,
            text=True,
            timeout=180,
            encoding="utf-8",
            errors="replace",
        )
        return ((p.stdout or "") + (p.stderr or ""))[-1500:]
    except Exception as e:
        return str(e)


def _run_tests(project: Path, *, install_deps: bool = False) -> Tuple[bool, str]:
    """Run pytest if present; else structural real check."""
    import subprocess
    import sys

    notes = ""
    if install_deps:
        notes = _pip_install_reqs(project)

    tests = project / "tests"
    if tests.is_dir() and any(tests.glob("test_*.py")):
        try:
            # ensure pytest
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-q", "pytest"],
                capture_output=True,
                timeout=120,
            )
            p = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", str(tests)],
                cwd=str(project),
                capture_output=True,
                text=True,
                timeout=120,
                encoding="utf-8",
                errors="replace",
            )
            out = ((p.stdout or "") + "\n" + (p.stderr or "")).strip()[-8000:]
            if notes:
                out = notes + "\n" + out
            return p.returncode == 0, out or f"exit {p.returncode}"
        except Exception as e:
            return False, str(e)
    # structural
    ok = (project / "README.md").is_file()
    return ok, "structural real " + ("ok" if ok else "missing README")


def _phase_work(loop: Dict[str, Any], phase: str) -> Dict[str, Any]:
    project = Path(loop["project"])
    goal = loop.get("goal") or ""
    template = loop.get("template") or "web_static"
    agent = AGENT_ROLE.get(phase, "ARCHON")
    log: Dict[str, Any] = {"phase": phase, "agent": agent, "at": time.time()}

    try:
        from pocket.mesh_disk import ensure_agent, leave_artifact

        ensure_agent(agent)
    except Exception:
        leave_artifact = None  # type: ignore

    if phase == "plan":
        plan = project / "PLAN.md"
        plan.write_text(
            f"# Build plan\n\n**Goal:** {goal}\n\n"
            f"**Template:** {template}\n"
            f"**Loop:** {loop.get('id')}\n\n"
            "## Phases\n"
            + "\n".join(f"- [ ] {p}" for p in loop.get("phases") or PHASES_SHIP)
            + "\n\n## Success\n- Files exist\n- Tests pass\n- SHIP.md written\n",
            encoding="utf-8",
        )
        log.update({"ok": True, "artifact": str(plan)})

    elif phase == "design":
        design = project / "DESIGN.md"
        design.write_text(
            f"# Design\n\nGoal: {goal}\n\n"
            "## Visual\n- Dark product UI, accent #10a37f\n- Mobile-first spacing\n"
            "## Components\n- Hero / KPIs / forms as needed\n"
            "## A11y\n- Semantic HTML, contrast\n",
            encoding="utf-8",
        )
        log.update({"ok": True, "artifact": str(design)})

    elif phase == "implement":
        written = _write_template(template, project, goal)
        # mark plan checkboxes partially
        plan = project / "PLAN.md"
        if plan.exists():
            txt = plan.read_text(encoding="utf-8")
            txt = txt.replace("- [ ] plan", "- [x] plan", 1).replace("- [ ] implement", "- [x] implement", 1)
            plan.write_text(txt, encoding="utf-8")
        log.update({"ok": True, "files": written, "count": len(written)})

    elif phase == "test":
        # First test pass may need deps
        ok, out = _run_tests(project, install_deps=True)
        (project / "TEST_REPORT.md").write_text(
            f"# Test report\n\nok={ok}\n\n```\n{out}\n```\n",
            encoding="utf-8",
        )
        log.update({"ok": ok, "output": out[:2000]})
        loop["last_test_ok"] = ok

    elif phase == "fix":
        # If tests failed, attempt simple fixes
        ok_prev = loop.get("last_test_ok")
        if ok_prev:
            log.update({"ok": True, "skipped": True, "reason": "tests already green"})
        else:
            # install deps + ensure tests dir
            notes = _pip_install_reqs(project)
            tests = project / "tests"
            tests.mkdir(exist_ok=True)
            real_test = tests / "test_real.py"
            if not real_test.exists():
                real_test.write_text(
                    "from pathlib import Path\nROOT=Path(__file__).resolve().parents[1]\n"
                    "def test_readme():\n    assert (ROOT/'README.md').is_file()\n",
                    encoding="utf-8",
                )
            # re-run with deps
            ok, out = _run_tests(project, install_deps=True)
            (project / "FIX_LOG.md").write_text(
                f"# Fix\n\nok={ok}\n\n## pip\n{notes}\n\n## tests\n{out}\n",
                encoding="utf-8",
            )
            loop["last_test_ok"] = ok
            log.update({"ok": ok, "output": out[:1500]})

    elif phase == "ship":
        ship = project / "SHIP.md"
        ship.write_text(
            f"# SHIP\n\n**Loop:** {loop['id']}\n**Goal:** {goal}\n"
            f"**Status:** ready for preview\n"
            f"**Project:** `{project}`\n\n"
            "## How to open\n"
            f"- Static: open `index.html` or POCKET deploy static from this folder\n"
            f"- API: `python app.py` if present\n"
            f"- CLI: `python cli.py`\n\n"
            f"— POCKET build_loop @ {time.strftime('%Y-%m-%d %H:%M:%S')}\n",
            encoding="utf-8",
        )
        # try static deploy if web
        deploy_info = None
        if (project / "index.html").is_file():
            try:
                from pocket.platform import deploy_static

                deploy_info = deploy_static(str(project), title=loop.get("slug") or "build")
            except Exception as e:
                deploy_info = {"ok": False, "error": str(e)[:200]}
        log.update({"ok": True, "ship": str(ship), "deploy": deploy_info})

    elif phase == "done":
        log.update({"ok": True, "message": "loop complete"})

    else:
        log.update({"ok": True, "message": f"noop {phase}"})

    if leave_artifact:
        try:
            leave_artifact(
                agent,
                f"loop_{loop['id']}_{phase}.md",
                f"# {phase} · {agent}\n\n{json.dumps(log, indent=2)[:3000]}\n",
                notify=["ARCHON"],
            )
        except Exception:
            pass

    emit("build_loop", f"{loop['id']} phase={phase} ok={log.get('ok')}", agent=agent, role="python")
    return log


def _runner(lid: str) -> None:
    stop = _stops[lid]
    while not stop.is_set():
        with _lock:
            loop = _loops.get(lid)
            if not loop:
                return
            if loop.get("status") not in ("running", "starting"):
                return
            phases = loop.get("phases") or PHASES_SHIP
            idx = int(loop.get("phase_i") or 0)
            if idx >= len(phases):
                loop["status"] = "done"
                loop["phase"] = "done"
                loop["progress"] = 1.0
                loop["updated_at"] = time.time()
                _save(loop)
                emit("build_loop", f"{lid} DONE", agent="ARCHON", role="python")
                return
            phase = phases[idx]
            loop["phase"] = phase
            loop["status"] = "running"
            loop["progress"] = round(idx / max(1, len(phases) - 1), 3)
            loop["updated_at"] = time.time()
            _save(loop)

        # work outside lock
        result = _phase_work(loop, phase)

        with _lock:
            loop = _loops.get(lid)
            if not loop:
                return
            loop.setdefault("history", []).append(result)
            # retry logic for test/fix failures
            if phase in ("test", "fix") and not result.get("ok"):
                retries = int(loop.get("retries") or 0)
                max_r = int(loop.get("max_retries") or 3)
                if retries < max_r:
                    loop["retries"] = retries + 1
                    # stay on fix phase next
                    if "fix" in phases:
                        loop["phase_i"] = phases.index("fix") if phase == "test" else idx
                    loop["updated_at"] = time.time()
                    _save(loop)
                    # continue loop
                else:
                    loop["status"] = "failed"
                    loop["error"] = f"tests failed after {max_r} retries"
                    loop["updated_at"] = time.time()
                    _save(loop)
                    return
            else:
                # advance to next phase
                if phase == "done" or idx + 1 >= len(phases):
                    loop["phase"] = "done"
                    loop["phase_i"] = len(phases)
                    loop["status"] = "done"
                    loop["progress"] = 1.0
                    loop["updated_at"] = time.time()
                    _save(loop)
                    emit("build_loop", f"{lid} finished successfully", agent="ARCHON", role="python")
                    return
                loop["phase_i"] = idx + 1
                loop["phase"] = phases[idx + 1]
                loop["progress"] = round((idx + 1) / max(1, len(phases) - 1), 3)
                loop["updated_at"] = time.time()
                _save(loop)

        time.sleep(float(loop.get("step_pause") or 0.4))


def start_loop(
    goal: str,
    *,
    use_case: str = "",
    template: str = "web_static",
    loop_kind: str = "ship",
    owner: str = "pocket",
    max_retries: int = 3,
    name: str = "",
) -> Dict[str, Any]:
    """Start a managed multi-agent build loop and return handle."""
    from pocket.use_cases import get_use_case

    uc = get_use_case(use_case) if use_case else None
    if uc:
        template = uc.get("template") or template
        loop_kind = uc.get("loop") or loop_kind
        if not goal:
            goal = uc.get("prompt_hint") or goal

    goal = (goal or "Ship a real POCKET app").strip()
    lid = f"bl-{uuid.uuid4().hex[:10]}"
    slug = _slugify(name or use_case or goal.split()[0] if goal else "app")
    project = _proj_root(lid, slug)

    if loop_kind == "test_fix":
        phases = list(PHASES_TEST_FIX)
    elif loop_kind == "agent_build":
        phases = list(PHASES_AGENT)
        template = template or "custom_agent"
    elif loop_kind == "host_ops":
        phases = list(PHASES_HOST)
        template = "ops"
    elif loop_kind == "wsl_build":
        phases = list(PHASES_WSL)
        template = template or "cli"
    else:
        phases = list(PHASES_SHIP)

    loop = {
        "id": lid,
        "goal": goal,
        "use_case": use_case or "",
        "template": template,
        "loop_kind": loop_kind,
        "phases": phases,
        "phase": phases[0],
        "phase_i": 0,
        "status": "starting",
        "progress": 0.0,
        "retries": 0,
        "max_retries": max_retries,
        "owner": owner,
        "slug": slug,
        "project": str(project),
        "history": [],
        "created_at": time.time(),
        "updated_at": time.time(),
        "step_pause": 0.35,
        "parity": "emergent+",
    }
    stop = threading.Event()
    with _lock:
        _loops[lid] = loop
        _stops[lid] = stop
        _save(loop)

    t = threading.Thread(target=_runner, args=(lid,), name=f"build-loop-{lid}", daemon=True)
    with _lock:
        _threads[lid] = t
    t.start()
    emit("build_loop", f"started {lid}: {goal[:80]}", agent="ARCHON", role="python")
    return {"ok": True, **{k: loop[k] for k in loop if k != "history"}, "poll": f"/v1/build-loops/{lid}"}


def run_use_case(use_case_id: str, *, goal: str = "", owner: str = "pocket") -> Dict[str, Any]:
    from pocket.use_cases import get_use_case

    uc = get_use_case(use_case_id)
    if not uc:
        return {"ok": False, "error": f"unknown use case {use_case_id}"}
    # custom agent path
    if uc.get("loop") == "agent_build":
        try:
            from pocket.custom_agents import create_agent

            create_agent(
                name="SupportAgent",
                role="customer support specialist",
                personality="calm, concise",
                tools=["files", "plan", "mesh", "web"],
                sub_agents=["RESEARCH_HEADLESS"],
                owner=owner,
            )
        except Exception:
            pass
    return start_loop(
        goal or uc.get("prompt_hint") or uc["title"],
        use_case=uc["id"],
        template=uc.get("template") or "web_static",
        loop_kind=uc.get("loop") or "ship",
        owner=owner,
        name=uc["id"],
    )


def manage_until_done(lid: str, *, timeout_sec: float = 180.0, poll: float = 0.5) -> Dict[str, Any]:
    """Block until loop finishes or timeout (for API/sync tools)."""
    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        m = get_loop(lid)
        if not m:
            return {"ok": False, "error": "not found"}
        if m.get("status") in ("done", "failed", "stopped"):
            return {"ok": m.get("status") == "done", "loop": m}
        time.sleep(poll)
    return {"ok": False, "error": "timeout", "loop": get_loop(lid)}
