"""Tests for the runnable Auro decoder-only architecture (RMSNorm/RoPE/GQA/SwiGLU)."""

import numpy as np
import pytest

from auro_native_llm.model import AuroConfig, AuroTransformer
from auro_native_llm.model.layers import (
    apply_rope,
    grouped_query_attention,
    repeat_kv,
    rms_norm,
    rope_frequencies,
    silu,
    swiglu,
)


# --- primitives --------------------------------------------------------------

def test_rms_norm_is_scale_invariant_in_direction():
    x = np.random.randn(4, 16).astype(np.float32)
    w = np.ones(16, dtype=np.float32)
    y = rms_norm(x, w, 1e-6)
    # each row should have unit root-mean-square (before the weight scaling)
    rms = np.sqrt(np.mean(y ** 2, axis=-1))
    assert np.allclose(rms, 1.0, atol=1e-3)


def test_rope_preserves_norm_and_relative_geometry():
    cos, sin = rope_frequencies(head_dim=8, seq_len=6, theta=10000.0)
    x = np.random.randn(2, 6, 8).astype(np.float32)  # (heads, seq, dim)
    y = apply_rope(x, cos, sin)
    # rotation preserves vector norm per position
    assert np.allclose(np.linalg.norm(x, axis=-1), np.linalg.norm(y, axis=-1), atol=1e-4)


def test_repeat_kv_expands_group_dimension():
    kv = np.random.randn(2, 5, 4).astype(np.float32)  # (n_kv, seq, dim)
    out = repeat_kv(kv, n_rep=3)
    assert out.shape == (6, 5, 4)
    # heads 0,1,2 all copy kv head 0
    assert np.array_equal(out[0], kv[0]) and np.array_equal(out[2], kv[0])
    assert np.array_equal(out[3], kv[1])


def test_gqa_is_causal():
    seq, hd = 5, 8
    q = np.random.randn(4, seq, hd).astype(np.float32)
    k = np.random.randn(2, seq, hd).astype(np.float32)
    v = np.random.randn(2, seq, hd).astype(np.float32)
    cos, sin = rope_frequencies(hd, seq)
    out_full = grouped_query_attention(q, k, v, cos, sin, n_rep=2, causal=True)
    # truncating the future must not change earlier outputs (causality)
    t = 3
    out_trunc = grouped_query_attention(q[:, :t], k[:, :t], v[:, :t], cos, sin, n_rep=2, causal=True)
    assert np.allclose(out_full[:, :t], out_trunc, atol=1e-5)


def test_swiglu_matches_reference():
    x = np.random.randn(3, 8).astype(np.float32)
    wg = np.random.randn(8, 16).astype(np.float32)
    wu = np.random.randn(8, 16).astype(np.float32)
    wd = np.random.randn(16, 8).astype(np.float32)
    got = swiglu(x, wg, wu, wd)
    ref = (silu(x @ wg) * (x @ wu)) @ wd
    assert np.allclose(got, ref, atol=1e-5)
    assert got.shape == (3, 8)


# --- config / param accounting ----------------------------------------------

def test_param_formula_matches_actual_arrays():
    cfg = AuroConfig(vocab_size=200, hidden_size=96, n_layers=3, n_heads=6, n_kv_heads=2)
    model = AuroTransformer(cfg, seed=1)
    assert cfg.param_count() == model.num_parameters()


def test_untied_embeddings_add_lm_head():
    tied = AuroConfig(vocab_size=100, hidden_size=64, n_layers=2, n_heads=4, n_kv_heads=2, tie_embeddings=True)
    untied = AuroConfig(vocab_size=100, hidden_size=64, n_layers=2, n_heads=4, n_kv_heads=2, tie_embeddings=False)
    assert untied.param_count() - tied.param_count() == 100 * 64


def test_dev_14b_config_predicts_about_14b():
    cfg = AuroConfig.from_target_json("native_llm/configs/auro_14b_dev.json")
    # faithful to the target shape
    assert (cfg.hidden_size, cfg.n_layers, cfg.n_heads, cfg.n_kv_heads) == (5120, 48, 40, 8)
    billions = cfg.param_count() / 1e9
    assert 13.0 < billions < 15.0            # lands on the 14B target


def test_gqa_ratio_preserved_when_scaled_down():
    big = AuroConfig.from_target_json("native_llm/configs/auro_14b_dev.json")
    small = big.scaled(n_layers=2, n_kv_heads=2, head_dim=32)
    # same query:kv head ratio as the 14B target (40:8 = 5:1)
    assert big.n_rep == small.n_rep == 5
    assert small.n_heads == 10 and small.n_kv_heads == 2   # 5:1 preserved
    assert small.hidden_size == 320                        # 10 heads * 32 dim
    assert small.hidden_size % small.n_heads == 0
    assert small.n_heads % small.n_kv_heads == 0


# --- full model --------------------------------------------------------------

def _tiny():
    cfg = AuroConfig(vocab_size=64, hidden_size=64, n_layers=3, n_heads=8, n_kv_heads=2, max_seq_len=32)
    return cfg, AuroTransformer(cfg, seed=0)


def test_forward_shape():
    cfg, model = _tiny()
    logits = model.forward([1, 2, 3, 4, 5, 6])
    assert logits.shape == (6, cfg.vocab_size)
    assert np.isfinite(logits).all()


def test_greedy_generation_is_deterministic():
    _, model = _tiny()
    a = model.generate([1, 2, 3], max_new_tokens=8, temperature=0.0)
    b = model.generate([1, 2, 3], max_new_tokens=8, temperature=0.0)
    assert a == b
    assert len(a) == 3 + 8


def test_forward_is_causal_prefix_stable():
    """Logits for a prefix must not depend on tokens appended after it."""
    _, model = _tiny()
    short = model.forward([5, 6, 7])
    long = model.forward([5, 6, 7, 8, 9])
    assert np.allclose(short, long[:3], atol=1e-5)


def test_state_dict_roundtrip():
    _, model = _tiny()
    restored = AuroTransformer.from_state_dict(model.state_dict())
    assert np.allclose(model.forward([1, 2, 3, 4]), restored.forward([1, 2, 3, 4]), atol=1e-6)


def test_sequence_over_max_len_raises():
    cfg, model = _tiny()
    with pytest.raises(ValueError):
        model.forward(list(range(cfg.max_seq_len + 1)))


# --- web export (the Pocket-includable path) --------------------------------

def test_export_web_shape_and_reload(tmp_path):
    """Exported JSON carries every weight with correct shape and reloads exactly."""
    import json
    from auro_native_llm.model.export_web import export_model

    cfg, model = _tiny()
    path = export_model(model, tmp_path / "m.json")
    payload = json.loads(path.read_text())

    assert payload["format"] == "auro.web.v1"
    assert "NOT a trained" not in payload["note"]  # honest wording ("Not a trained checkpoint")
    assert "not a trained" in payload["note"].lower()
    assert payload["config"] == cfg.to_dict()

    # every weight present with a shape whose product matches its flat length
    total = 0
    for name, arr in model.weights.items():
        w = payload["weights"][name]
        assert tuple(w["shape"]) == arr.shape
        assert len(w["data"]) == arr.size
        total += len(w["data"])
    assert total == model.num_parameters()

    # rebuilding a numpy model from the exported flat weights reproduces logits
    rebuilt = {n: np.asarray(w["data"], dtype=np.float32).reshape(w["shape"])
               for n, w in payload["weights"].items()}
    restored = AuroTransformer(cfg, weights=rebuilt)
    # export rounds to 6 decimals; parity holds to ~2e-5 (same as the JS runtime)
    assert np.allclose(model.forward([1, 2, 3, 4]), restored.forward([1, 2, 3, 4]), atol=1e-3)
