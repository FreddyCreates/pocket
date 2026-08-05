"""Reverse-mode autograd on NumPy — real backprop, not hand-waved.

Ops record backward closures: matmul, broadcast add/mul, reshape/transpose,
embedding gather, softmax, SiLU, log_softmax / cross-entropy.
"""

from __future__ import annotations

import numpy as np


class Tensor:
    __slots__ = ("data", "grad", "requires_grad", "_backward", "_prev")

    def __init__(self, data, requires_grad: bool = False):
        self.data = np.asarray(data, dtype=np.float32)
        self.grad = None
        self.requires_grad = bool(requires_grad)
        self._backward = lambda: None
        self._prev: tuple = ()

    # --- plumbing -----------------------------------------------------------
    def zero_grad(self):
        self.grad = None

    def _ensure_grad(self):
        if self.grad is None:
            self.grad = np.zeros_like(self.data)

    def backward(self, grad=None):
        if grad is None:
            if self.data.size != 1:
                raise RuntimeError("backward() for non-scalar needs grad")
            grad = np.ones_like(self.data)
        self._ensure_grad()
        self.grad = self.grad + np.asarray(grad, dtype=np.float32)
        # topo sort
        seen, order = set(), []

        def build(t: "Tensor"):
            if id(t) in seen:
                return
            seen.add(id(t))
            for p in t._prev:
                build(p)
            order.append(t)

        build(self)
        for t in reversed(order):
            t._backward()

    def numpy(self):
        return self.data

    def __repr__(self):
        return f"Tensor(shape={self.data.shape}, requires_grad={self.requires_grad})"


def _as_tensor(x) -> Tensor:
    return x if isinstance(x, Tensor) else Tensor(x, requires_grad=False)


def matmul(a: Tensor, b: Tensor) -> Tensor:
    a, b = _as_tensor(a), _as_tensor(b)
    out = Tensor(a.data @ b.data, requires_grad=a.requires_grad or b.requires_grad)

    def _bw():
        if out.grad is None:
            return
        g = out.grad
        if a.requires_grad:
            a._ensure_grad()
            a.grad = a.grad + g @ b.data.T
        if b.requires_grad:
            b._ensure_grad()
            b.grad = b.grad + a.data.T @ g

    out._backward = _bw
    out._prev = (a, b)
    return out


def add(a: Tensor, b: Tensor) -> Tensor:
    a, b = _as_tensor(a), _as_tensor(b)
    out = Tensor(a.data + b.data, requires_grad=a.requires_grad or b.requires_grad)

    def _bw():
        if out.grad is None:
            return
        g = out.grad
        if a.requires_grad:
            a._ensure_grad()
            a.grad = a.grad + _unbroadcast(g, a.data.shape)
        if b.requires_grad:
            b._ensure_grad()
            b.grad = b.grad + _unbroadcast(g, b.data.shape)

    out._backward = _bw
    out._prev = (a, b)
    return out


def mul(a: Tensor, b: Tensor) -> Tensor:
    a, b = _as_tensor(a), _as_tensor(b)
    out = Tensor(a.data * b.data, requires_grad=a.requires_grad or b.requires_grad)

    def _bw():
        if out.grad is None:
            return
        g = out.grad
        if a.requires_grad:
            a._ensure_grad()
            a.grad = a.grad + _unbroadcast(g * b.data, a.data.shape)
        if b.requires_grad:
            b._ensure_grad()
            b.grad = b.grad + _unbroadcast(g * a.data, b.data.shape)

    out._backward = _bw
    out._prev = (a, b)
    return out


def _unbroadcast(grad: np.ndarray, shape: tuple) -> np.ndarray:
    g = grad
    while g.ndim > len(shape):
        g = g.sum(axis=0)
    for i, (gs, s) in enumerate(zip(g.shape, shape)):
        if s == 1 and gs != 1:
            g = g.sum(axis=i, keepdims=True)
    return g


def reshape(a: Tensor, shape) -> Tensor:
    a = _as_tensor(a)
    out = Tensor(a.data.reshape(shape), requires_grad=a.requires_grad)

    def _bw():
        if out.grad is None or not a.requires_grad:
            return
        a._ensure_grad()
        a.grad = a.grad + out.grad.reshape(a.data.shape)

    out._backward = _bw
    out._prev = (a,)
    return out


def transpose(a: Tensor, axes=None) -> Tensor:
    a = _as_tensor(a)
    out = Tensor(np.transpose(a.data, axes), requires_grad=a.requires_grad)
    inv = None if axes is None else tuple(np.argsort(axes))

    def _bw():
        if out.grad is None or not a.requires_grad:
            return
        a._ensure_grad()
        a.grad = a.grad + np.transpose(out.grad, inv)

    out._backward = _bw
    out._prev = (a,)
    return out


def embedding(weight: Tensor, ids) -> Tensor:
    """weight: (V, D), ids: int array → (..., D)."""
    weight = _as_tensor(weight)
    ids = np.asarray(ids, dtype=np.int64)
    out = Tensor(weight.data[ids], requires_grad=weight.requires_grad)

    def _bw():
        if out.grad is None or not weight.requires_grad:
            return
        weight._ensure_grad()
        np.add.at(weight.grad, ids.reshape(-1), out.grad.reshape(-1, weight.data.shape[-1]))

    out._backward = _bw
    out._prev = (weight,)
    return out


def silu(a: Tensor) -> Tensor:
    """SiLU(x) = x * sigmoid(x)."""
    a = _as_tensor(a)
    s = 1.0 / (1.0 + np.exp(-np.clip(a.data, -40, 40)))
    out = Tensor(a.data * s, requires_grad=a.requires_grad)

    def _bw():
        if out.grad is None or not a.requires_grad:
            return
        a._ensure_grad()
        # d/dx [x σ] = σ + x σ (1-σ)
        a.grad = a.grad + out.grad * (s + a.data * s * (1.0 - s))

    out._backward = _bw
    out._prev = (a,)
    return out


def softmax(a: Tensor, axis: int = -1) -> Tensor:
    a = _as_tensor(a)
    x = a.data - np.max(a.data, axis=axis, keepdims=True)
    e = np.exp(x)
    s = e / np.sum(e, axis=axis, keepdims=True)
    out = Tensor(s, requires_grad=a.requires_grad)

    def _bw():
        if out.grad is None or not a.requires_grad:
            return
        a._ensure_grad()
        # Jacobian: diag(s) - s s^T applied to g
        g = out.grad
        # sum over axis
        dot = np.sum(g * s, axis=axis, keepdims=True)
        a.grad = a.grad + s * (g - dot)

    out._backward = _bw
    out._prev = (a,)
    return out


def log_softmax(a: Tensor, axis: int = -1) -> Tensor:
    a = _as_tensor(a)
    x = a.data - np.max(a.data, axis=axis, keepdims=True)
    log_z = np.log(np.sum(np.exp(x), axis=axis, keepdims=True))
    out = Tensor(x - log_z, requires_grad=a.requires_grad)

    def _bw():
        if out.grad is None or not a.requires_grad:
            return
        a._ensure_grad()
        s = np.exp(out.data)
        a.grad = a.grad + out.grad - s * np.sum(out.grad, axis=axis, keepdims=True)

    out._backward = _bw
    out._prev = (a,)
    return out


def cross_entropy(logits: Tensor, targets) -> Tensor:
    """Mean NLL. logits (N, V) or (T, V); targets int (N,) or (T,)."""
    logits = _as_tensor(logits)
    targets = np.asarray(targets, dtype=np.int64)
    flat = logits.data.reshape(-1, logits.data.shape[-1])
    t = targets.reshape(-1)
    n = t.shape[0]
    logp = log_softmax(Tensor(flat, requires_grad=logits.requires_grad), axis=-1)
    # wire through
    logp.requires_grad = logits.requires_grad
    # rebuild with graph from logits
    ls = log_softmax(logits, axis=-1)
    # gather
    rows = np.arange(n)
    flat_ls = ls.data.reshape(n, -1)
    nll = -flat_ls[rows, t]
    loss_data = np.mean(nll).astype(np.float32)
    out = Tensor(loss_data, requires_grad=logits.requires_grad)

    def _bw():
        if out.grad is None or not logits.requires_grad:
            return
        logits._ensure_grad()
        # dL/dlogits = (softmax - onehot) / N
        s = np.exp(ls.data.reshape(n, -1) - np.max(ls.data.reshape(n, -1), axis=-1, keepdims=True))
        # use true softmax from logits
        x = logits.data.reshape(n, -1)
        x = x - np.max(x, axis=-1, keepdims=True)
        e = np.exp(x)
        s = e / np.sum(e, axis=-1, keepdims=True)
        s[rows, t] -= 1.0
        g = (s / n) * float(np.asarray(out.grad).reshape(()))
        logits.grad = logits.grad + g.reshape(logits.data.shape)

    out._backward = _bw
    out._prev = (logits,)
    return out


def sum(a: Tensor, axis=None, keepdims=False) -> Tensor:
    a = _as_tensor(a)
    out = Tensor(np.sum(a.data, axis=axis, keepdims=keepdims), requires_grad=a.requires_grad)

    def _bw():
        if out.grad is None or not a.requires_grad:
            return
        a._ensure_grad()
        g = out.grad
        if axis is not None and not keepdims:
            g = np.expand_dims(g, axis=axis)
        a.grad = a.grad + np.broadcast_to(g, a.data.shape)

    out._backward = _bw
    out._prev = (a,)
    return out


def mean_sq(a: Tensor, axis=-1, keepdims=True) -> Tensor:
    a = _as_tensor(a)
    out = Tensor(np.mean(np.square(a.data), axis=axis, keepdims=keepdims), requires_grad=a.requires_grad)
    n = a.data.shape[axis] if axis is not None else a.data.size

    def _bw():
        if out.grad is None or not a.requires_grad:
            return
        a._ensure_grad()
        g = out.grad
        if axis is not None and not keepdims:
            g = np.expand_dims(g, axis)
        a.grad = a.grad + (2.0 / n) * a.data * np.broadcast_to(g, a.data.shape)

    out._backward = _bw
    out._prev = (a,)
    return out


def rms_norm(x: Tensor, weight: Tensor, eps: float = 1e-6) -> Tensor:
    """Autograd RMSNorm."""
    # y = x / sqrt(mean(x^2)+eps) * w
    ms = mean_sq(x, axis=-1, keepdims=True)
    # inv_rms via ops
    inv = Tensor(1.0 / np.sqrt(ms.data + eps), requires_grad=x.requires_grad)

    def _bw_inv():
        if inv.grad is None:
            return
        # d/d(ms) of (ms+eps)^-0.5 = -0.5 (ms+eps)^-1.5
        if ms.requires_grad or x.requires_grad:
            ms._ensure_grad() if False else None
        # reconnect: we'll do explicit backward on composed
        pass

    # explicit composite backward
    scale = inv.data
    y_data = x.data * scale * weight.data
    out = Tensor(y_data, requires_grad=x.requires_grad or weight.requires_grad)

    def _bw():
        if out.grad is None:
            return
        g = out.grad
        # y = x * inv * w, inv = (mean x^2 + eps)^-0.5
        inv_d = 1.0 / np.sqrt(ms.data + eps)
        if weight.requires_grad:
            weight._ensure_grad()
            weight.grad = weight.grad + np.sum(g * x.data * inv_d, axis=tuple(range(g.ndim - 1)), keepdims=g.ndim > 1)
            if weight.grad.shape != weight.data.shape:
                weight.grad = np.sum(g * x.data * inv_d, axis=tuple(range(0, g.ndim - 1)))
        if x.requires_grad:
            x._ensure_grad()
            # dy/dx = inv*w + x * w * d(inv)/dx
            # d(inv)/dx_i = -0.5 (m+eps)^-1.5 * d(m)/dx_i, m = mean x^2, dm/dx_i = 2x_i/n
            n = x.data.shape[-1]
            d_inv_dm = -0.5 * np.power(ms.data + eps, -1.5)
            dm_dx = (2.0 / n) * x.data
            d_inv_dx = d_inv_dm * dm_dx
            x.grad = x.grad + g * (inv_d * weight.data + x.data * weight.data * d_inv_dx)

    out._backward = _bw
    out._prev = (x, weight)
    return out


def gradient_check(fn, x0: np.ndarray, eps: float = 1e-4) -> float:
    """Max relative error between analytic and finite-diff grads."""
    x = Tensor(x0.copy(), requires_grad=True)
    y = fn(x)
    y.backward()
    analytic = x.grad.copy()
    numeric = np.zeros_like(x0)
    flat = x0.reshape(-1)
    num = numeric.reshape(-1)
    ana = analytic.reshape(-1)
    for i in range(flat.size):
        xp = x0.copy().reshape(-1)
        xm = x0.copy().reshape(-1)
        xp[i] += eps
        xm[i] -= eps
        yp = float(fn(Tensor(xp.reshape(x0.shape))).data.reshape(-1)[0] if fn(Tensor(xp.reshape(x0.shape))).data.size == 1 else np.sum(fn(Tensor(xp.reshape(x0.shape))).data))
        # re-eval properly
        def _eval(arr):
            t = fn(Tensor(arr.reshape(x0.shape)))
            return float(np.sum(t.data))

        yp = _eval(xp)
        ym = _eval(xm)
        num[i] = (yp - ym) / (2 * eps)
    rel = np.max(np.abs(ana - num) / (np.abs(ana) + np.abs(num) + 1e-8))
    return float(rel)


def self_test() -> dict:
    rng = np.random.default_rng(0)
    # matmul
    A = rng.standard_normal((4, 5)).astype(np.float32)
    B = rng.standard_normal((5, 3)).astype(np.float32)

    def f_mm(t):
        # t unused shape - check mul+sum
        return sum(mul(t, t))

    x = rng.standard_normal((3, 3)).astype(np.float32) * 0.1
    err_sq = gradient_check(lambda t: sum(mul(t, t)), x)
    # silu
    err_silu = gradient_check(lambda t: sum(silu(t)), x)
    # softmax CE
    logits = Tensor(rng.standard_normal((6, 10)).astype(np.float32), requires_grad=True)
    targets = rng.integers(0, 10, size=(6,))
    loss = cross_entropy(logits, targets)
    loss.backward()
    # finite diff on first logit
    e = 1e-4
    base = float(loss.data)
    L = logits.data.copy()
    L[0, 0] += e
    lp = float(cross_entropy(Tensor(L), targets).data)
    L[0, 0] -= 2 * e
    lm = float(cross_entropy(Tensor(L), targets).data)
    num = (lp - lm) / (2 * e)
    ana = float(logits.grad[0, 0])
    err_ce = abs(ana - num) / (abs(ana) + abs(num) + 1e-8)
    return {
        "ok": err_sq < 1e-3 and err_silu < 1e-3 and err_ce < 1e-3,
        "err_sq": err_sq,
        "err_silu": err_silu,
        "err_ce": err_ce,
    }


if __name__ == "__main__":
    print(self_test())
