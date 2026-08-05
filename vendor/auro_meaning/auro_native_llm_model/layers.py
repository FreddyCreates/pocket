"""Core Auro architecture primitives, in pure NumPy.

Four building blocks, each matching the target model card:

  * ``rms_norm``        — RMSNorm (no mean-subtraction, scale-only)
  * ``rope`` helpers    — rotary position embeddings applied to q/k
  * ``grouped_query_attention`` — GQA: fewer kv heads than query heads
  * ``swiglu``          — SwiGLU feed-forward (SiLU gate * up, then down)

These are written for clarity and correctness at small scale, and are the exact
operations the WebGPU cluster matmul substrate accelerates when scaled.
"""

from __future__ import annotations

import numpy as np


# --- normalization -----------------------------------------------------------

def rms_norm(x: np.ndarray, weight: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """RMSNorm over the last axis: x / sqrt(mean(x^2) + eps) * weight."""
    ms = np.mean(np.square(x), axis=-1, keepdims=True)
    return x / np.sqrt(ms + eps) * weight


# --- rotary position embeddings (RoPE) --------------------------------------

def rope_frequencies(head_dim: int, seq_len: int, theta: float = 10000.0):
    """Precompute cos/sin tables of shape (seq_len, head_dim)."""
    if head_dim % 2 != 0:
        raise ValueError("head_dim must be even for RoPE")
    inv_freq = 1.0 / (theta ** (np.arange(0, head_dim, 2, dtype=np.float64) / head_dim))
    pos = np.arange(seq_len, dtype=np.float64)
    freqs = np.outer(pos, inv_freq)            # (seq_len, head_dim/2)
    emb = np.concatenate([freqs, freqs], axis=-1)  # (seq_len, head_dim)
    return np.cos(emb), np.sin(emb)


def _rotate_half(x: np.ndarray) -> np.ndarray:
    half = x.shape[-1] // 2
    x1, x2 = x[..., :half], x[..., half:]
    return np.concatenate([-x2, x1], axis=-1)


def apply_rope(x: np.ndarray, cos: np.ndarray, sin: np.ndarray) -> np.ndarray:
    """Apply RoPE to x of shape (..., seq_len, head_dim).

    cos/sin are (seq_len, head_dim); broadcasting handles the head axis.
    """
    seq_len = x.shape[-2]
    cos = cos[:seq_len]
    sin = sin[:seq_len]
    # shape cos/sin for (heads, seq, dim) broadcasting
    while cos.ndim < x.ndim:
        cos = cos[None, ...]
        sin = sin[None, ...]
    return x * cos + _rotate_half(x) * sin


# --- attention ---------------------------------------------------------------

def softmax(x: np.ndarray, axis: int = -1) -> np.ndarray:
    x = x - np.max(x, axis=axis, keepdims=True)
    e = np.exp(x)
    return e / np.sum(e, axis=axis, keepdims=True)


def repeat_kv(x: np.ndarray, n_rep: int) -> np.ndarray:
    """Expand (n_kv_heads, seq, head_dim) -> (n_kv_heads*n_rep, seq, head_dim).

    This is the GQA broadcast: each kv head is shared by n_rep query heads.
    """
    if n_rep == 1:
        return x
    n_kv, seq, hd = x.shape
    return np.repeat(x, n_rep, axis=0)


def grouped_query_attention(q, k, v, cos, sin, n_rep, causal=True):
    """One GQA layer.

    Shapes:
      q: (n_heads,    seq, head_dim)
      k: (n_kv_heads, seq, head_dim)
      v: (n_kv_heads, seq, head_dim)
    Returns: (n_heads, seq, head_dim)
    """
    q = apply_rope(q, cos, sin)
    k = apply_rope(k, cos, sin)
    k = repeat_kv(k, n_rep)      # -> (n_heads, seq, head_dim)
    v = repeat_kv(v, n_rep)
    head_dim = q.shape[-1]

    # scores: (n_heads, seq, seq)
    scores = np.einsum("hqd,hkd->hqk", q, k) / np.sqrt(head_dim)
    if causal:
        seq = scores.shape[-1]
        mask = np.triu(np.ones((seq, seq), dtype=bool), k=1)
        scores = np.where(mask[None, :, :], -1e30, scores)
    attn = softmax(scores, axis=-1)
    return np.einsum("hqk,hkd->hqd", attn, v)


# --- feed-forward ------------------------------------------------------------

def silu(x: np.ndarray) -> np.ndarray:
    return x / (1.0 + np.exp(-x))


def swiglu(x, w_gate, w_up, w_down):
    """SwiGLU FFN: down( silu(x @ gate) * (x @ up) ).

    x: (seq, hidden); w_gate/w_up: (hidden, inter); w_down: (inter, hidden)
    """
    gate = silu(x @ w_gate)
    up = x @ w_up
    return (gate * up) @ w_down
