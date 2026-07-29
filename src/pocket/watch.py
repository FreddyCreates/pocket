"""PC terminal watcher for POCKET code queue — Grok/operator side."""

from __future__ import annotations

import json
import time
from pathlib import Path

from pocket.server import CODE_Q, read_jsonl

try:
    from hz.ai.offline_brain import OfflineBrain
except Exception:
    OfflineBrain = None  # type: ignore


def run_watch(*, once: bool = False, poll: float = 2.5) -> None:
    print("POCKET watch — phone coding queue")
    print(f"  queue: {CODE_Q}")
    print("  Ctrl+C stop")
    seen = set()
    brain = OfflineBrain(node_name="pocket-pc") if OfflineBrain else None
    while True:
        for item in read_jsonl(CODE_Q, 80):
            iid = item.get("id")
            if not iid or iid in seen or item.get("status") != "queued":
                continue
            seen.add(iid)
            print()
            print("=" * 52)
            print(f"POCKET CODE  {item.get('from')}  [{item.get('lang')}]  {iid}")
            print(item.get("prompt") or "")
            print("=" * 52)
            if brain:
                r = brain.think(
                    f"Phone coding request ({item.get('lang')}): {item.get('prompt')}. "
                    "Give a short plan + first code steps for the PC operator/Grok."
                )
                print("\nAGENT PLAN:\n", r.get("reply"), "\n")
            print("(Mark handled in your session; re-queue by sending again from POCKET.)")
        if once:
            break
        time.sleep(poll)


if __name__ == "__main__":
    run_watch()
