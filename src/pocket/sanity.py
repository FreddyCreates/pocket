"""Sanity guards — research-spec risk controls for Fusion Sense / act paths.

Implements HITL-style thresholds from AIS / Fusion-Sense papers:
  · Prefer fusion symbol matches over hallucinated clicks
  · Block vague system-level destructive acts without explicit allow
  · Score-style confidence for agents
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


DESTRUCTIVE = frozenset({
    "close_window", "format", "delete", "rm ", "shutdown", "reboot",
    "drop ", "remove-item", "del ", "erase",
})


def score_symbol_match(query: str, hits: List[Dict[str, Any]]) -> float:
    if not hits or not query:
        return 0.0
    q = query.lower().strip()
    best = 0.0
    for h in hits:
        t = (h.get("text") or "").lower()
        if not t:
            continue
        if t == q:
            best = max(best, 1.0)
        elif q in t or t in q:
            best = max(best, 0.85)
        elif any(w in t for w in q.split() if len(w) > 3):
            best = max(best, 0.65)
    return best


def guard_click(query: str, *, min_score: float = 0.65) -> Dict[str, Any]:
    """Fusion-first click with confidence gate (85% paper threshold ≈ 0.85 strict)."""
    from pocket.perception import find_symbol, act_on_symbol

    hits = find_symbol(query)
    score = score_symbol_match(query, hits)
    if score < min_score:
        return {
            "ok": False,
            "blocked": True,
            "reason": "sanity_guard_low_confidence",
            "score": score,
            "min_score": min_score,
            "hits": len(hits),
            "message": f"No confident fusion match for {query!r} (score={score:.2f}). Re-sense or refine name.",
            "hint": "GET /v1/vision/page then click an exact button/link text",
        }
    r = act_on_symbol(query)
    r["score"] = score
    r["sanity"] = "passed"
    return r


def guard_shell(command: str, *, allow_destructive: bool = False) -> Dict[str, Any]:
    c = (command or "").lower()
    if not allow_destructive and any(d in c for d in DESTRUCTIVE):
        return {
            "ok": False,
            "blocked": True,
            "reason": "sanity_guard_destructive",
            "message": "Destructive shell blocked. Pass allow_destructive=true only with human confirm.",
            "command_head": (command or "")[:120],
        }
    return {"ok": True, "allowed": True}


def intent_buffer(page_or_ctx: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Pre-render next-act suggestions from fusion action_hints (intent buffer)."""
    if page_or_ctx is None:
        from pocket.perception import agent_context

        page_or_ctx = agent_context(max_ui=300)
    hints = page_or_ctx.get("action_hints") or []
    predicted = []
    for h in hints[:8]:
        predicted.append(
            {
                "action": h.get("action"),
                "name": h.get("name"),
                "x": h.get("x"),
                "y": h.get("y"),
                "reason": h.get("reason"),
            }
        )
    return {
        "ok": True,
        "product": "Fusion Sense Intent Buffer",
        "predicted_acts": predicted,
        "brief": page_or_ctx.get("brief"),
        "page_hint": page_or_ctx.get("page_hint"),
        "counts": page_or_ctx.get("counts"),
    }
