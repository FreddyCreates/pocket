/**
 * parity_check.mjs — prove the JS runtime matches the NumPy reference.
 *
 * Reads a model exported by export_web.py plus a token sequence and the NumPy
 * logits for that sequence, runs auro.js forward, and reports the max abs diff.
 *
 *   node parity_check.mjs <model.json> <expected.json>
 */
import fs from 'fs';
import { AuroModel } from './auro.js';

const [modelPath, expectedPath] = process.argv.slice(2);
const payload = JSON.parse(fs.readFileSync(modelPath, 'utf8'));
const expected = JSON.parse(fs.readFileSync(expectedPath, 'utf8'));

const model = AuroModel.fromPayload(payload);
const logits = model.forward(expected.tokens);
const ref = Float32Array.from(expected.logits);

if (logits.length !== ref.length) {
  console.error(`length mismatch: js=${logits.length} ref=${ref.length}`);
  process.exit(2);
}
let maxDiff = 0;
for (let i = 0; i < ref.length; i++) maxDiff = Math.max(maxDiff, Math.abs(logits[i] - ref[i]));

// also check greedy generation agrees
const gen = model.generate(expected.tokens.slice(0, 3), { maxNewTokens: 5, temperature: 0 });

console.log(JSON.stringify({
  seq: expected.tokens.length,
  vocab: model.c.vocab_size,
  max_abs_logit_diff: maxDiff,
  js_greedy: gen,
  ref_greedy: expected.greedy,
  greedy_match: JSON.stringify(gen) === JSON.stringify(expected.greedy),
}, null, 2));

process.exit(maxDiff < 1e-3 && JSON.stringify(gen) === JSON.stringify(expected.greedy) ? 0 : 1);
