/**
 * auro.js — a portable, dependency-free browser/Node runtime for the Auro
 * decoder-only architecture: RMSNorm + RoPE + grouped-query attention + SwiGLU.
 *
 * This is the piece of Auro-14B you can drop into any web app (Pocket, an
 * Electron renderer, a plain page). Load a model exported by
 * `auro_native_llm.model.export_web` and the SAME forward pass the NumPy
 * reference runs executes here, in the browser, with matching math.
 *
 *   import { AuroModel } from './auro.js';
 *   const model = await AuroModel.load('./model.json');
 *   const logits = model.forward([1, 2, 3, 4]);          // Float32Array (seq*vocab)
 *   const out = model.generate([1, 2, 3], { maxNewTokens: 8, temperature: 0 });
 *
 * It is intentionally plain JS (typed arrays, no WebGPU required) so it runs
 * anywhere. When a WebGPU cluster node is present, swap `matmul` for the GPU
 * kernel in webgpu_cluster/node.html — the contract is identical.
 *
 * Not a trained checkpoint. This runs whatever weights you export: an untrained
 * scaffold, or a small model you actually trained.
 */

// --- tiny linear-algebra core (row-major Float32Array) ----------------------

// C(m x n) = A(m x k) @ B(k x n)
export function matmul(A, B, m, k, n) {
  const C = new Float32Array(m * n);
  for (let i = 0; i < m; i++) {
    const aOff = i * k;
    const cOff = i * n;
    for (let p = 0; p < k; p++) {
      const a = A[aOff + p];
      if (a === 0) continue;
      const bOff = p * n;
      for (let j = 0; j < n; j++) C[cOff + j] += a * B[bOff + j];
    }
  }
  return C;
}

function rmsNorm(x, weight, rows, dim, eps) {
  const out = new Float32Array(rows * dim);
  for (let r = 0; r < rows; r++) {
    const off = r * dim;
    let ss = 0;
    for (let d = 0; d < dim; d++) ss += x[off + d] * x[off + d];
    const scale = 1 / Math.sqrt(ss / dim + eps);
    for (let d = 0; d < dim; d++) out[off + d] = x[off + d] * scale * weight[d];
  }
  return out;
}

function silu(v) { return v / (1 + Math.exp(-v)); }

function softmaxInPlace(arr, off, len) {
  let mx = -Infinity;
  for (let i = 0; i < len; i++) mx = Math.max(mx, arr[off + i]);
  let sum = 0;
  for (let i = 0; i < len; i++) { const e = Math.exp(arr[off + i] - mx); arr[off + i] = e; sum += e; }
  for (let i = 0; i < len; i++) arr[off + i] /= sum;
}

// --- RoPE tables -------------------------------------------------------------

function ropeTables(headDim, seqLen, theta) {
  const half = headDim / 2;
  const cos = new Float32Array(seqLen * headDim);
  const sin = new Float32Array(seqLen * headDim);
  for (let pos = 0; pos < seqLen; pos++) {
    for (let i = 0; i < half; i++) {
      const freq = 1 / Math.pow(theta, (2 * i) / headDim);
      const ang = pos * freq;
      const c = Math.cos(ang), s = Math.sin(ang);
      // layout matches numpy concat([freqs, freqs]): index i and i+half share angle
      cos[pos * headDim + i] = c;       cos[pos * headDim + i + half] = c;
      sin[pos * headDim + i] = s;       sin[pos * headDim + i + half] = s;
    }
  }
  return { cos, sin, half };
}

// apply RoPE to one head vector (length headDim) at position `pos`, in place
function applyRope(vec, off, pos, headDim, tables) {
  const { cos, sin, half } = tables;
  const cOff = pos * headDim;
  const tmp = new Float32Array(headDim);
  for (let d = 0; d < headDim; d++) tmp[d] = vec[off + d];
  for (let d = 0; d < headDim; d++) {
    // rotate_half: [-x2, x1]
    const rot = d < half ? -tmp[d + half] : tmp[d - half];
    vec[off + d] = tmp[d] * cos[cOff + d] + rot * sin[cOff + d];
  }
}

// --- the model ---------------------------------------------------------------

export class AuroModel {
  constructor(config, weights) {
    this.c = normalizeConfig(config);
    this.w = weights;               // name -> Float32Array (flat, row-major)
    const c = this.c;
    this.tables = ropeTables(c.head_dim, c.max_seq_len, c.rope_theta);
  }

  static async load(url) {
    const res = await fetch(url);
    const payload = await res.json();
    return AuroModel.fromPayload(payload);
  }

  static fromPayload(payload) {
    const weights = {};
    for (const [name, w] of Object.entries(payload.weights)) {
      weights[name] = { data: Float32Array.from(w.data), shape: w.shape };
    }
    return new AuroModel(payload.config, weights);
  }

  _mat(name) { return this.w[name].data; }

  /** logits: Float32Array of length seq*vocab (row-major). */
  forward(tokenIds) {
    const c = this.c;
    const seq = tokenIds.length;
    if (seq > c.max_seq_len) throw new Error(`sequence ${seq} exceeds max_seq_len ${c.max_seq_len}`);
    const H = c.hidden_size, D = c.head_dim, HD = c.n_heads, KV = c.n_kv_heads;
    const REP = HD / KV, kvDim = KV * D;

    // embedding lookup
    const embed = this._mat('tok_embed');
    let x = new Float32Array(seq * H);
    for (let t = 0; t < seq; t++)
      x.set(embed.subarray(tokenIds[t] * H, tokenIds[t] * H + H), t * H);

    for (let l = 0; l < c.n_layers; l++) {
      const p = `layers.${l}.`;
      // --- attention (pre-norm, residual) ---
      const hn = rmsNorm(x, this._mat(p + 'attn_norm'), seq, H, c.rms_eps);
      const q = matmul(hn, this._mat(p + 'wq'), seq, H, H);        // (seq, H)
      const k = matmul(hn, this._mat(p + 'wk'), seq, H, kvDim);     // (seq, kvDim)
      const v = matmul(hn, this._mat(p + 'wv'), seq, H, kvDim);

      // apply RoPE per head
      for (let t = 0; t < seq; t++) {
        for (let h = 0; h < HD; h++) applyRope(q, t * H + h * D, t, D, this.tables);
        for (let h = 0; h < KV; h++) applyRope(k, t * kvDim + h * D, t, D, this.tables);
      }

      const attnOut = new Float32Array(seq * H);
      const scores = new Float32Array(seq);
      for (let h = 0; h < HD; h++) {
        const kvh = Math.floor(h / REP);         // GQA: which kv head this query head reads
        for (let ti = 0; ti < seq; ti++) {
          const qOff = ti * H + h * D;
          // scores over keys 0..ti (causal)
          for (let tj = 0; tj <= ti; tj++) {
            const kOff = tj * kvDim + kvh * D;
            let dot = 0;
            for (let d = 0; d < D; d++) dot += q[qOff + d] * k[kOff + d];
            scores[tj] = dot / Math.sqrt(D);
          }
          softmaxInPlace(scores, 0, ti + 1);
          // weighted sum of values -> attnOut
          const oOff = ti * H + h * D;
          for (let tj = 0; tj <= ti; tj++) {
            const a = scores[tj];
            const vOff = tj * kvDim + kvh * D;
            for (let d = 0; d < D; d++) attnOut[oOff + d] += a * v[vOff + d];
          }
        }
      }
      const proj = matmul(attnOut, this._mat(p + 'wo'), seq, H, H);
      for (let i = 0; i < x.length; i++) x[i] += proj[i];

      // --- feed-forward SwiGLU (pre-norm, residual) ---
      const fn = rmsNorm(x, this._mat(p + 'ffn_norm'), seq, H, c.rms_eps);
      const inter = this.w[p + 'w_gate'].shape[1];
      const gate = matmul(fn, this._mat(p + 'w_gate'), seq, H, inter);
      const up = matmul(fn, this._mat(p + 'w_up'), seq, H, inter);
      const act = new Float32Array(seq * inter);
      for (let i = 0; i < act.length; i++) act[i] = silu(gate[i]) * up[i];
      const down = matmul(act, this._mat(p + 'w_down'), seq, inter, H);
      for (let i = 0; i < x.length; i++) x[i] += down[i];
    }

    x = rmsNorm(x, this._mat('final_norm'), seq, H, c.rms_eps);

    // lm head: tied (embed^T) or separate
    const vocab = c.vocab_size;
    const logits = new Float32Array(seq * vocab);
    if (c.tie_embeddings) {
      const embedW = this._mat('tok_embed');  // (vocab, H)
      for (let t = 0; t < seq; t++) {
        const xOff = t * H;
        for (let vtok = 0; vtok < vocab; vtok++) {
          let dot = 0; const eOff = vtok * H;
          for (let d = 0; d < H; d++) dot += x[xOff + d] * embedW[eOff + d];
          logits[t * vocab + vtok] = dot;
        }
      }
    } else {
      logits.set(matmul(x, this._mat('lm_head'), seq, H, vocab));
    }
    return logits;
  }

  /** Autoregressive generation. temperature=0 -> greedy/deterministic. */
  generate(promptIds, { maxNewTokens = 16, temperature = 0, topK = 0, rng = Math.random } = {}) {
    const vocab = this.c.vocab_size;
    const ids = promptIds.slice();
    for (let step = 0; step < maxNewTokens; step++) {
      const ctx = ids.slice(-this.c.max_seq_len);
      const logits = this.forward(ctx);
      const last = logits.subarray((ctx.length - 1) * vocab, ctx.length * vocab);
      ids.push(sampleToken(last, vocab, temperature, topK, rng));
    }
    return ids;
  }
}

function sampleToken(logits, vocab, temperature, topK, rng) {
  if (temperature <= 0) {
    let best = 0, bestV = -Infinity;
    for (let i = 0; i < vocab; i++) if (logits[i] > bestV) { bestV = logits[i]; best = i; }
    return best;
  }
  const scaled = new Float32Array(vocab);
  for (let i = 0; i < vocab; i++) scaled[i] = logits[i] / temperature;
  if (topK && topK < vocab) {
    const idx = Array.from(scaled.keys()).sort((a, b) => scaled[b] - scaled[a]);
    const keep = new Set(idx.slice(0, topK));
    for (let i = 0; i < vocab; i++) if (!keep.has(i)) scaled[i] = -Infinity;
  }
  softmaxInPlace(scaled, 0, vocab);
  let r = rng(), acc = 0;
  for (let i = 0; i < vocab; i++) { acc += scaled[i]; if (r <= acc) return i; }
  return vocab - 1;
}

function normalizeConfig(cfg) {
  const c = { ...cfg };
  c.head_dim = c.hidden_size / c.n_heads;
  if (c.rms_eps === undefined) c.rms_eps = 1e-6;
  if (c.rope_theta === undefined) c.rope_theta = 10000.0;
  if (c.tie_embeddings === undefined) c.tie_embeddings = true;
  return c;
}

// Node/CommonJS interop for the parity test (harmless in the browser).
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { AuroModel, matmul };
}
