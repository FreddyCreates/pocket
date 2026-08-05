# Auro Web — the includable piece of Auro-14B

A portable, dependency-free runtime for the **Auro decoder-only architecture**
(RMSNorm · RoPE · grouped-query attention · SwiGLU). It runs a real forward pass
and autoregressive generation **in the browser** — the piece you can drop into
Pocket (or any web app, Electron renderer, or plain page).

```
auro_web/
├── auro.js          # the runtime (ES module, no dependencies)
├── model.json       # an exported Auro model (config + weights)
├── index.html       # a working demo (generate in-browser)
├── parity_check.mjs # proves JS output == NumPy reference
└── package.json
```

## What it is (and isn't)

- **Is:** the Auro architecture, faithfully — the same math as the NumPy
  reference in `auro_native_llm/model/`. Verified: `auro.js` reproduces the
  reference logits to **1.9e-5** (float32 rounding) and greedy generation
  **matches exactly** (`node parity_check.mjs`).
- **Isn't:** a trained 14B/200B checkpoint. It runs whatever weights you export —
  an untrained scaffold today, a small model you actually train tomorrow. Same
  code path either way.

## Use it in Pocket (3 lines)

```html
<script type="module">
  import { AuroModel } from './auro.js';
  const model = await AuroModel.load('./model.json');
  const out = model.generate([3, 1, 4], { maxNewTokens: 8, temperature: 0.7 });
</script>
```

`AuroModel` API:

| Method | Returns |
|---|---|
| `AuroModel.load(url)` | model (fetches + parses the json) |
| `AuroModel.fromPayload(obj)` | model (from an already-loaded object) |
| `model.forward(tokenIds)` | `Float32Array` of `seq × vocab` logits |
| `model.generate(ids, {maxNewTokens, temperature, topK, rng})` | token id array |

Because it's pure typed-array math with no imports, it works in a Caffeine
frontend, an Electron renderer, or a static page. To try the demo locally:

```bash
cd auro_web && python3 -m http.server 8080   # then open http://localhost:8080
```

## Export your own model

Train or initialize in NumPy, then export one file:

```bash
python3 -m auro_native_llm.model.export_web \
  --out auro_web/model.json --hidden 64 --layers 3 --heads 8 --kv 2 --vocab 48
```

The exporter (`auro_native_llm/model/export_web.py`) writes config + row-major
weights; `auro.js` loads them directly.

## Scaling path

`auro.js` uses a plain CPU `matmul` so it runs everywhere. The matmul contract
is identical to the WebGPU kernel in `../webgpu_cluster/node.html` — swap it in
to run the same forward pass on the GPU, and fan large matmuls out across
browser nodes via `../webgpu_cluster/coordinator.py`. Architecture here,
throughput there.
