"""Web research product — search + fetch + research (no API keys required)."""

from __future__ import annotations

import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Tuple

from pocket.safety import allow_url, audit
from pocket.tokenomics import burn

MAX_BYTES = 900_000
UA = "POCKET/1.0 (desktop-agent; +https://pocket.medinatechlabs.net)"


def _strip_html(raw: str) -> str:
    text = re.sub(r"(?is)<script.*?>.*?</script>", " ", raw)
    text = re.sub(r"(?is)<style.*?>.*?</style>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_url(url: str, *, max_chars: int = 14000) -> Dict[str, Any]:
    ok, msg = allow_url(url)
    if not ok:
        return {"ok": False, "error": msg}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,application/json,*/*"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read(MAX_BYTES)
            ctype = r.headers.get("Content-Type", "")
            final = r.geturl()
        text = data.decode("utf-8", errors="replace")
        if "json" in ctype.lower():
            try:
                text = json.dumps(json.loads(text), indent=2)
            except Exception:
                pass
        elif "html" in ctype.lower() or "<html" in text[:300].lower() or text.lstrip().lower().startswith("<!doctype"):
            text = _strip_html(text)
        text = text[:max_chars]
        audit("web_fetch", url=url[:200], bytes=len(data))
        burn("web_fetch", meta={"url": url[:120]}) if "web_fetch" in __import__("pocket.tokenomics", fromlist=["COSTS"]).COSTS else burn("job_ask", meta={"web": "fetch"})
        return {"ok": True, "url": final, "chars": len(text), "content_type": ctype, "text": text, "at": time.time()}
    except Exception as e:
        audit("web_fetch_fail", url=url[:200], error=str(e))
        return {"ok": False, "error": str(e), "url": url}


def search_web(query: str, *, max_results: int = 6) -> Dict[str, Any]:
    """Product search: DuckDuckGo Instant Answer API + Wikipedia OpenSearch."""
    q = (query or "").strip()
    if not q or len(q) > 300:
        return {"ok": False, "error": "query required (max 300 chars)"}

    results: List[Dict[str, str]] = []

    # 1) DuckDuckGo Instant Answer JSON
    try:
        ddg = "https://api.duckduckgo.com/?" + urllib.parse.urlencode(
            {"q": q, "format": "json", "no_html": 1, "skip_disambig": 1}
        )
        ok, _ = allow_url(ddg)
        if ok:
            req = urllib.request.Request(ddg, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8", errors="replace"))
            if data.get("AbstractText"):
                results.append(
                    {
                        "title": data.get("Heading") or "Summary",
                        "url": data.get("AbstractURL") or ddg,
                        "snippet": (data.get("AbstractText") or "")[:400],
                    }
                )
            for t in (data.get("RelatedTopics") or [])[: max_results]:
                if isinstance(t, dict) and t.get("FirstURL"):
                    results.append(
                        {
                            "title": _strip_html(t.get("Text") or t.get("FirstURL"))[:160],
                            "url": t.get("FirstURL"),
                            "snippet": _strip_html(t.get("Text") or "")[:300],
                        }
                    )
                elif isinstance(t, dict) and t.get("Topics"):
                    for tt in t["Topics"][:3]:
                        if tt.get("FirstURL"):
                            results.append(
                                {
                                    "title": _strip_html(tt.get("Text") or "")[:160],
                                    "url": tt.get("FirstURL"),
                                    "snippet": _strip_html(tt.get("Text") or "")[:300],
                                }
                            )
    except Exception:
        pass

    # 2) Wikipedia OpenSearch
    try:
        wiki = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
            {
                "action": "opensearch",
                "search": q,
                "limit": max_results,
                "namespace": 0,
                "format": "json",
            }
        )
        ok, _ = allow_url(wiki)
        if ok:
            req = urllib.request.Request(wiki, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode("utf-8", errors="replace"))
            # [query, titles[], descs[], urls[]]
            if isinstance(data, list) and len(data) >= 4:
                titles, descs, urls = data[1], data[2], data[3]
                for i, title in enumerate(titles):
                    results.append(
                        {
                            "title": title,
                            "url": urls[i] if i < len(urls) else "",
                            "snippet": descs[i] if i < len(descs) else "",
                        }
                    )
    except Exception:
        pass

    # 3) DuckDuckGo HTML lite (product fallback when Instant Answer is empty)
    if len(results) < 2:
        try:
            html_url = "https://html.duckduckgo.com/html/?" + urllib.parse.urlencode({"q": q})
            ok, _ = allow_url(html_url)
            if ok:
                req = urllib.request.Request(
                    html_url,
                    headers={"User-Agent": UA, "Accept": "text/html"},
                )
                with urllib.request.urlopen(req, timeout=25) as r:
                    raw = r.read(MAX_BYTES).decode("utf-8", errors="replace")
                # result links: <a rel="nofollow" class="result__a" href="...">title</a>
                for m in re.finditer(
                    r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                    raw,
                    re.I | re.S,
                ):
                    href, title = m.group(1), _strip_html(m.group(2))
                    # DDG sometimes wraps redirects
                    if "uddg=" in href:
                        try:
                            href = urllib.parse.unquote(
                                re.search(r"uddg=([^&]+)", href).group(1)
                            )
                        except Exception:
                            pass
                    if not href.startswith("http"):
                        continue
                    snip = ""
                    # nearby snippet
                    results.append({"title": title[:160] or href, "url": href, "snippet": snip})
                    if len(results) >= max_results + 4:
                        break
        except Exception:
            pass

    # dedupe by url
    seen = set()
    uniq = []
    for r in results:
        u = r.get("url") or ""
        if not u or u in seen:
            continue
        seen.add(u)
        uniq.append(r)
        if len(uniq) >= max_results:
            break

    audit("web_search", query=q[:200], n=len(uniq))
    try:
        burn("web_search", meta={"q": q[:80]})
    except Exception:
        burn("job_ask", meta={"web": "search"})

    return {"ok": True, "query": q, "results": uniq, "count": len(uniq), "at": time.time()}


def run_web_job(prompt: str) -> Tuple[str, str, str]:
    text = (prompt or "").strip()
    low = text.lower()

    if low.startswith("fetch "):
        res = fetch_url(text[6:].strip())
        if not res.get("ok"):
            return "", res.get("error") or "fetch failed", "web"
        return (
            f"## Fetch\n**URL:** {res.get('url')}\n**chars:** {res.get('chars')}\n\n{res.get('text')}",
            "",
            "web",
        )

    if low.startswith("search "):
        res = search_web(text[7:].strip())
        if not res.get("ok"):
            return "", res.get("error") or "search failed", "web"
        lines = [f"## Search: {res.get('query')}", f"Results: {res.get('count')}", ""]
        for i, r in enumerate(res.get("results") or [], 1):
            lines.append(f"{i}. **{r.get('title')}**\n   {r.get('url')}\n   {r.get('snippet') or ''}")
        if not res.get("results"):
            lines.append("_No results — try a different query._")
        return "\n".join(lines), "", "web"

    if low.startswith("research "):
        q = text[9:].strip()
        s = search_web(q, max_results=4)
        if not s.get("ok"):
            return "", s.get("error") or "search failed", "web"
        lines = [f"## Research: {q}", "", "### Sources"]
        for i, r in enumerate(s.get("results") or [], 1):
            lines.append(f"{i}. {r.get('title')} — {r.get('url')}")
        top = (s.get("results") or [{}])[0].get("url")
        if top:
            f = fetch_url(top, max_chars=7000)
            lines.append("\n### Extract from top source\n")
            lines.append(f.get("text") if f.get("ok") else f"(fetch failed: {f.get('error')})")
        return "\n".join(lines), "", "web"

    return (
        "## Web research (product)\n\n"
        "Commands:\n"
        "- `search <query>` — multi-source search\n"
        "- `fetch https://…` — page text extract\n"
        "- `research <query>` — search + top page extract\n",
        "",
        "web",
    )
