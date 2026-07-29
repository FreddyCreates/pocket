"""Production rate limits — login, register, API calls."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Dict, List, Tuple

_lock = Lock()
_buckets: Dict[str, List[float]] = defaultdict(list)

# window_sec, max_hits
LIMITS = {
    "login": (300, 20),       # 20 attempts / 5 min / IP
    "register": (600, 10),    # 10 register / 10 min / IP
    "api": (60, 120),         # 120 API calls / min / key-or-ip
    "api_heavy": (60, 20),    # 20 heavy agent runs / min
}


def hit(bucket: str, key: str, *, kind: str = "api") -> Tuple[bool, str]:
    """Return (allowed, reason)."""
    window, max_hits = LIMITS.get(kind, (60, 60))
    now = time.time()
    bk = f"{kind}:{bucket}:{key}"
    with _lock:
        hits = [t for t in _buckets.get(bk, []) if now - t < window]
        if len(hits) >= max_hits:
            _buckets[bk] = hits
            return False, f"rate limit: {max_hits} per {window}s"
        hits.append(now)
        _buckets[bk] = hits
    return True, "ok"
