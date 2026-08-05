"""Agent Duels — two specialists propose; a judge picks; optional apply.

Cool, product-native: not one model monologue — competitive multi-agent craft.
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path.home() / ".pocket" / "duels"
ROOT.mkdir(parents=True, exist_ok=True)

PERSONAS = {
    "FORGE": {
        "name": "FORGE",
        "style": "minimal diff, production safety, tests first",
        "bias": "smallest change that works",
    },
    "AESTHETE": {
        "name": "AESTHETE",
        "style": "clarity, UX, naming, elegant structure",
        "bias": "readable architecture over clever hacks",
    },
    "SENTINEL": {
        "name": "SENTINEL",
        "style": "threat model, auth, isolation, least privilege",
        "bias": "security over speed",
    },
    "ARCHON": {
        "name": "ARCHON",
        "style": "orchestration, tradeoffs, ship criteria",
        "bias": "decide and finish",
    },
}


def _proposal(persona: str, challenge: str) -> Dict[str, Any]:
    p = PERSONAS.get(persona) or {
        "name": persona,
        "style": "generalist",
        "bias": "balanced",
    }
    # Structured proposal without requiring live LLM (deterministic craft)
    # Live engines can refine later via desk handoff.
    steps = [
        f"Restate goal in one sentence under {p['bias']}.",
        f"List 3 constraints ({p['style']}).",
        "Propose a 5-step plan with success checks.",
        "Name exact files/modules to touch (prefer Infinite Wiki profile→slice).",
        "Define a 60-second real verification.",
    ]
    plan = (
        f"# Proposal · {p['name']}\n\n"
        f"**Challenge:** {challenge}\n\n"
        f"**Lens:** {p['style']}\n"
        f"**Bias:** {p['bias']}\n\n"
        "## Plan\n"
        + "\n".join(f"{i+1}. {s}" for i, s in enumerate(steps))
        + "\n\n## Risks\n- Scope creep\n- Missing tests\n- Host/market isolation edge cases\n"
        + "\n## Ship bar\n- Diff is reviewable\n- One real check green\n- Receipt minted\n"
    )
    score = 70
    if "security" in challenge.lower() and persona == "SENTINEL":
        score += 15
    if any(k in challenge.lower() for k in ("ui", "design", "ux")) and persona == "AESTHETE":
        score += 15
    if any(k in challenge.lower() for k in ("ship", "fix", "bug", "code")) and persona == "FORGE":
        score += 12
    if persona == "ARCHON":
        score += 5
    return {
        "persona": p["name"],
        "score_hint": min(99, score),
        "plan": plan,
        "style": p["style"],
    }


def _judge(challenge: str, proposals: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Weighted: score_hint + keyword fit + length sanity
    ranked = sorted(proposals, key=lambda x: (-int(x.get("score_hint") or 0), x.get("persona") or ""))
    winner = ranked[0] if ranked else {}
    rationale = (
        f"Judge ARCHON selected **{winner.get('persona')}** "
        f"(hint={winner.get('score_hint')}) for challenge fitness and ship clarity. "
        f"Runner-up: {ranked[1].get('persona') if len(ranked)>1 else 'n/a'}."
    )
    return {
        "winner": winner.get("persona"),
        "rationale": rationale,
        "ranking": [p.get("persona") for p in ranked],
        "winning_plan": winner.get("plan"),
    }


def duel(
    challenge: str,
    *,
    contenders: Optional[List[str]] = None,
    judge: str = "ARCHON",
) -> Dict[str, Any]:
    challenge = (challenge or "").strip()
    if not challenge:
        return {"ok": False, "error": "challenge required"}
    contenders = contenders or ["FORGE", "AESTHETE", "SENTINEL"]
    contenders = [c.upper() for c in contenders if c][:4]
    proposals = [_proposal(c, challenge) for c in contenders]
    verdict = _judge(challenge, proposals)
    did = f"duel-{uuid.uuid4().hex[:10]}"
    rec = {
        "ok": True,
        "id": did,
        "at": time.time(),
        "challenge": challenge,
        "judge": judge,
        "proposals": proposals,
        "verdict": verdict,
        "schema": "pocket.duel.v1",
    }
    (ROOT / f"{did}.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    (ROOT / f"{did}-winner.md").write_text(verdict.get("winning_plan") or "", encoding="utf-8")
    try:
        from pocket.proof_chain import mint_receipt

        mint_receipt(
            "duel",
            f"{verdict.get('winner')} wins: {challenge[:80]}",
            meta={"id": did, "winner": verdict.get("winner")},
        )
    except Exception:
        pass
    try:
        from pocket.live_events import emit

        emit("duel", f"{verdict.get('winner')} · {challenge[:60]}", agent="ARCHON", role="judge")
    except Exception:
        pass
    return rec


def list_duels(limit: int = 15) -> List[Dict[str, Any]]:
    files = sorted(ROOT.glob("duel-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []
    for fp in files[:limit]:
        try:
            j = json.loads(fp.read_text(encoding="utf-8"))
            out.append(
                {
                    "id": j.get("id"),
                    "at": j.get("at"),
                    "challenge": j.get("challenge"),
                    "winner": (j.get("verdict") or {}).get("winner"),
                }
            )
        except Exception:
            continue
    return out


def get_duel(did: str) -> Optional[Dict[str, Any]]:
    fp = ROOT / f"{did}.json"
    if not fp.exists() and not did.startswith("duel-"):
        fp = ROOT / f"duel-{did}.json"
    if not fp.exists():
        # try exact
        for p in ROOT.glob("duel-*.json"):
            if did in p.name:
                fp = p
                break
    if not fp.exists():
        return None
    try:
        return json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return None
