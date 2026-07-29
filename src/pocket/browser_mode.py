"""Browser mode — Codex/Grok + real desktop/browser (production).

Separate desk box from pure coding sessions. The agent can:
  · look up topics (Python evidence + open Edge/Copilot)
  · open signed-in Edge profiles (your X session stays logged in)
  · compose an X post and open the compose/intent URL ready to publish
  · open Windows Copilot app and web Copilot
  · emit [[POCKET …]] action tags that this host executes for real

Safety: allowlisted apps + http(s) only. Tweet text is pre-filled; user still hits Post.
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

from pocket.live_events import emit

MAX_TWEET = 280
TAG_RE = re.compile(
    r"\[\[POCKET\s+([^\]]+)\]\]",
    re.I,
)

HELP = """# Browser mode — real-world desk (ItsNotAI Labs / Medina Tech Labs)

You are in a **Browser** session: coding engines + host browser/desktop.

## What works

| Command / pattern | Effect |
|-------------------|--------|
| `help` | This help |
| `lookup <topic>` | Python search + open Edge/Bing + optional Windows Copilot |
| `tweet <text>` | Open X compose (signed-in Edge) with text ready |
| `tweet <text> to https://x.com/...` | Same + open your page |
| `open x` / `open twitter` | Open x.com home in Edge |
| `open copilot` | **Windows** Copilot app (`ms-copilot:`) |
| `open copilot web` | Web Copilot in Edge |
| `open edge https://…` | Edge with your Default profile (signed-in sites) |
| Multi-step with `then` | Up to 10 Python worker steps |
| Freeform with Codex/Grok | Engine composes; host runs `[[POCKET …]]` tags |
| `screenshot` | Capture screen → paste-back (no folder) |
| `open my 5 repos` | GitHub via `gh` + Edge |
| `introduce` (Copilot session) | Windows Copilot intro agent |

## Who does what (named agents)

| Agent | Role |
|-------|------|
| **Browser Orchestrator** | Intent detect, step order |
| **Research Worker** (Python) | `lookup` / web search / fetch |
| **Composer** (Codex or Grok LLM) | Draft tweet / tags |
| **Edge Host Worker** (Python) | Signed-in Edge, X intent, clipboard |
| **Live Event Bus** | Streams actions to desk rail |

## X / tweet flow (production)

1. You: `look up AI agents then write a tweet for my page https://x.com/ItsnotAILabs`
2. **Python** researches + opens evidence UI
3. **LLM (Codex/Grok)** drafts ≤280 chars
4. **Python** opens Edge (your profile) on intent URL + clipboard
5. **You click Post** — POCKET does not auto-publish
6. Live rail shows each step as it happens

## Agent tags (Codex/Grok may emit)

```
[[POCKET open edge https://example.com]]
[[POCKET open copilot]]
[[POCKET open copilot web]]
[[POCKET lookup multi-agent platforms]]
[[POCKET tweet Hello world from POCKET]]
[[POCKET open x]]
[[POCKET open explorer]]
```

Tags are executed on this PC after the model returns.
"""


def _edge_exe() -> str:
    from pocket.desktop import _resolve_cmd

    resolved, _ = _resolve_cmd("edge", "msedge")
    return resolved


def open_edge_url(
    url: str,
    *,
    profile: str = "Default",
    new_window: bool = False,
) -> Dict[str, Any]:
    """Open URL in Edge using the user profile so X/etc stay signed in."""
    from pocket.safety import allow_url, audit
    from pocket.tokenomics import burn
    import os
    import subprocess

    u = (url or "").strip()
    if not u.startswith("http://") and not u.startswith("https://"):
        if u.startswith("ms-") or ":" in u[:20]:
            # protocol handler
            try:
                subprocess.Popen(["cmd", "/c", "start", "", u], shell=False)
                return {"ok": True, "url": u, "kind": "protocol", "message": f"Opened {u}"}
            except Exception as e:
                return {"ok": False, "error": str(e)}
        return {"ok": False, "error": "URL must be http(s)"}
    ok, msg = allow_url(u)
    if not ok:
        return {"ok": False, "error": msg}

    exe = _edge_exe()
    missing = (not exe) or ("\\" in str(exe) and not os.path.isfile(exe))
    if missing:
        from pocket.desktop import open_app

        return open_app("edge", args=u)

    argv = [exe]
    if profile:
        argv.append(f"--profile-directory={profile}")
    if new_window:
        argv.append("--new-window")
    argv.append(u)
    try:
        emit("edge", f"Opening Edge ({profile}): {u[:100]}", agent="edge_host", role="python", meta={"url": u[:200]})
        subprocess.Popen(argv, cwd=os.path.expanduser("~"), shell=False)
        audit("browser_edge", url=u[:200], profile=profile)
        try:
            burn("desktop_open", meta={"app": "edge", "browser_mode": True})
        except Exception:
            pass
        return {
            "ok": True,
            "url": u,
            "profile": profile,
            "exe": exe,
            "argv": argv,
            "message": f"Opened Edge ({profile}): {u[:80]}",
            "at": time.time(),
        }
    except Exception as e:
        from pocket.desktop import open_app

        fb = open_app("edge", args=u)
        fb["fallback"] = str(e)
        return fb


def open_windows_copilot(*, query: str = "") -> Dict[str, Any]:
    """Open the **Windows** Copilot app (not web). Query is best-effort via Bing if needed."""
    import os
    import subprocess

    results: List[Dict[str, Any]] = []
    # Primary: URI scheme
    for proto in ("ms-copilot:", "ms-copilot://", "ms-windows-ai-studio:"):
        try:
            subprocess.Popen(["cmd", "/c", "start", "", proto], shell=False)
            results.append({"ok": True, "via": proto})
            break
        except Exception as e:
            results.append({"ok": False, "via": proto, "error": str(e)})

    # Windows 11 often: explorer shell:AppsFolder\… or start Microsoft.Copilot
    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-Command", "Start-Process 'ms-copilot:'"],
            shell=False,
        )
        results.append({"ok": True, "via": "powershell-ms-copilot"})
    except Exception as e:
        results.append({"ok": False, "via": "powershell", "error": str(e)})

    # If user gave a query, also park it in Bing chat for the web surface (next hop)
    web = None
    if query.strip():
        web = open_web_copilot(query.strip())

    ok = any(r.get("ok") for r in results)
    return {
        "ok": ok,
        "kind": "windows_copilot",
        "query": query,
        "launches": results,
        "web_copilot": web,
        "message": "Opened Windows Copilot app"
        + (f" + web assist for query" if query else ""),
    }


def open_web_copilot(query: str = "") -> Dict[str, Any]:
    """Web Copilot / Bing chat in Edge (signed-in profile)."""
    q = (query or "").strip()
    if q:
        url = "https://www.bing.com/chat?" + urllib.parse.urlencode({"q": q})
        # also copilot.microsoft.com
        alt = "https://copilot.microsoft.com/?" + urllib.parse.urlencode({"q": q})
    else:
        url = "https://copilot.microsoft.com/"
        alt = "https://www.bing.com/chat"
    r1 = open_edge_url(url)
    # don't open two windows always — only primary
    return {"ok": r1.get("ok"), "url": url, "alt": alt, "edge": r1, "kind": "web_copilot"}


def open_x_home() -> Dict[str, Any]:
    return open_edge_url("https://x.com/home")


def open_x_profile(url_or_handle: str) -> Dict[str, Any]:
    raw = (url_or_handle or "").strip()
    if raw.startswith("http"):
        return open_edge_url(raw)
    handle = raw.lstrip("@")
    return open_edge_url(f"https://x.com/{handle}")


def open_tweet_compose(
    text: str,
    *,
    profile_url: str = "",
) -> Dict[str, Any]:
    """Open X intent compose with prefilled text (user is signed in via Edge profile)."""
    t = (text or "").strip()
    if len(t) > MAX_TWEET:
        t = t[: MAX_TWEET - 1] + "…"
    # intent/tweet works when logged into X in that browser
    intent = "https://twitter.com/intent/tweet?" + urllib.parse.urlencode({"text": t})
    # modern compose
    compose = "https://x.com/compose/post"
    emit("tweet", f"Opening X compose ({len(t)} chars)…", agent="edge_host", role="python")
    r = open_edge_url(intent)
    out: Dict[str, Any] = {
        "ok": r.get("ok"),
        "kind": "tweet_compose",
        "text": t,
        "chars": len(t),
        "intent_url": intent,
        "compose_url": compose,
        "edge": r,
        "message": f"Opened X compose with {len(t)} chars — review and click Post",
        "note": "POCKET never auto-publishes. You confirm in the browser.",
    }
    if profile_url:
        # also open profile so user sees their page
        out["profile"] = open_edge_url(profile_url)
    # clipboard for convenience
    try:
        import subprocess

        subprocess.run(
            ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value @'\n{t}\n'@"],
            capture_output=True,
            timeout=8,
        )
        out["clipboard"] = True
    except Exception:
        out["clipboard"] = False
    return out


def execute_pocket_tag(body: str) -> Dict[str, Any]:
    """Execute one [[POCKET …]] body string."""
    body = (body or "").strip()
    low = body.lower()

    if low.startswith("open edge "):
        return open_edge_url(body[10:].strip())
    if low in ("open x", "open twitter", "open x.com"):
        return open_x_home()
    if low.startswith("open x ") or low.startswith("open twitter "):
        rest = body.split(None, 2)[-1] if " " in body else ""
        return open_x_profile(rest)
    if low in ("open copilot", "open windows copilot", "copilot"):
        return open_windows_copilot()
    if low.startswith("open copilot "):
        rest = body[13:].strip()
        if rest.lower() in ("web", "bing", "online"):
            return open_web_copilot()
        return open_windows_copilot(query=rest)
    if low.startswith("open copilot web"):
        q = body[16:].strip() if len(body) > 16 else ""
        return open_web_copilot(q)
    if low.startswith("lookup "):
        from pocket.step_agent import _lookup_and_bring_back

        return _lookup_and_bring_back(body[7:].strip(), open_ui=True)
    if low.startswith("tweet "):
        return open_tweet_compose(body[6:].strip())
    if low.startswith("open "):
        app = body[5:].strip().split()[0]
        from pocket.desktop import open_app

        return open_app(app)
    return {"ok": False, "error": f"unknown POCKET tag: {body[:80]}"}


def execute_all_tags(text: str) -> List[Dict[str, Any]]:
    actions = []
    for m in TAG_RE.finditer(text or ""):
        actions.append({"tag": m.group(0), **execute_pocket_tag(m.group(1))})
    return actions


def _extract_tweet_text(model_out: str) -> str:
    """Pull a likely tweet from model output."""
    t = (model_out or "").strip()
    m = re.search(r"(?:^|\n)\s*TWEET:\s*(.+)", t, re.I)
    if m:
        return m.group(1).strip().strip('"').strip("'")[:MAX_TWEET]
    m = re.search(r"```(?:tweet|text)?\s*\n(.*?)```", t, re.S | re.I)
    if m:
        return m.group(1).strip()[:MAX_TWEET]
    for para in re.split(r"\n\s*\n", t):
        p = para.strip().strip('"').strip("'")
        if not p or p.startswith("#") or p.lower().startswith("engine"):
            continue
        if "[[pocket" in p.lower():
            continue
        if 10 <= len(p) <= MAX_TWEET:
            return p[:MAX_TWEET]
    clean = re.sub(r"\[\[POCKET[^\]]*\]\]", "", t)
    clean = re.sub(r"^#+\s.*$", "", clean, flags=re.M).strip()
    return clean[:MAX_TWEET]


def _detect_intent(prompt: str) -> Dict[str, Any]:
    p = (prompt or "").strip()
    low = p.lower()
    intent: Dict[str, Any] = {
        "kind": "general",
        "query": "",
        "tweet_hint": "",
        "x_url": "",
        "engine": "auto",
        "raw": p,
    }
    # engine override
    if low.startswith("engine:codex") or low.startswith("use codex"):
        intent["engine"] = "codex"
    elif low.startswith("engine:grok") or low.startswith("use grok"):
        intent["engine"] = "grok"
    elif low.startswith("engine:python") or low.startswith("no llm"):
        intent["engine"] = "python"

    # X URL in prompt
    m = re.search(r"https?://(?:www\.)?(?:x|twitter)\.com/[^\s]+", p, re.I)
    if m:
        intent["x_url"] = m.group(0).rstrip(").,]")

    if low in ("help", "?", "commands"):
        intent["kind"] = "help"
        return intent

    if low.startswith("tweet ") or low.startswith("post "):
        intent["kind"] = "tweet_only"
        intent["tweet_hint"] = re.sub(r"^(tweet|post)\s+", "", p, flags=re.I).strip()
        # strip trailing "to https…"
        intent["tweet_hint"] = re.sub(
            r"\s+to\s+https?://\S+", "", intent["tweet_hint"], flags=re.I
        ).strip()
        return intent

    if "tweet" in low or "x.com" in low or "twitter" in low or "post to my" in low:
        intent["kind"] = "research_tweet"
        q = re.sub(r"https?://\S+", "", p)
        # pull topic after look up / research / about
        mtopic = re.search(
            r"(?:look\s*up|lookup|research|about|regarding)\s+(.+?)(?:\s+then\s+|\s+and\s+write|\s+and\s+draft|\s+for\s+my|\s+to\s+my|$)",
            q,
            re.I,
        )
        if mtopic:
            q = mtopic.group(1)
        else:
            q = re.sub(
                r"\b(write|draft|make|post|tweet|to my|x page|twitter|page|link|look up|lookup|then)\b",
                " ",
                q,
                flags=re.I,
            )
        q = re.sub(r"\s+", " ", q).strip(" .")
        intent["query"] = q or "latest AI news"
        return intent

    if low.startswith("lookup ") or low.startswith("look up ") or low.startswith("research "):
        intent["kind"] = "lookup"
        intent["query"] = re.sub(r"^(lookup|look up|research)\s+", "", p, flags=re.I).strip()
        return intent

    if low.startswith("open "):
        intent["kind"] = "open"
        return intent

    if " then " in low or "\n" in p:
        intent["kind"] = "multistep"
        return intent

    # default freeform → use LLM + tags
    intent["kind"] = "freeform"
    intent["query"] = p
    return intent


def _compose_with_engine(
    instruction: str,
    cwd: str,
    job: Optional[Dict],
    engine: str,
    job_id: str = "",
) -> Tuple[str, str, str]:
    """Run Codex or Grok to compose content / plan browser tags."""
    from pocket.executor import which_codex, which_grok_cli, _run_codex, _run_grok_agent, _run_claude

    system = (
        "You are POCKET Browser mode. You work in the REAL world via host actions.\n"
        "After your answer, emit zero or more action tags on their own lines:\n"
        "[[POCKET open edge https://...]]\n"
        "[[POCKET open copilot]]\n"
        "[[POCKET open copilot web]]\n"
        "[[POCKET lookup your query]]\n"
        "[[POCKET tweet your tweet text under 280 chars]]\n"
        "[[POCKET open x]]\n"
        "For tweets: put the final post as: TWEET: <text>\n"
        "Do not claim you already posted. Host opens compose; human clicks Post.\n"
    )
    full = system + "\nUser request:\n" + instruction
    eng = (engine or "auto").lower()
    if eng == "auto":
        eng = "codex" if which_codex() else ("grok" if which_grok_cli() else "python")
    if eng == "codex" and which_codex():
        return _run_codex(full, cwd, job_id=job_id, job=job or {})
    if eng == "grok" and which_grok_cli():
        return _run_grok_agent(full, cwd, job_id=job_id)
    if eng == "claude":
        return _run_claude(full, cwd, job_id=job_id)
    # python-only: no model
    return (
        "TWEET: " + instruction[:240] + "\n[[POCKET lookup " + instruction[:80] + "]]\n",
        "",
        "python",
    )


def run_browser_job(
    prompt: str,
    *,
    cwd: str = "",
    job: Optional[Dict[str, Any]] = None,
) -> Tuple[str, str, str]:
    """Main entry for mode=browser."""
    job = job or {}
    jid = job.get("id") or ""
    sid = (job.get("session_id") or "")
    emit(
        "browser",
        f"Browser job start: {(prompt or '')[:120]}",
        agent="browser_orchestrator",
        role="host",
        session_id=sid,
        job_id=jid,
    )
    intent = _detect_intent(prompt)
    engine = intent.get("engine") or job.get("browser_engine") or "auto"
    actions: List[Dict[str, Any]] = []
    parts: List[str] = [
        f"## Browser mode · engine={engine}",
        f"**Intent:** `{intent['kind']}`",
        f"**Agents:** browser_orchestrator · research_worker · composer(LLM) · edge_host",
        "",
    ]

    low_full = (prompt or "").strip().lower()
    if low_full in ("screenshot", "capture", "shot"):
        from pocket.capture import run_capture_job

        return run_capture_job(prompt)
    if low_full in ("open my 5 repos", "open github", "open my repos", "list repos"):
        from pocket.repos import run_repos_job

        return run_repos_job(prompt)

    if intent["kind"] == "help":
        return HELP, "", "browser"

    if intent["kind"] == "open":
        # reuse step agent / desktop
        low = prompt.lower().strip()
        if low in ("open copilot", "open windows copilot"):
            r = open_windows_copilot()
        elif low.startswith("open copilot web"):
            r = open_web_copilot(prompt[16:].strip() if len(prompt) > 16 else "")
        elif low.startswith("open edge "):
            r = open_edge_url(prompt[10:].strip())
        elif low in ("open x", "open twitter"):
            r = open_x_home()
        else:
            from pocket.desktop import run_desktop_job

            text, err, eng = run_desktop_job(prompt)
            return f"## Browser mode · open\n\n{text}", err, "browser"
        actions.append(r)
        parts.append("### Actions")
        parts.append(f"```json\n{json.dumps(r, indent=2, default=str)[:4000]}\n```")
        return "\n".join(parts), "" if r.get("ok") else (r.get("error") or "open failed"), "browser"

    if intent["kind"] == "lookup":
        from pocket.step_agent import _lookup_and_bring_back

        emit("research", f"Lookup: {intent['query']}", agent="research_worker", role="python", session_id=sid)
        r = _lookup_and_bring_back(intent["query"], open_ui=True)
        actions.append(r)
        parts.append(f"### Lookup: {intent['query']}")
        parts.append(r.get("brief") or r.get("message") or "")
        if r.get("error"):
            parts.append(f"**Error:** {r['error']}")
        return "\n".join(parts), "" if r.get("ok") else (r.get("error") or "lookup failed"), "browser"

    if intent["kind"] == "tweet_only":
        text = intent.get("tweet_hint") or ""
        # if looks like a topic not final text, compose
        if len(text) > 200 or " about " in text.lower() or "write" in text.lower():
            model_out, err, eng = _compose_with_engine(
                f"Write ONE tweet (≤280 chars) for: {text}\nOutput TWEET: line only plus optional tags.",
                cwd,
                job,
                engine,
                job_id=jid,
            )
            parts.append(f"### Composer ({eng})\n\n{model_out[-8000:]}")
            text = _extract_tweet_text(model_out)
            tag_acts = execute_all_tags(model_out)
            actions.extend(tag_acts)
        r = open_tweet_compose(text, profile_url=intent.get("x_url") or "")
        actions.append(r)
        parts.append(f"### Tweet ready ({r.get('chars')} chars)\n\n> {r.get('text')}\n")
        parts.append(r.get("message") or "")
        parts.append(f"\n```json\n{json.dumps({'intent_url': r.get('intent_url'), 'ok': r.get('ok')}, indent=2)}\n```")
        return "\n".join(parts), "" if r.get("ok") else (r.get("error") or "tweet open failed"), "browser"

    if intent["kind"] == "research_tweet":
        from pocket.step_agent import _lookup_and_bring_back

        q = intent.get("query") or "news"
        parts.append(f"### 1. Research (Python · research_worker): {q}")
        emit("research", f"Research for tweet: {q}", agent="research_worker", role="python", session_id=sid)
        research = _lookup_and_bring_back(q, open_ui=True)
        actions.append(research)
        brief = research.get("brief") or ""
        parts.append(brief[:3000] if brief else research.get("message", ""))

        emit("compose", f"LLM compose tweet via {engine}", agent="composer", role="llm", session_id=sid)
        compose_prompt = (
            f"Topic research:\n{brief[:3500]}\n\n"
            f"User asked: {prompt}\n"
            f"Write ONE sharp X/Twitter post ≤280 characters. "
            f"No hashtag spam. Optional one emoji max.\n"
            f"Output exactly:\nTWEET: <text>\n"
            f"Then emit: [[POCKET tweet <same text>]]\n"
            f"If profile URL known: also [[POCKET open edge {intent.get('x_url') or 'https://x.com/home'}]]\n"
        )
        model_out, err, eng = _compose_with_engine(compose_prompt, cwd, job, engine, job_id=jid)
        parts.append(f"\n### 2. Compose (LLM · {eng})\n\n{model_out[-6000:]}")
        if err:
            parts.append(f"_(composer warning: {err})_")

        tweet = _extract_tweet_text(model_out)
        tag_acts = execute_all_tags(model_out)
        actions.extend(tag_acts)
        # Always open compose even if model forgot tag
        if not any(a.get("kind") == "tweet_compose" for a in tag_acts):
            emit("tweet", "Python opening X intent (signed-in Edge)", agent="edge_host", role="python", session_id=sid)
            r = open_tweet_compose(tweet, profile_url=intent.get("x_url") or "")
            actions.append(r)
            parts.append(f"\n### 3. Opened X compose (Python · edge_host)\n\n> {tweet}\n\n{r.get('message')}")
        else:
            parts.append(f"\n### 3. X compose via tags\n\n> {tweet}")

        parts.append("\n### Who did what")
        parts.append("| Step | Agent | Role |")
        parts.append("|------|-------|------|")
        parts.append("| Research | research_worker | **Python** (no LLM tokens) |")
        parts.append(f"| Draft tweet | composer | **LLM ({eng})** |")
        parts.append("| Open Edge + paste intent | edge_host | **Python** |")
        parts.append("| Click Post | you | **Human** |")
        parts.append("\n### Action log")
        for a in actions[-8:]:
            parts.append(f"- ok={a.get('ok')} kind={a.get('kind') or a.get('tag', '')[:40]} {a.get('message') or a.get('error') or ''}")
        emit("browser", "Browser research_tweet flow complete", agent="browser_orchestrator", role="host", session_id=sid)
        return "\n".join(parts), "", "browser"

    if intent["kind"] == "multistep":
        from pocket.step_agent import run_step_agent

        text, err, eng = run_step_agent(prompt, cwd=cwd, job=job, max_steps=10)
        return f"## Browser mode · multi-step\n\n{text}", err, "browser"

    # freeform: model + execute tags; also run direct opens if no tags
    model_out, err, eng = _compose_with_engine(prompt, cwd, job, engine, job_id=jid)
    parts.append(f"### Agent ({eng})\n\n{model_out[-12000:]}")
    tag_acts = execute_all_tags(model_out)
    if not tag_acts:
        # heuristic assists
        if "copilot" in prompt.lower():
            if "web" in prompt.lower():
                tag_acts.append(open_web_copilot(re.sub(r".*copilot\s*web\s*", "", prompt, flags=re.I)[:120]))
            else:
                tag_acts.append(open_windows_copilot(query=prompt[:120]))
        if re.search(r"https?://", prompt):
            for u in re.findall(r"https?://[^\s]+", prompt)[:3]:
                tag_acts.append(open_edge_url(u.rstrip(").,]")))
    actions.extend(tag_acts)
    if tag_acts:
        parts.append("\n### Host actions executed")
        for a in tag_acts:
            parts.append(
                f"- **{'OK' if a.get('ok') else 'FAIL'}** "
                f"{a.get('kind') or a.get('tag', '')}: "
                f"{a.get('message') or a.get('error') or a.get('url') or ''}"
            )
    else:
        parts.append("\n_No host actions (model did not emit tags; add `[[POCKET …]]` or use presets)._")
    if err:
        return "\n".join(parts), err, "browser"
    return "\n".join(parts), "", "browser"
