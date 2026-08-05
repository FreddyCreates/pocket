"""Export a trained/initialized AuroTransformer to a portable JSON the browser
runtime (``auro_web/auro.js``) can load.

This is the bridge that makes a piece of Auro includable in a web app like
Pocket: run/​train the model here in NumPy, export one ``.json`` file, drop it
next to ``auro.js``, and the same architecture (RMSNorm/RoPE/GQA/SwiGLU) runs in
the browser with byte-for-byte matching math.

    python3 -m auro_native_llm.model.export_web --out auro_web/model.json \
        --hidden 64 --layers 3 --heads 8 --kv 2 --vocab 64
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from .config import AuroConfig
from .transformer import AuroTransformer


def export_model(model: AuroTransformer, path: str | Path) -> Path:
    """Write config + flattened row-major weights to a compact JSON file."""
    c = model.config
    weights = {}
    for name, arr in model.weights.items():
        a = np.ascontiguousarray(arr, dtype=np.float32)
        weights[name] = {"shape": list(a.shape), "data": a.reshape(-1).round(6).tolist()}
    payload = {
        "format": "auro.web.v1",
        "note": "Auro architecture weights (RMSNorm/RoPE/GQA/SwiGLU). "
                "Not a trained 14B/200B checkpoint — the runnable architecture.",
        "config": c.to_dict(),
        "weights": weights,
    }
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload))
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description="Export an Auro model to portable web JSON.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--hidden", type=int, default=64)
    ap.add_argument("--layers", type=int, default=3)
    ap.add_argument("--heads", type=int, default=8)
    ap.add_argument("--kv", type=int, default=2)
    ap.add_argument("--vocab", type=int, default=64)
    ap.add_argument("--max-seq", type=int, default=64)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    cfg = AuroConfig(vocab_size=args.vocab, hidden_size=args.hidden, n_layers=args.layers,
                     n_heads=args.heads, n_kv_heads=args.kv, max_seq_len=args.max_seq)
    model = AuroTransformer(cfg, seed=args.seed)
    out = export_model(model, args.out)
    print(f"exported {model.num_parameters()} params -> {out}")


if __name__ == "__main__":
    main()
