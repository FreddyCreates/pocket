# Auro meaning path inside POCKET

## What we integrated (option **b** — into Pocket)

From `Downloads/auro14b_pocket_piece.zip` → `vendor/auro_meaning/`:

| Piece | Role |
|-------|------|
| `auro_native_llm_model/` | NumPy AuroTransformer (RMSNorm/RoPE/GQA/SwiGLU) |
| `auro_web/auro.js` | Browser runtime |
| `auro_web/model.json` | Exported weights (~1.2 MB in this package) |
| `test_auro_architecture.py` | Architecture tests |

## URLs

| | |
|--|--|
| Browser demo | http://127.0.0.1:8787/auro/ |
| Status API | `GET /v1/auro/status` |
| Generate | `POST /v1/auro/generate` `{"ids":[1,2,3]}` or `{"prompt":"…"}` |
| Train hook | `POST /v1/auro/train` `{"corpus":"…","steps":200}` |

Desk session mode **Auro** prefers the meaning model for short prompts; use `native …` for full Auro14B LMR.

## Train loop (built in-tree — not waiting on anyone)

```text
vendor/auro_meaning/autograd.py   # reverse-mode NumPy autograd
vendor/auro_meaning/train_lm.py  # AuroTrainer.train_text → export model.json
```

```powershell
cd vendor/auro_meaning
$env:PYTHONPATH=$PWD
python train_lm.py --steps 1500 --seq 64
```

Or:

```text
POST /v1/auro/train  {"corpus":"hydrogen and helium…", "steps":800}
```

Loss drops from ~5.5 (random over 256 bytes) with real CE+AdamW. Export updates `auro_web/model.json` for `/auro/` browser.

## WebGPU (option a — next)

`auro.js` matmul contract matches the WebGPU cluster path documented in Auro. Next step is swapping matmul, not rewriting the model. POCKET can offload train jobs via Offload + ghost math for hash receipts.

## Verified on integrate

- Host serves `/auro/` public
- NumPy load + generate ids path wired
- Full Auro14B checkpoints still available via native bridge when repo present
