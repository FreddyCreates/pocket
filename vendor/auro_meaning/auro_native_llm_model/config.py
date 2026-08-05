"""AuroConfig — the decoder-only transformer configuration.

This is the *runnable* companion to the JSON targets in
``native_llm/configs/*.json``. The same fields that describe the 14B and 200B
shapes describe a tiny model too, so the architecture code below can be executed
end-to-end on a laptop while remaining faithful to the target design:

    decoder-only  •  RMSNorm  •  RoPE  •  grouped-query attention  •  SwiGLU

Nothing here is a trained checkpoint. This is the architecture — the shape and
the math — made real and testable at small scale, exactly as the model cards
require ("do not claim trained until checkpoint and eval receipts exist").
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuroConfig:
    """Shape of an Auro decoder-only transformer.

    Field names mirror ``native_llm/configs/auro_14b_dev.json`` so a target
    config loads directly (see :meth:`from_target_json`).
    """

    vocab_size: int = 256
    hidden_size: int = 128
    n_layers: int = 4
    n_heads: int = 8
    n_kv_heads: int = 2            # GQA: kv_heads <= heads, heads % kv_heads == 0
    ffn_multiple: int = 4         # SwiGLU intermediate ~ ffn_multiple * hidden (rounded)
    max_seq_len: int = 512
    rope_theta: float = 10000.0
    rms_eps: float = 1e-6
    tie_embeddings: bool = True

    def __post_init__(self) -> None:
        if self.hidden_size % self.n_heads != 0:
            raise ValueError(f"hidden_size {self.hidden_size} not divisible by n_heads {self.n_heads}")
        if self.n_heads % self.n_kv_heads != 0:
            raise ValueError(f"n_heads {self.n_heads} not divisible by n_kv_heads {self.n_kv_heads}")

    # --- derived ------------------------------------------------------------
    @property
    def head_dim(self) -> int:
        return self.hidden_size // self.n_heads

    @property
    def n_rep(self) -> int:
        """How many query heads share each kv head (GQA repeat factor)."""
        return self.n_heads // self.n_kv_heads

    @property
    def intermediate_size(self) -> int:
        """SwiGLU hidden width, rounded to a multiple of 256 like real models."""
        raw = int(self.ffn_multiple * self.hidden_size * 2 / 3)
        return ((raw + 255) // 256) * 256

    # --- parameter accounting ----------------------------------------------
    def param_count(self) -> int:
        """Exact trainable-parameter count for this shape.

        Matches the standard decoder-only formula so a scaled config predicts
        its own size — the same arithmetic that yields ~14B at the dev shape.
        """
        h, d = self.hidden_size, self.head_dim
        kv = self.n_kv_heads
        inter = self.intermediate_size

        embed = self.vocab_size * h
        # attention: q (h*h) + k,v (h*kv*d each) + o (h*h)
        attn = h * h + 2 * (h * kv * d) + h * h
        # swiglu: gate + up (h*inter each) + down (inter*h)
        ffn = 3 * (h * inter)
        # two rmsnorm weights per block (attn + ffn), one final norm
        norms_per_block = 2 * h
        per_block = attn + ffn + norms_per_block
        total = embed + self.n_layers * per_block + h  # + final norm
        if not self.tie_embeddings:
            total += self.vocab_size * h                # separate lm_head
        return total

    # --- (de)serialization --------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "vocab_size": self.vocab_size, "hidden_size": self.hidden_size,
            "n_layers": self.n_layers, "n_heads": self.n_heads,
            "n_kv_heads": self.n_kv_heads, "ffn_multiple": self.ffn_multiple,
            "max_seq_len": self.max_seq_len, "rope_theta": self.rope_theta,
            "rms_eps": self.rms_eps, "tie_embeddings": self.tie_embeddings,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "AuroConfig":
        fields = {k: d[k] for k in cls().to_dict() if k in d}
        return cls(**fields)

    @classmethod
    def from_target_json(cls, path: str | Path, *, max_seq_len: int | None = None) -> "AuroConfig":
        """Load a ``native_llm/configs/auro_*.json`` target as a runnable config.

        The target JSON describes billions of parameters; this returns the exact
        same *shape* (heads, kv_heads, layers, activation, rope) so the
        architecture is faithful. To actually run it on a laptop, scale down
        ``hidden_size``/``n_layers`` via :meth:`scaled`.
        """
        cfg = json.loads(Path(path).read_text())
        arch = cfg["architecture"]
        return cls(
            vocab_size=arch.get("vocab_size_target", 256),
            hidden_size=arch["hidden_size"],
            n_layers=arch["layers"],
            n_heads=arch["attention_heads"],
            n_kv_heads=arch.get("kv_heads", arch["attention_heads"]),
            ffn_multiple=arch.get("ffn_multiple", 4),
            max_seq_len=max_seq_len or arch.get("context_window_tokens_target", 512),
        )

    def scaled(self, *, n_layers: int, n_kv_heads: int = 2, head_dim: int = 32,
               vocab_size: int | None = None, max_seq_len: int | None = None) -> "AuroConfig":
        """Return the same architecture at a smaller, runnable size.

        Builds the miniature *from* the GQA ratio so the query:kv head ratio
        (the defining GQA design choice) is preserved exactly:

            n_heads = n_kv_heads * self.n_rep      (same ratio as the target)
            hidden  = n_heads * head_dim

        The result is a true miniature of the target — same normalization,
        position encoding, activation, and grouped-query ratio — just narrower
        and shallower so it runs on a laptop.
        """
        new_heads = n_kv_heads * self.n_rep
        return AuroConfig(
            vocab_size=vocab_size or self.vocab_size,
            hidden_size=new_heads * head_dim,
            n_layers=n_layers,
            n_heads=new_heads,
            n_kv_heads=n_kv_heads,
            ffn_multiple=self.ffn_multiple,
            max_seq_len=max_seq_len or self.max_seq_len,
            rope_theta=self.rope_theta,
            rms_eps=self.rms_eps,
            tie_embeddings=self.tie_embeddings,
        )
