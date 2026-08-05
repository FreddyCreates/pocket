"""Auro meaning path inside POCKET — NumPy train/infer + browser model.json.

Wires the shipped ``vendor/auro_meaning`` piece (architecture + auro_web) so
POCKET can serve the browser demo, run greedy generation on host, and train
small corpora via optional train_lm/autograd when present.

Pipeline: train (NumPy) → model.json → auro.js (browser) — one function.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VENDOR = Path(__file__).resolve().parents[2] / "vendor" / "auro_meaning"
WEB = VENDOR / "auro_web"
MODEL_JSON = WEB / "model.json"
MODEL_PKG = VENDOR / "auro_native_llm_model"


def meaning_root() -> Path:
    env = os.environ.get("POCKET_AURO_MEANING")
    if env and Path(env).is_dir():
        return Path(env)
    return VENDOR


def status() -> Dict[str, Any]:
    root = meaning_root()
    web = root / "auro_web"
    model = web / "model.json"
    note = ""
    cfg = {}
    if model.is_file():
        try:
            payload = json.loads(model.read_text(encoding="utf-8"))
            note = str(payload.get("note") or "")[:240]
            cfg = payload.get("config") or {}
        except Exception as e:
            note = f"read error: {e}"
    train_lm = root / "train_lm.py"
    autograd = root / "autograd.py"
    if not train_lm.exists():
        # also search sibling names
        for p in root.rglob("train_lm.py"):
            train_lm = p
            break
    if not autograd.exists():
        for p in root.rglob("autograd.py"):
            autograd = p
            break
    return {
        "ok": model.is_file() and (root / "auro_native_llm_model").is_dir(),
        "product": "Auro meaning · NumPy ↔ browser",
        "vendor": str(root),
        "web_dir": str(web),
        "model_json": str(model) if model.is_file() else None,
        "model_bytes": model.stat().st_size if model.is_file() else 0,
        "config": cfg,
        "note": note,
        "browser_url": "/auro/",
        "train_lm": str(train_lm) if train_lm.is_file() else None,
        "autograd": str(autograd) if autograd.is_file() else None,
        "has_train_loop": train_lm.is_file() and autograd.is_file(),
        "claim": (
            "Same architecture (RMSNorm/RoPE/GQA/SwiGLU) on host NumPy and auro.js; "
            "export model.json for browser. Full AuroTrainer/autograd when train_lm present."
        ),
    }


def _ensure_sys_path() -> Path:
    root = meaning_root()
    s = str(root)
    if s not in sys.path:
        sys.path.insert(0, s)
    return root


def load_model_from_web_json(path: Optional[Path] = None) -> Any:
    """Load AuroTransformer weights from auro.web.v1 model.json."""
    import numpy as np

    _ensure_sys_path()
    from auro_native_llm_model.config import AuroConfig
    from auro_native_llm_model.transformer import AuroTransformer

    p = Path(path or MODEL_JSON)
    payload = json.loads(p.read_text(encoding="utf-8"))
    cfg = AuroConfig.from_dict(payload["config"])
    weights = {}
    for name, blob in (payload.get("weights") or {}).items():
        shape = blob.get("shape")
        data = blob.get("data")
        weights[name] = np.asarray(data, dtype=np.float32).reshape(shape)
    return AuroTransformer(cfg, weights=weights)


def generate_ids(
    prompt_ids: List[int],
    *,
    max_new: int = 24,
    temperature: float = 0.0,
) -> Dict[str, Any]:
    t0 = time.time()
    model = load_model_from_web_json()
    out = model.generate(prompt_ids, max_new_tokens=max_new, temperature=temperature)
    return {
        "ok": True,
        "prompt_ids": list(prompt_ids),
        "output_ids": list(out),
        "new_ids": list(out)[len(prompt_ids) :],
        "ms": int((time.time() - t0) * 1000),
        "params": model.num_parameters(),
        "config": model.config.to_dict() if hasattr(model.config, "to_dict") else {},
    }


def generate_bytes_greedy(prompt: str, *, max_new: int = 64) -> Dict[str, Any]:
    """If vocab>=256 treat tokens as bytes; else return id-only generation."""
    model = load_model_from_web_json()
    vocab = int(model.config.vocab_size)
    if vocab >= 256:
        ids = list(prompt.encode("utf-8", errors="replace")[: model.config.max_seq_len - 1])
        out = model.generate(ids, max_new_tokens=max_new, temperature=0.0)
        raw = bytes([min(255, max(0, i)) for i in out])
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            text = str(out)
        return {"ok": True, "mode": "bytes", "text": text, "ids": out, "params": model.num_parameters()}
    # small vocab demo
    seed = [min(vocab - 1, max(0, (ord(c) % vocab))) for c in (prompt or "abc")[:8]] or [1, 2, 3]
    r = generate_ids(seed, max_new=max_new, temperature=0.0)
    r["mode"] = "id-vocab"
    r["note"] = (
        f"vocab_size={vocab} — not byte LM; use train_lm with vocab 256 for text reproduction demos"
    )
    return r


def train_text_if_available(
    corpus: str,
    *,
    steps: int = 400,
) -> Dict[str, Any]:
    """Run AuroTrainer.train_text — always available now (vendor autograd+train_lm)."""
    st = status()
    root = meaning_root()
    _ensure_sys_path()
    train_path = Path(st["train_lm"]) if st.get("train_lm") else root / "train_lm.py"
    if not train_path.is_file():
        return {"ok": False, "error": "train_lm.py missing", "status": st}
    import importlib.util

    spec = importlib.util.spec_from_file_location("pocket_train_lm", train_path)
    if not spec or not spec.loader:
        return {"ok": False, "error": "cannot load train_lm"}
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "AuroTrainer"):
        return {"ok": False, "error": "AuroTrainer missing"}
    trainer = mod.AuroTrainer()
    text = corpus or getattr(mod, "ELEMENTS", "hello world")
    result = trainer.train_text(text, steps=int(steps))
    return {
        "ok": True,
        "final_loss": result.final_loss,
        "min_loss": min(result.losses) if result.losses else None,
        "sample": result.sample,
        "export_path": result.export_path,
        "seconds": result.seconds,
        "steps": result.steps,
        "browser": "/auro/",
    }


def run_auro_meaning_job(prompt: str) -> Tuple[str, str, str]:
    st = status()
    low = (prompt or "").lower().strip()
    lines = [
        "# Auro meaning · in POCKET\n\n",
        f"**Browser demo:** {st.get('browser_url')}\n",
        f"**model.json:** `{st.get('model_json')}` ({st.get('model_bytes')} bytes)\n",
        f"**config:** `{st.get('config')}`\n",
        f"**train loop on disk:** {st.get('has_train_loop')}\n\n",
        f"{st.get('claim')}\n\n",
    ]
    if low in ("", "status", "help"):
        lines.append(
            "Commands: `generate hydrogen` · `ids 3,1,4` · `train <corpus>` (needs train_lm)\n"
        )
        return "".join(lines), "", "auro-meaning"

    if low.startswith("ids ") or low.startswith("generate ids"):
        raw = prompt.split(" ", 1)[-1]
        ids = [int(x.strip()) for x in raw.replace("generate ids", "").split(",") if x.strip().lstrip("-").isdigit()]
        try:
            r = generate_ids(ids or [1, 2, 3], max_new=12, temperature=0.0)
            lines.append(f"## Greedy ids\n`{r['output_ids']}` · {r['ms']}ms · params={r['params']}\n")
            return "".join(lines), "", "auro-meaning"
        except Exception as e:
            return "".join(lines), str(e), "auro-meaning"

    if low.startswith("train "):
        corpus = prompt.split(" ", 1)[1]
        r = train_text_if_available(corpus, steps=100)
        lines.append(f"## Train\n```\n{json.dumps(r, default=str)[:3000]}\n```\n")
        return "".join(lines), ("" if r.get("ok") else r.get("error") or "train failed"), "auro-meaning"

    # default text-ish generate
    try:
        r = generate_bytes_greedy(prompt, max_new=48)
        lines.append("## Generate\n")
        if r.get("mode") == "bytes":
            lines.append(f"```\n{r.get('text')}\n```\n")
        else:
            lines.append(f"ids: `{r.get('output_ids') or r.get('ids')}`\n")
            if r.get("note"):
                lines.append(f"_{r['note']}_\n")
        return "".join(lines), "", "auro-meaning"
    except Exception as e:
        lines.append(f"## Error\n`{e}`\n")
        return "".join(lines), str(e), "auro-meaning"
