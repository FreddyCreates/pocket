"""Unified subagents registry for the desk UI.

Merges Latin workers, DESIGN, 4 headless mesh agents, live dynamic workers,
skill_suite names, and mesh disk identities into one catalog the panel can render.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

# Always surface these in the desk roster (Antigravity-style mesh pack)
MESH_CORE: Dict[str, str] = {
    "DESIGN": "design · UI + product craft",
    "AESTHETE": "design · visual taste",
    "LAYOUT": "design · structure + spacing",
    "MOTION": "design · motion + feedback",
    "FORGE_HEADLESS": "headless · build / test / package",
    "SENTINEL_HEADLESS": "headless · security + audit",
    "RESEARCH_HEADLESS": "headless · research packs",
    "SHIP_HEADLESS": "headless · release / beta ship",
}


def _entry(
    id: str,
    name: str,
    role: str,
    status: str,
    source: str,
) -> Dict[str, Any]:
    return {
        "id": id,
        "name": name,
        "role": role,
        "status": status,
        "source": source,
    }


def _latin_workers() -> List[Dict[str, Any]]:
    from pocket.alpha_workers import list_workers

    out: List[Dict[str, Any]] = []
    for w in list_workers():
        wid = str(w.get("id") or w.get("latin") or "").upper()
        if not wid:
            continue
        role = str(w.get("role") or w.get("class") or "python")
        meaning = (w.get("meaning") or "").strip()
        if meaning:
            role = f"{role} · {meaning}"
        out.append(
            _entry(
                id=wid,
                # Canonical UPPER id for @mentions (ARCHON, OCULUS, …)
                name=wid,
                role=role,
                status="ready",
                source="latin",
            )
        )
    return out


def _design_and_headless() -> List[Dict[str, Any]]:
    """DESIGN + 4 headless — always present with roles for desk UI."""
    out: List[Dict[str, Any]] = []
    # Prefer HEADLESS map from dispatch for live descriptions
    headless_desc: Dict[str, str] = {}
    try:
        from pocket.subagent_dispatch import HEADLESS

        headless_desc = {str(k).upper(): str(v) for k, v in (HEADLESS or {}).items()}
    except Exception:
        pass

    design_ids = {"DESIGN", "AESTHETE", "LAYOUT", "MOTION"}
    for name, default_role in MESH_CORE.items():
        if name in design_ids or default_role.startswith("design"):
            role = default_role if default_role.startswith("design") else f"design · {default_role}"
            source = "design"
            status = "ready"
        else:
            desc = headless_desc.get(name) or default_role.replace("headless · ", "")
            role = f"headless · {desc}" if not str(desc).startswith("headless") else desc
            if not role.startswith("headless"):
                role = f"headless · {role}"
            source = "headless"
            status = "headless"
        out.append(_entry(id=name, name=name, role=role, status=status, source=source))

    # Extra design agents if design_agents module exists
    try:
        from pocket.design_agents import list_design_agents

        seen = {e["id"] for e in out}
        for e in list_design_agents():
            did = str(e.get("id") or "").upper()
            if not did or did in seen:
                continue
            out.append(
                _entry(
                    id=did,
                    name=did,
                    role=f"design · {e.get('role') or 'craft'}",
                    status=str(e.get("status") or "ready"),
                    source="design",
                )
            )
            seen.add(did)
    except Exception:
        pass

    return out


def _mesh_extras(seen_ids: Set[str]) -> List[Dict[str, Any]]:
    """Other mesh-registered agents not already in latin/design/headless."""
    try:
        from pocket.mesh_disk import bootstrap_core_agents, status as mesh_status

        try:
            bootstrap_core_agents()
        except Exception:
            pass
        st = mesh_status()
    except Exception:
        return []

    out: List[Dict[str, Any]] = []
    for a in st.get("agents") or []:
        aid = str(a or "").upper().strip()
        if not aid or aid in seen_ids or aid == "USER":
            continue
        if aid in MESH_CORE:
            role = MESH_CORE[aid]
            source = "design" if aid == "DESIGN" else "headless"
        elif "HEADLESS" in aid:
            role = "headless · mesh"
            source = "headless"
        else:
            role = "mesh · worker"
            source = "mesh"
        out.append(_entry(id=aid, name=aid, role=role, status="ready", source=source))
        seen_ids.add(aid)
    return out


def _dynamic_workers() -> List[Dict[str, Any]]:
    from pocket.dynamic_worker import list_active

    out: List[Dict[str, Any]] = []
    for w in list_active():
        wid = str(w.get("id") or "")
        name = str(w.get("name") or wid or "DYNAMIC")
        status = str(w.get("status") or "unknown")
        goal = (w.get("goal") or "").strip()
        role = f"dynamic · {goal}" if goal else "dynamic"
        out.append(
            _entry(
                id=wid or f"dw-{name}",
                name=name,
                role=role[:200],
                status=status,
                source="dynamic",
            )
        )
    return out


def _skill_suite_workers(seen_ids: Set[str]) -> List[Dict[str, Any]]:
    from pocket.skill_suite import all_skills

    names: List[str] = []
    for s in all_skills():
        n = (s.get("worker") or "").strip().upper()
        if n and n not in names:
            names.append(n)

    out: List[Dict[str, Any]] = []
    for n in names:
        if n in seen_ids:
            continue
        out.append(
            _entry(
                id=n,
                name=n,
                role="skill_suite",
                status="catalog",
                source="skill_suite",
            )
        )
        seen_ids.add(n)
    return out


def _is_running(status: str) -> bool:
    s = (status or "").lower()
    return s in ("running", "running_async", "active", "busy")


def list_subagents() -> Dict[str, Any]:
    """Full registry: latin + DESIGN/headless mesh + dynamic + skill_suite."""
    latin = _latin_workers()
    core = _design_and_headless()
    dynamic = _dynamic_workers()
    seen: Set[str] = set()
    for e in latin + core + dynamic:
        seen.add(str(e.get("id") or "").upper())
        nm = str(e.get("name") or "").upper()
        if nm:
            seen.add(nm)

    mesh = _mesh_extras(seen)
    suite = _skill_suite_workers(seen)

    # Latin first, then DESIGN + headless pack, then live dynamic, mesh extras, suite
    subagents = latin + core + dynamic + mesh + suite
    uniq: List[Dict[str, Any]] = []
    seen2: Set[str] = set()
    for e in subagents:
        k = str(e.get("id") or "").upper()
        if not k or k in seen2:
            continue
        seen2.add(k)
        uniq.append(e)

    running_count = sum(1 for e in uniq if _is_running(e["status"]))
    mesh_meta: Dict[str, Any] = {}
    try:
        from pocket.mesh_disk import status as mesh_status

        mesh_meta = mesh_status()
    except Exception:
        pass

    return {
        "ok": True,
        "subagents": uniq,
        "running_count": running_count,
        "count": len(uniq),
        "mesh_core": list(MESH_CORE.keys()),
        "headless_count": sum(1 for e in uniq if e.get("source") == "headless"),
        "design_count": sum(1 for e in uniq if e.get("source") == "design"),
        "mesh": mesh_meta,
    }


def list_running() -> Dict[str, Any]:
    """Only subagents currently running (typically dynamic workers)."""
    full = list_subagents()
    running = [e for e in full["subagents"] if _is_running(e["status"])]
    return {
        "ok": True,
        "subagents": running,
        "running_count": len(running),
    }
