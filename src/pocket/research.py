"""Research substrate embedded in POCKET runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

PAPER_ID = "INL-2026-POCKET.001"
PAPER_TITLE = "POCKET OS: Mobile Operator Substrate for Agent-Native Coding"
PAPER_PATH = Path(__file__).resolve().parents[2] / "docs" / "research" / "POCKET_RESEARCH_PAPER.md"


def research_manifest() -> Dict[str, Any]:
    text = ""
    if PAPER_PATH.is_file():
        try:
            text = PAPER_PATH.read_text(encoding="utf-8")[:4000]
        except Exception:
            text = ""
    return {
        "schema": "pocket.research.v1",
        "paper_id": PAPER_ID,
        "title": PAPER_TITLE,
        "path": str(PAPER_PATH),
        "exists": PAPER_PATH.is_file(),
        "bytes": PAPER_PATH.stat().st_size if PAPER_PATH.is_file() else 0,
        "abstract_prefix": text.split("## Abstract")[-1][:600] if "## Abstract" in text else text[:600],
        "keywords": [
            "mobile agents",
            "coding orchestration",
            "offline-capable ops",
            "Grok workflow",
            "suite integration",
        ],
        "protocol": "pocket.code.v1",
        "port": 8787,
        "related": [
            "INL-2026-HZHUB.001",
            "docs/suite/PROTOCOL_SUITE.md",
        ],
    }
