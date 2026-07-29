"""Purchase playbooks — SCAFFOLD only. Never auto-confirm payment.

Teaches structure for future: vision→find cart→fill→STOP for human confirm.
"""

from __future__ import annotations

from typing import Any, Dict, List

# Explicit human gate — never skip
REQUIRE_HUMAN_CONFIRM = True

PLAYBOOKS: Dict[str, Dict[str, Any]] = {
    "generic_checkout_scaffold": {
        "id": "generic_checkout_scaffold",
        "risk": "high",
        "auto_pay": False,
        "steps": [
            {"skill": "observe", "note": "See current page via vision+UI map"},
            {"skill": "click_by_name", "params": {"name": "Add to cart"}, "optional": True},
            {"skill": "click_by_name", "params": {"name": "Cart"}, "optional": True},
            {"skill": "click_by_name", "params": {"name": "Checkout"}, "optional": True},
            {"action": "HUMAN_CONFIRM", "message": "STOP — human must confirm payment. Workers never click Buy/Pay/Place order without explicit operator approval token."},
        ],
        "forbidden_clicks": ["Place order", "Pay now", "Buy now", "Confirm purchase", "Submit payment"],
    }
}


def list_playbooks() -> List[Dict[str, Any]]:
    return [
        {
            "id": p["id"],
            "risk": p["risk"],
            "auto_pay": False,
            "human_gate": True,
            "steps": len(p["steps"]),
        }
        for p in PLAYBOOKS.values()
    ]


def run_playbook_scaffold(playbook_id: str) -> Dict[str, Any]:
    """Run non-payment steps only; always halt before pay."""
    from pocket.vision_core import observe, click_by_name

    pb = PLAYBOOKS.get(playbook_id) or PLAYBOOKS["generic_checkout_scaffold"]
    log = []
    for step in pb["steps"]:
        if step.get("action") == "HUMAN_CONFIRM":
            log.append({"halt": True, "message": step["message"]})
            break
        if step.get("skill") == "observe":
            obs = observe(with_ui_map=True)
            log.append({"skill": "observe", "ui_count": obs.get("ui_map_count")})
        elif step.get("skill") == "click_by_name":
            name = (step.get("params") or {}).get("name") or ""
            if any(f.lower() in name.lower() for f in pb.get("forbidden_clicks") or []):
                log.append({"blocked": name, "reason": "forbidden payment control"})
                continue
            # scaffold: do not actually click cart flows by default
            log.append({"skipped_click": name, "reason": "scaffold mode — teach only until operator enables"})
    return {
        "ok": True,
        "playbook": pb["id"],
        "scaffold": True,
        "auto_pay": False,
        "log": log,
        "message": "Purchase playbook scaffold only — no payments executed",
    }
