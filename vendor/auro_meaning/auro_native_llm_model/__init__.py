"""Runnable Auro decoder-only transformer architecture (RMSNorm + RoPE + GQA + SwiGLU).

The architecture from the Auro model cards, implemented in pure NumPy so it runs
end-to-end at small scale. Not a trained checkpoint — the shape and the math,
made real and testable.
"""

from .config import AuroConfig
from .transformer import AuroTransformer
from . import layers

__all__ = ["AuroConfig", "AuroTransformer", "layers"]
