"""Headless multi-step doer — silent Python agent, up to 10 steps.

Does not ask the user questions. Parses a plan and executes allowlisted actions
sequentially. Edge+URL is already 2 internal launch steps.

Also: lookup / copilot lookup — open the host app AND bring Python web results
back (no LLM tokens on the worker path).
"""

from __future__ import annotations

import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

MAX_STEPS = 10

_SPLIT_RE = re.compile(
    r"\s*(?:then|next|after that|and then|;|\n|\r\n)\s*",
    re.I,
)


def parse_steps(prompt: str, *, max_steps: int = MAX_STEPS) -> List[str]:
    """Turn free text into at most max_steps action lines."""
    text = (prompt or "").strip()
    if not text:
        return []

    low = text.lower()
    for prefix in (
        "do:",
        "doer:",
        "steps:",
        "run:",
        "agent:",
        "execute:",
        "guppy:",
        "guppy ",
    ):
        if low.startswith(prefix):
            text = text[len(prefix) :].strip()
            low = text.lower()
            break

    lines = []
    for raw in re.split(r"[\r\n]+", text):
        line = raw.strip()
        if not line:
            continue
        line = re.sub(r"^(?:step\s*)?\d+[\).\:\-]\s*", "", line, flags=re.I)
        line = re.sub(r"^[\-\*\u2022]\s*", "", line)
        if line:
            lines.append(line)

    if len(lines) >= 2:
        steps = lines
    else:
        chunk = lines[0] if lines else text
        parts = [p.strip() for p in _SPLIT_RE.split(chunk) if p and p.strip()]
        steps = parts if len(parts) > 1 else [chunk]

    out: List[str] = []
    for s in steps[:max_steps]:
        s = s.strip().strip('"').strip("'")
        if not s:
            continue
        low = s.lower()
        if low.startswith(
            (
                "open ",
                "list",
                "lookup ",
                "look up ",
                "search ",
                "fetch ",
                "research ",
                "copilot ",
                "shell ",
                "cmd ",
                "schedule ",
            )
        ):
            out.append(s)
        elif re.match(r"https?://", s, re.I):
            out.append(f"open edge {s}")
        elif low in ("help", "?", "what can you do"):
            out.append("help")
        else:
            if " " not in s and re.match(r"^[a-z0-9_\-]+$", low):
                out.append(f"open {low}")
            else:
                # bare query → lookup
                out.append(f"lookup {s}")
    return out[:max_steps]


def _lookup_and_bring_back(query: str, *, open_ui: bool = True) -> Dict[str, Any]:
    """Open Copilot/Bing on the host + Python search results (zero LLM tokens)."""
    q = (query or "").strip()
    t0 = time.time()
    opened = None
    if open_ui and q:
        from pocket.desktop import open_app

        # Bing chat / Copilot-style surface in Edge + native Copilot if present
        bing = "https://www.bing.com/search?" + urllib.parse.urlencode(
            {"q": q, "showconv": "1"}
        )
        opened = open_app("edge", args=bing)
        try:
            open_app("copilot")
        except Exception:
            pass

    from pocket.web_research import search_web, fetch_url

    search = search_web(q, max_results=8) if q else {"ok": False, "error": "empty query"}
    snippets: List[str] = []
    if search.get("ok"):
        for r in (search.get("results") or [])[:6]:
            snippets.append(
                f"- **{r.get('title') or 'result'}** — {r.get('snippet') or ''}\n  {r.get('url') or ''}"
            )
        # Optionally deepen first URL
        first_url = None
        for r in search.get("results") or []:
            if r.get("url") and str(r["url"]).startswith("http"):
                first_url = r["url"]
                break
        deep = None
        if first_url:
            deep = fetch_url(first_url, max_chars=4000)
        return {
            "ok": True,
            "kind": "lookup",
            "query": q,
            "opened_ui": opened,
            "search": search,
            "deep_fetch": deep,
            "brief": "\n".join(snippets) if snippets else "(no snippets)",
            "ms": int((time.time() - t0) * 1000),
            "token_path": "python-worker",
            "message": f"Opened host UI for lookup + brought Python results back for: {q}",
        }
    return {
        "ok": False,
        "kind": "lookup",
        "query": q,
        "opened_ui": opened,
        "error": search.get("error") or "search failed",
        "ms": int((time.time() - t0) * 1000),
    }


def _run_one_step(step: str, *, cwd: str = "") -> Dict[str, Any]:
    low = step.lower().strip()
    t0 = time.time()

    if low in ("help", "list", "list steps", "list apps", "apps"):
        from pocket.desktop import list_apps

        apps = list_apps()
        native = [a for a in apps if a.get("group") == "native"]
        third = [a for a in apps if a.get("group") == "third_party"]
        return {
            "ok": True,
            "step": step,
            "kind": "help",
            "ms": int((time.time() - t0) * 1000),
            "message": (
                f"Headless doer / Guppy: up to {MAX_STEPS} steps, no chat. "
                f"Apps: {len(apps)} ({len(native)} native + {len(third)} third-party). "
                "lookup <q> opens Copilot/Bing + returns Python search. "
                "schedule daily … for autonomous background."
            ),
            "apps_sample": [a["id"] for a in apps[:16]],
        }

    # lookup / look up / copilot <query>
    if low.startswith("lookup ") or low.startswith("look up ") or low.startswith("copilot "):
        if low.startswith("look up "):
            q = step[8:].strip()
        elif low.startswith("lookup "):
            q = step[7:].strip()
        else:
            q = step[8:].strip()
        r = _lookup_and_bring_back(q, open_ui=True)
        r["step"] = step
        r["index"] = None
        return r

    if low in ("screenshot", "capture", "shot", "snip", "snipping tool"):
        from pocket.capture import run_capture_job

        result, error, engine = run_capture_job(step)
        return {
            "ok": not bool(error),
            "step": step,
            "kind": "capture",
            "engine": engine,
            "ms": int((time.time() - t0) * 1000),
            "result": (result or "")[:120000],
            "error": error or "",
        }

    if low in ("open my 5 repos", "list repos", "open github", "gh status") or low.startswith("new repo ") or low.startswith("new folder "):
        from pocket.repos import run_repos_job

        result, error, engine = run_repos_job(step)
        return {
            "ok": not bool(error),
            "step": step,
            "kind": "repos",
            "engine": engine,
            "ms": int((time.time() - t0) * 1000),
            "result": (result or "")[:8000],
            "error": error or "",
        }

    if low.startswith("open ") or low.startswith("list"):
        # open copilot with trailing query → lookup path
        if low.startswith("open copilot ") and len(step) > 13:
            q = step[13:].strip()
            r = _lookup_and_bring_back(q, open_ui=True)
            r["step"] = step
            return r
        from pocket.desktop import run_desktop_job

        # Prevent re-entrancy into multi-step: only single commands here
        result, error, engine = run_desktop_job(step if " then " not in low else step.split(" then ")[0])
        return {
            "ok": not bool(error),
            "step": step,
            "kind": "desktop",
            "engine": engine,
            "ms": int((time.time() - t0) * 1000),
            "result": (result or "")[:4000],
            "error": error or "",
        }

    if low.startswith("shell ") or low.startswith("cmd "):
        from pocket.executor import _run_shell
        from pocket.safety import allow_shell

        cmd = step.split(None, 1)[1] if " " in step else ""
        ok, msg = allow_shell(cmd)
        if not ok:
            return {"ok": False, "step": step, "kind": "shell", "error": msg, "ms": 0}
        out, err, eng = _run_shell(cmd, cwd or "", job_id="")
        return {
            "ok": not bool(err),
            "step": step,
            "kind": "shell",
            "engine": eng,
            "ms": int((time.time() - t0) * 1000),
            "result": (out or "")[:4000],
            "error": err or "",
        }

    if low.startswith("fetch ") or low.startswith("search ") or low.startswith("research "):
        from pocket.web_research import run_web_job

        result, error, engine = run_web_job(step)
        return {
            "ok": not bool(error),
            "step": step,
            "kind": "web",
            "engine": engine,
            "ms": int((time.time() - t0) * 1000),
            "result": (result or "")[:4000],
            "error": error or "",
        }

    if low.startswith("schedule "):
        from pocket.autonomy import handle_schedule_command

        result, error, engine = handle_schedule_command(step)
        return {
            "ok": not bool(error),
            "step": step,
            "kind": "schedule",
            "engine": engine,
            "ms": int((time.time() - t0) * 1000),
            "result": (result or "")[:4000],
            "error": error or "",
        }

    return {
        "ok": False,
        "step": step,
        "kind": "unknown",
        "error": (
            f"Unknown step. Use: open <app> · lookup <q> · research/search/fetch · "
            f"schedule daily … · shell <cmd>. Max {MAX_STEPS} steps."
        ),
        "ms": 0,
    }


def run_step_agent(
    prompt: str,
    *,
    cwd: str = "",
    job: Optional[Dict[str, Any]] = None,
    max_steps: int = MAX_STEPS,
) -> Tuple[str, str, str]:
    """Run up to max_steps silently. Returns (markdown, error, engine)."""
    cap = min(int(max_steps or MAX_STEPS), MAX_STEPS)
    steps = parse_steps(prompt, max_steps=cap)
    if not steps:
        return (
            f"## Headless doer / Guppy\n\nNo steps parsed. Max {cap}.\n\n"
            "Examples:\n"
            "- `open edge https://example.com`  _(launch + URL)_\n"
            "- `lookup multi-agent desktop platforms`  _(Copilot/Bing open + Python results)_\n"
            "- `open edge https://x.com then open notepad then lookup AI news`\n"
            "- `schedule daily lookup market brief`\n",
            "no steps",
            "agent",
        )

    results: List[Dict[str, Any]] = []
    for i, step in enumerate(steps, 1):
        r = _run_one_step(step, cwd=cwd)
        r["index"] = i
        results.append(r)
        if not r.get("ok") and r.get("kind") not in ("help",):
            break

    ok_n = sum(1 for r in results if r.get("ok"))
    fail_n = len(results) - ok_n
    lines = [
        f"## Headless doer · {ok_n}/{len(results)} ok · max {cap} steps · python-worker",
        "",
        f"**Plan ({len(steps)} step(s)):**",
    ]
    for i, s in enumerate(steps, 1):
        mark = "✓" if i <= len(results) and results[i - 1].get("ok") else ("·" if i > len(results) else "✗")
        lines.append(f"{i}. [{mark}] `{s}`")
    lines.append("")
    lines.append("### Results")
    for r in results:
        st = "OK" if r.get("ok") else "FAIL"
        lines.append(f"\n#### Step {r.get('index')} · {st} · {r.get('kind')} · {r.get('ms', 0)}ms")
        lines.append(f"Command: `{r.get('step')}`")
        if r.get("message"):
            lines.append(r["message"])
        if r.get("brief"):
            lines.append("\n**Brought back:**\n")
            lines.append(r["brief"])
        if r.get("deep_fetch") and isinstance(r["deep_fetch"], dict) and r["deep_fetch"].get("text"):
            lines.append("\n**Deep fetch (first source):**\n```")
            lines.append(str(r["deep_fetch"]["text"])[:2000])
            lines.append("```")
        if r.get("result"):
            lines.append("```")
            lines.append(str(r["result"])[:2500])
            lines.append("```")
        if r.get("error"):
            lines.append(f"**Error:** {r['error']}")

    try:
        from pocket.tokenomics import burn

        # Cheap worker burn only — not LLM token path
        burn("job_shell", meta={"agent": "doer", "steps": len(results), "path": "python-worker"})
    except Exception:
        pass

    err = "" if fail_n == 0 else f"{fail_n} step(s) failed"
    return "\n".join(lines), err, "agent"
