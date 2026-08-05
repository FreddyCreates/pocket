"""AuroTransformer — the full decoder-only model, forward pass and generation.

Assembles the primitives in ``layers.py`` into the architecture described by the
Auro model cards. Weights are held in a plain dict of NumPy arrays so the whole
model is trivially serializable (``state_dict`` / ``load_state_dict``) and can be
exported to the browser runtime that Pocket embeds.

Run it:

    from auro_native_llm.model import AuroConfig, AuroTransformer
    cfg = AuroConfig(vocab_size=256, hidden_size=128, n_layers=4, n_heads=8, n_kv_heads=2)
    model = AuroTransformer(cfg)                 # random-init (untrained)
    logits = model.forward([1, 2, 3, 4])          # (seq, vocab)
    out = model.generate([1, 2, 3], max_new_tokens=8, temperature=0.0)
"""

from __future__ import annotations

import numpy as np

from .config import AuroConfig
from .layers import (
    apply_rope,
    grouped_query_attention,
    rms_norm,
    rope_frequencies,
    softmax,
    swiglu,
)


def _init(shape, rng, scale):
    return (rng.standard_normal(shape) * scale).astype(np.float32)


class AuroTransformer:
    """Decoder-only transformer: RMSNorm + RoPE + GQA + SwiGLU."""

    def __init__(self, config: AuroConfig, seed: int = 0, weights: dict | None = None):
        self.config = config
        self.rng = np.random.default_rng(seed)
        self._cos, self._sin = rope_frequencies(
            config.head_dim, config.max_seq_len, config.rope_theta)
        self.weights = weights if weights is not None else self._init_weights()

    # --- initialization -----------------------------------------------------
    def _init_weights(self) -> dict:
        c = self.config
        h, d, kv = c.hidden_size, c.head_dim, c.n_kv_heads
        inter = c.intermediate_size
        s = 0.02
        w: dict = {"tok_embed": _init((c.vocab_size, h), self.rng, s)}
        for i in range(c.n_layers):
            p = f"layers.{i}."
            w[p + "attn_norm"] = np.ones((h,), dtype=np.float32)
            w[p + "wq"] = _init((h, h), self.rng, s)
            w[p + "wk"] = _init((h, kv * d), self.rng, s)
            w[p + "wv"] = _init((h, kv * d), self.rng, s)
            w[p + "wo"] = _init((h, h), self.rng, s)
            w[p + "ffn_norm"] = np.ones((h,), dtype=np.float32)
            w[p + "w_gate"] = _init((h, inter), self.rng, s)
            w[p + "w_up"] = _init((h, inter), self.rng, s)
            w[p + "w_down"] = _init((inter, h), self.rng, s)
        w["final_norm"] = np.ones((h,), dtype=np.float32)
        if not c.tie_embeddings:
            w["lm_head"] = _init((h, c.vocab_size), self.rng, s)
        return w

    # --- forward ------------------------------------------------------------
    def forward(self, token_ids) -> np.ndarray:
        """Return logits of shape (seq_len, vocab_size) for a token id list."""
        c = self.config
        ids = np.asarray(token_ids, dtype=np.int64)
        seq = ids.shape[0]
        if seq > c.max_seq_len:
            raise ValueError(f"sequence length {seq} exceeds max_seq_len {c.max_seq_len}")
        w = self.weights
        x = w["tok_embed"][ids]                       # (seq, hidden)

        for i in range(c.n_layers):
            p = f"layers.{i}."
            # --- attention block (pre-norm, residual) ---
            h_in = rms_norm(x, w[p + "attn_norm"], c.rms_eps)
            q = (h_in @ w[p + "wq"]).reshape(seq, c.n_heads, c.head_dim).transpose(1, 0, 2)
            k = (h_in @ w[p + "wk"]).reshape(seq, c.n_kv_heads, c.head_dim).transpose(1, 0, 2)
            v = (h_in @ w[p + "wv"]).reshape(seq, c.n_kv_heads, c.head_dim).transpose(1, 0, 2)
            attn = grouped_query_attention(q, k, v, self._cos, self._sin, c.n_rep, causal=True)
            attn = attn.transpose(1, 0, 2).reshape(seq, c.hidden_size)  # (seq, hidden)
            x = x + attn @ w[p + "wo"]
            # --- feed-forward block (pre-norm, residual) ---
            h_ff = rms_norm(x, w[p + "ffn_norm"], c.rms_eps)
            x = x + swiglu(h_ff, w[p + "w_gate"], w[p + "w_up"], w[p + "w_down"])

        x = rms_norm(x, w["final_norm"], c.rms_eps)
        head = w["tok_embed"].T if c.tie_embeddings else w["lm_head"]
        return x @ head                               # (seq, vocab)

    # --- generation ---------------------------------------------------------
    def generate(self, prompt_ids, max_new_tokens: int = 16, temperature: float = 0.0,
                 top_k: int | None = None, seed: int | None = None):
        """Autoregressively extend prompt_ids. temperature=0 -> greedy/deterministic."""
        rng = np.random.default_rng(seed) if seed is not None else self.rng
        ids = list(prompt_ids)
        for _ in range(max_new_tokens):
            context = ids[-self.config.max_seq_len:]
            logits = self.forward(context)[-1]        # (vocab,)
            if temperature <= 0.0:
                nxt = int(np.argmax(logits))
            else:
                logits = logits / temperature
                if top_k:
                    kth = np.partition(logits, -top_k)[-top_k]
                    logits = np.where(logits < kth, -1e30, logits)
                probs = softmax(logits)
                nxt = int(rng.choice(len(probs), p=probs))
            ids.append(nxt)
        return ids

    # --- (de)serialization --------------------------------------------------
    def num_parameters(self) -> int:
        return int(sum(v.size for v in self.weights.values()))

    def state_dict(self) -> dict:
        return {"config": self.config.to_dict(),
                "weights": {k: v.tolist() for k, v in self.weights.items()}}

    @classmethod
    def from_state_dict(cls, state: dict) -> "AuroTransformer":
        cfg = AuroConfig.from_dict(state["config"])
        weights = {k: np.asarray(v, dtype=np.float32) for k, v in state["weights"].items()}
        return cls(cfg, weights=weights)
