"""Agentic real-world campaigns — task-oriented multi-worker workflows via API.

Not fixed demo scripts. A Campaign is a durable task with phases:
  research → capture evidence (vision/record) → synthesize → distribute (draft only)
Callable only through platform/API so Grok/Codex/phone/UI share one path.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from pocket.live_events import emit

CAMP = Path.home() / ".pocket" / "campaigns"
CAMP.mkdir(parents=True, exist_ok=True)


def _save(c: Dict[str, Any]) -> None:
    (CAMP / f"{c['id']}.json").write_text(json.dumps(c, indent=2, default=str)[:200000], encoding="utf-8")


def list_campaigns(limit: int = 20) -> List[Dict[str, Any]]:
    files = sorted(CAMP.glob("camp-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for f in files[:limit]:
        try:
            out.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


def get_campaign(cid: str) -> Optional[Dict[str, Any]]:
    p = CAMP / f"{cid}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def run_research_campaign(
    topic: str,
    *,
    repos: Optional[List[str]] = None,
    record: bool = True,
    commercial_polish: bool = True,
) -> Dict[str, Any]:
    """Full research campaign with multi-GitHub + vision + commercial capture.

    Uses host_backend so local and VM share the same path.
    Spawns a dynamic worker for live glass exploration (not only skill checklist).
    """
    from pocket.host_backend import get_host
    from pocket.dynamic_worker import spawn_worker
    from pocket.screen_record import record_start, record_stop
    from pocket.vision_core import observe
    from pocket.learn import record_run

    host = get_host()
    cid = f"camp-{uuid.uuid4().hex[:10]}"
    camp: Dict[str, Any] = {
        "id": cid,
        "type": "research_campaign",
        "topic": topic,
        "status": "running",
        "created_at": time.time(),
        "phases": [],
        "artifacts": {},
        "backend": host.kind(),
    }
    _save(camp)
    emit("campaign", f"Start {cid}: {topic[:80]}", agent="CAMPAIGN", role="host")

    # Phase 0 — record commercial-grade capture of real use
    if record:
        rs = record_start(label=f"campaign-{cid[-6:]}")
        camp["phases"].append({"phase": "record_start", "ok": rs.get("ok"), "path": rs.get("path")})
        camp["artifacts"]["recording_start"] = rs.get("path")
        time.sleep(0.8)

    # Phase 1 — multi-repo research (real work, different each call)
    repo_list = repos or []
    if not repo_list:
        try:
            from pocket.repos import list_github_repos

            listed = list_github_repos(5)
            repo_list = [r.get("url") for r in (listed.get("repos") or [])[:3] if r.get("url")]
        except Exception:
            repo_list = []
    if not repo_list:
        repo_list = [
            "https://github.com/FreddyCreates/imagiEngine",
            "https://github.com/FreddyCreates/neuroemergence-core",
        ]

    analyses = []
    for i, url in enumerate(repo_list[:4]):
        emit("campaign", f"Repo {i+1}/{len(repo_list)}: {url}", agent="SCRUTATOR", role="python")
        # Open one page + dynamic explore (agentic, not multi-link spam)
        host.execute_skill("edge_url", prompt=url, params={"url": url})
        time.sleep(1.5)
        dw = spawn_worker(
            f"scroll and explore this github repository page like a user, topic {topic}",
            name=f"SCOUT{i+1}",
            max_steps=5,
            async_=False,
        )
        from pocket.repos import analyze_github_repo

        name = url.rstrip("/").split("/")[-1]
        analysis = analyze_github_repo(name, useful_for=f"POCKET campaign: {topic}")
        analyses.append(
            {
                "url": url,
                "worker": dw.get("worker_id"),
                "worker_steps": dw.get("steps"),
                "analysis_ok": analysis.get("ok"),
                "repo": analysis.get("repo"),
                "recommendations": analysis.get("recommendations"),
                "useful_n": len(analysis.get("useful_files") or []),
            }
        )
        camp["phases"].append({"phase": f"repo_{i+1}", "url": url, "ok": True})
        # vision sample
        obs = observe(with_ui_map=False)
        camp["phases"].append({"phase": f"observe_{i+1}", "titles": (obs.get("window_titles") or [])[:3]})

    camp["artifacts"]["analyses"] = analyses

    # Phase 2 — synthesize brief (no LLM required; structure from analyses)
    lines = [f"# Campaign brief: {topic}", "", f"Backend: {host.kind()}", ""]
    for a in analyses:
        lines.append(f"## {a.get('repo') or a.get('url')}")
        for rec in (a.get("recommendations") or [])[:4]:
            lines.append(f"- {rec}")
        lines.append(f"- useful files: {a.get('useful_n')}")
        lines.append(f"- scout worker steps: {a.get('worker_steps')}")
        lines.append("")
    brief = "\n".join(lines)
    brief_path = CAMP / f"{cid}-brief.md"
    brief_path.write_text(brief, encoding="utf-8")
    camp["artifacts"]["brief"] = str(brief_path)

    # Phase 3 — commercial outputs (drafts only)
    tweet = (
        f"Building in public: multi-repo research campaign on {topic}. "
        f"{len(analyses)} repos scouted via POCKET host workers + vision. "
        f"ItsNotAI Labs."
    )[:270]
    from pocket.browser_mode import open_tweet_compose
    from pocket.outlook_agent import create_draft
    from pocket.skill_runner import notepad_type

    open_tweet_compose(tweet)
    camp["phases"].append({"phase": "tweet_draft", "ok": True})
    create_draft(
        subject=f"POCKET campaign: {topic[:60]}",
        body=brief[:4000] + "\n\n— Generated by POCKET campaign API (TABELLARIUS draft, not sent)\n",
    )
    camp["phases"].append({"phase": "email_draft", "ok": True})
    notepad_type(f"POCKET CAMPAIGN\n{topic}\n\n{brief[:1500]}")
    camp["phases"].append({"phase": "notepad", "ok": True})

    # Phase 4 — polished capture close
    if commercial_polish:
        host.execute_skill("screenshot")
        camp["phases"].append({"phase": "screenshot", "ok": True})

    if record:
        stop = record_stop()
        camp["artifacts"]["recording"] = stop.get("path")
        camp["phases"].append({"phase": "record_stop", "ok": stop.get("ok"), "path": stop.get("path")})

    camp["status"] = "done"
    camp["finished_at"] = time.time()
    camp["message"] = (
        f"Campaign complete · {len(analyses)} repos · brief={brief_path.name} · "
        f"video={camp['artifacts'].get('recording')}"
    )
    _save(camp)
    record_run(
        name=f"campaign_{topic[:40]}",
        steps=camp["phases"],
        notes=brief[:500],
        worker="CAMPAIGN",
    )
    emit("campaign", camp["message"], agent="CAMPAIGN", role="host")
    return camp
