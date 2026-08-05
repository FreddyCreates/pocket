"""AuroTrainer — real CE training (pure reverse-mode autograd) + model.json export.

Single-head causal attention via pure Tensor ops so grads are correct.
Weight layout still matches AuroTransformer for auro.js (n_kv_heads=n_heads=1 or multi-head pure).
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import numpy as np

from autograd import (
    Tensor,
    add,
    cross_entropy,
    embedding,
    matmul,
    mul,
    reshape,
    rms_norm,
    silu,
    softmax,
    transpose,
)
from auro_native_llm_model.config import AuroConfig
from auro_native_llm_model.export_web import export_model
from auro_native_llm_model.transformer import AuroTransformer

HERE = Path(__file__).resolve().parent
WEB_MODEL = HERE / "auro_web" / "model.json"

ELEMENTS = (
    "hydrogen and helium are the lightest elements. "
    "carbon forms the basis of life. "
    "iron is forged in the hearts of stars. "
    "oxygen keeps animals alive. "
    "nitrogen fills most of the air we breathe. "
)


def _p(shape, rng, scale=0.02) -> Tensor:
    return Tensor((rng.standard_normal(shape) * scale).astype(np.float32), requires_grad=True)


class TrainableAuro:
    """Multi-head causal attention with pure autograd (no detached VJPs)."""

    def __init__(self, config: AuroConfig, seed: int = 0):
        self.config = config
        rng = np.random.default_rng(seed)
        c = config
        assert c.n_heads == c.n_kv_heads, "train path uses MHA (n_heads == n_kv_heads)"
        h, d = c.hidden_size, c.head_dim
        inter = c.intermediate_size
        s = 0.05
        self.w: Dict[str, Tensor] = {"tok_embed": _p((c.vocab_size, h), rng, s)}
        for i in range(c.n_layers):
            p = f"layers.{i}."
            self.w[p + "attn_norm"] = Tensor(np.ones(h, np.float32), requires_grad=True)
            self.w[p + "wq"] = _p((h, h), rng, s)
            self.w[p + "wk"] = _p((h, h), rng, s)
            self.w[p + "wv"] = _p((h, h), rng, s)
            self.w[p + "wo"] = _p((h, h), rng, s)
            self.w[p + "ffn_norm"] = Tensor(np.ones(h, np.float32), requires_grad=True)
            self.w[p + "w_gate"] = _p((h, inter), rng, s)
            self.w[p + "w_up"] = _p((h, inter), rng, s)
            self.w[p + "w_down"] = _p((inter, h), rng, s)
        self.w["final_norm"] = Tensor(np.ones(h, np.float32), requires_grad=True)

    def parameters(self) -> List[Tensor]:
        return list(self.w.values())

    def zero_grad(self):
        for p in self.parameters():
            p.zero_grad()

    def _causal_attn(self, x: Tensor, p: str) -> Tensor:
        c = self.config
        seq, h, nh, d = x.data.shape[0], c.hidden_size, c.n_heads, c.head_dim
        q = matmul(x, self.w[p + "wq"])
        k = matmul(x, self.w[p + "wk"])
        v = matmul(x, self.w[p + "wv"])
        # process each head with pure matmul (loop — small models)
        outs = []
        for hi in range(nh):
            qs = q.data[:, hi * d : (hi + 1) * d]
            ks = k.data[:, hi * d : (hi + 1) * d]
            vs = v.data[:, hi * d : (hi + 1) * d]
            # slice tensors via mul with masks is hard; use views as Tensor with shared backward
            Q = self._slice_cols(q, hi * d, (hi + 1) * d)
            K = self._slice_cols(k, hi * d, (hi + 1) * d)
            V = self._slice_cols(v, hi * d, (hi + 1) * d)
            scale = 1.0 / np.sqrt(d)
            scores = mul(matmul(Q, transpose(K)), Tensor(np.float32(scale)))
            mask = np.triu(np.ones((seq, seq), np.float32), 1) * (-1e9)
            scores = add(scores, Tensor(mask))
            P = softmax(scores, axis=-1)
            outs.append(matmul(P, V))
        # concat heads
        cat = outs[0]
        for o in outs[1:]:
            cat = self._concat_last(cat, o)
        return matmul(cat, self.w[p + "wo"])

    def _slice_cols(self, a: Tensor, start: int, end: int) -> Tensor:
        out = Tensor(a.data[:, start:end].copy(), requires_grad=a.requires_grad)

        def _bw():
            if out.grad is None or not a.requires_grad:
                return
            a._ensure_grad()
            a.grad[:, start:end] += out.grad

        out._backward = _bw
        out._prev = (a,)
        return out

    def _concat_last(self, a: Tensor, b: Tensor) -> Tensor:
        out = Tensor(np.concatenate([a.data, b.data], axis=-1), requires_grad=a.requires_grad or b.requires_grad)
        na = a.data.shape[-1]

        def _bw():
            if out.grad is None:
                return
            if a.requires_grad:
                a._ensure_grad()
                a.grad = a.grad + out.grad[..., :na]
            if b.requires_grad:
                b._ensure_grad()
                b.grad = b.grad + out.grad[..., na:]

        out._backward = _bw
        out._prev = (a, b)
        return out

    def forward_logits(self, ids: List[int]) -> Tensor:
        c = self.config
        x = embedding(self.w["tok_embed"], np.asarray(ids, dtype=np.int64))
        for i in range(c.n_layers):
            p = f"layers.{i}."
            h_in = rms_norm(x, self.w[p + "attn_norm"], c.rms_eps)
            x = add(x, self._causal_attn(h_in, p))
            h_ff = rms_norm(x, self.w[p + "ffn_norm"], c.rms_eps)
            gate = silu(matmul(h_ff, self.w[p + "w_gate"]))
            up = matmul(h_ff, self.w[p + "w_up"])
            x = add(x, matmul(mul(gate, up), self.w[p + "w_down"]))
        x = rms_norm(x, self.w["final_norm"], c.rms_eps)
        return matmul(x, transpose(self.w["tok_embed"]))

    def to_numpy_model(self) -> AuroTransformer:
        return AuroTransformer(self.config, weights={k: v.data.copy() for k, v in self.w.items()})


class AdamW:
    def __init__(self, params: List[Tensor], lr=3e-3, betas=(0.9, 0.95), eps=1e-8, wd=0.0):
        self.params = params
        self.lr = lr
        self.b1, self.b2 = betas
        self.eps = eps
        self.wd = wd
        self.m = [np.zeros_like(p.data) for p in params]
        self.v = [np.zeros_like(p.data) for p in params]
        self.t = 0

    def step(self):
        self.t += 1
        total = 0.0
        for p in self.params:
            if p.grad is not None:
                total += float(np.sum(p.grad * p.grad))
        scale = min(1.0, 1.0 / (np.sqrt(total) + 1e-8))
        for i, p in enumerate(self.params):
            if p.grad is None:
                continue
            g = p.grad * scale
            if self.wd:
                g = g + self.wd * p.data
            self.m[i] = self.b1 * self.m[i] + (1 - self.b1) * g
            self.v[i] = self.b2 * self.v[i] + (1 - self.b2) * (g * g)
            mhat = self.m[i] / (1 - self.b1**self.t)
            vhat = self.v[i] / (1 - self.b2**self.t)
            p.data = (p.data - self.lr * mhat / (np.sqrt(vhat) + self.eps)).astype(np.float32)


@dataclass
class TrainResult:
    steps: int
    losses: List[float]
    final_loss: float
    export_path: str
    sample: str
    seconds: float


class AuroTrainer:
    def __init__(self, lr: float = 8e-3, seed: int = 7, **cfg_kw):
        # MHA (n_heads == n_kv_heads) for correct pure-autograd train
        defaults = dict(
            vocab_size=256,
            hidden_size=64,
            n_layers=2,
            n_heads=4,
            n_kv_heads=4,
            max_seq_len=128,
            ffn_multiple=4,
            tie_embeddings=True,
        )
        defaults.update(cfg_kw)
        self.config = AuroConfig(**defaults)
        self.model = TrainableAuro(self.config, seed=seed)
        self.opt = AdamW(self.model.parameters(), lr=lr, wd=0.0)

    def train_text(self, corpus: str = ELEMENTS, steps: int = 800, seq_len: int = 64) -> TrainResult:
        raw = (corpus or ELEMENTS).encode("utf-8")
        raw = (raw + b" ") * 4
        data = np.frombuffer(memoryview(raw), dtype=np.uint8).astype(np.int64)
        seq_len = min(seq_len, self.config.max_seq_len - 1, len(data) - 2)
        span = max(1, len(data) - seq_len - 1)
        losses: List[float] = []
        t0 = time.time()
        for step in range(steps):
            i = (step * 2) % span
            chunk = data[i : i + seq_len + 1]
            inp = chunk[:-1].tolist()
            tgt = chunk[1:]
            self.model.zero_grad()
            logits = self.model.forward_logits(inp)
            loss = cross_entropy(logits, tgt)
            loss.backward()
            self.opt.step()
            losses.append(float(loss.data))
            if step % max(1, steps // 10) == 0 or step == steps - 1:
                print(f"step {step:4d} loss {losses[-1]:.4f}", flush=True)
        np_model = self.model.to_numpy_model()
        path = export_model(np_model, WEB_MODEL)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["note"] = (
            f"POCKET-trained Auro (pure autograd CE+AdamW). steps={steps} "
            f"final={losses[-1]:.4f} min={min(losses):.4f}"
        )
        payload["trained"] = True
        payload["final_loss"] = losses[-1]
        payload["min_loss"] = min(losses)
        path.write_text(json.dumps(payload), encoding="utf-8")
        sample = self.sample_greedy("hydrogen", 120)
        return TrainResult(
            steps=steps,
            losses=losses,
            final_loss=losses[-1],
            export_path=str(path),
            sample=sample,
            seconds=round(time.time() - t0, 2),
        )

    def sample_greedy(self, prompt: str, max_new: int = 80) -> str:
        m = self.model.to_numpy_model()
        ids = list(prompt.encode("utf-8"))
        out = m.generate(ids, max_new_tokens=max_new, temperature=0.0)
        return bytes(min(255, max(0, i)) for i in out).decode("utf-8", errors="replace")


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--steps", type=int, default=800)
    ap.add_argument("--seq", type=int, default=64)
    ap.add_argument("--lr", type=float, default=8e-3)
    args = ap.parse_args()
    tr = AuroTrainer(lr=args.lr)
    r = tr.train_text(ELEMENTS, steps=args.steps, seq_len=args.seq)
    print("final_loss", r.final_loss, "min", min(r.losses))
    print("sample:", r.sample)
    print("exported", r.export_path, "sec", r.seconds)


if __name__ == "__main__":
    main()
