"""PyInstaller entrypoint for the bundled POCKET local engine."""
from __future__ import annotations

import argparse
import os
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()
    state = Path.home() / ".pocket"
    state.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("POCKET_PORT", str(args.port))
    os.environ.setdefault("POCKET_DESKTOP_MANAGED", "1")
    os.environ.setdefault("POCKET_MESH_HOOK", "0")
    os.environ.setdefault("POCKET_ALWAYS_MESH", "0")
    os.environ.setdefault("POCKET_HEADLESS_AUTO", "0")
    os.environ.setdefault("POCKET_AURO_TRAIN", "0")
    from pocket.server import serve
    serve(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
