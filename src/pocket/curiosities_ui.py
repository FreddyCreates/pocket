"""Curiosities — the features you didn't ask for (until now)."""

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>POCKET · Curiosities</title>
<style>
:root{--bg:#07070a;--panel:#121218;--line:rgba(255,255,255,.08);--text:#e8e8ed;--muted:#8b8b9a;--fg:#fafafa;--accent:#10a37f;--violet:#a78bfa;--pink:#f472b6;--amber:#fbbf24}
*{box-sizing:border-box}body{margin:0;font-family:ui-sans-serif,system-ui,sans-serif;background:var(--bg);color:var(--text)}
a{color:var(--accent);text-decoration:none}
.top{display:flex;gap:12px;align-items:center;padding:12px 18px;border-bottom:1px solid var(--line)}
.mark{width:28px;height:28px;border-radius:9px;background:linear-gradient(145deg,#10a37f,#7c3aed);color:#041;display:grid;place-items:center;font-weight:800}
.wrap{max-width:1100px;margin:0 auto;padding:22px 18px 80px}
h1{letter-spacing:-.04em;color:var(--fg);margin:0 0 8px}
.lead{color:var(--muted);max-width:640px;line-height:1.5}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px;margin-top:22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px}
.card h2{margin:0 0 6px;font-size:15px;color:var(--fg)}
.card p{margin:0 0 12px;font-size:13px;color:var(--muted);line-height:1.45}
.btn{border:0;border-radius:10px;padding:9px 12px;font-weight:700;font-size:12.5px;cursor:pointer;margin:0 6px 6px 0}
.btn-p{background:var(--accent);color:#041}
.btn-g{background:transparent;border:1px solid var(--line);color:var(--fg)}
.btn-v{background:linear-gradient(135deg,#7c3aed,#db2777);color:#fff}
input,textarea{width:100%;background:#0c0c10;border:1px solid var(--line);border-radius:10px;padding:10px;color:var(--fg);font:inherit;margin:6px 0 10px}
pre{background:#0a0a0c;border:1px solid var(--line);border-radius:10px;padding:10px;font-size:11px;max-height:160px;overflow:auto;color:#b7f0c6;white-space:pre-wrap}
.pill{font-size:10px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--violet)}
</style>
</head>
<body>
<header class="top">
  <div class="mark">P</div>
  <b style="color:#fafafa">Curiosities</b>
  <a href="/desk">Desk</a>
  <a href="/work">Work Studio</a>
  <a href="/phone">Phone</a>
  <a href="/docs/hub">Docs</a>
</header>
<main class="wrap">
  <div class="pill">features you didn't order</div>
  <h1>Strange powers of a host co-pilot</h1>
  <p class="lead">Dream while idle. Duel two agents. Bury time capsules. Mint proof. Stumble on serendipity.</p>
  <div class="grid">
    <section class="card">
      <h2>🌙 Dream Mode</h2>
      <p>When the lab goes quiet, Subcortex consolidates wiki, world model, and odd links into a dream journal — not chat spam.</p>
      <button class="btn btn-p" onclick="dreamNow()">Dream now</button>
      <button class="btn btn-g" onclick="dreamStatus()">Status</button>
      <pre id="dreamOut">—</pre>
    </section>
    <section class="card">
      <h2>⚔️ Agent Duels</h2>
      <p>FORGE vs AESTHETE vs SENTINEL propose; ARCHON judges. Winner's plan is saved with a receipt.</p>
      <textarea id="duelQ" rows="2" placeholder="How should we harden market seat isolation without killing founder power?"></textarea>
      <button class="btn btn-v" onclick="runDuel()">Start duel</button>
      <pre id="duelOut">—</pre>
    </section>
    <section class="card">
      <h2>⏳ Time Capsules</h2>
      <p>Leave instructions for future-you. Fire after N seconds, on file change, or when idle.</p>
      <input id="capMsg" placeholder="Message / challenge for the future"/>
      <input id="capSec" type="number" placeholder="After seconds (e.g. 120)" value="120"/>
      <select id="capAct"><option value="note">Note</option><option value="dream">Dream</option><option value="duel">Duel</option><option value="build">Build loop</option></select>
      <button class="btn btn-p" onclick="armCapsule()">Arm capsule</button>
      <button class="btn btn-g" onclick="listCapsules()">List</button>
      <pre id="capOut">—</pre>
    </section>
    <section class="card">
      <h2>✨ Serendipity</h2>
      <p>Unexpected adjacency across wiki files, facts, dreams, and builds.</p>
      <button class="btn btn-p" onclick="serendipity()">Find links</button>
      <pre id="serOut">—</pre>
    </section>
    <section class="card">
      <h2>🔗 Proof Chain</h2>
      <p>Hash-linked local receipts for dreams, duels, ships, capsules — show your work happened.</p>
      <button class="btn btn-p" onclick="proofs()">Ledger</button>
      <button class="btn btn-g" onclick="verifyProof()">Verify</button>
      <pre id="proofOut">—</pre>
    </section>
  </div>
</main>
<script>
let token=localStorage.getItem('pocket_token')||'';
function headers(){const h={'Content-Type':'application/json'}; if(token){h.Authorization='Bearer '+token; h['X-Pocket-Token']=token;} return h;}
async function api(path, opts={}){
  const r=await fetch(path,{...opts,headers:{...headers(),...(opts.headers||{})}});
  const t=await r.text(); let j={}; try{j=t?JSON.parse(t):{}}catch(_){j={raw:t}}
  if(!r.ok) throw new Error(j.error||j.message||r.status); return j;
}
(async()=>{ try{ const r=await fetch('/v1/auth/desktop',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}); const j=await r.json(); if(j.token){token=j.token; localStorage.setItem('pocket_token',token);} }catch(_){}})();
async function dreamNow(){ try{ const j=await api('/v1/dreams/now',{method:'POST',body:'{}'}); $('dreamOut').textContent=JSON.stringify(j.dream||j,null,2);}catch(e){$('dreamOut').textContent=e.message}}
async function dreamStatus(){ try{ $('dreamOut').textContent=JSON.stringify(await api('/v1/dreams'),null,2);}catch(e){$('dreamOut').textContent=e.message}}
async function runDuel(){ try{ const j=await api('/v1/duels',{method:'POST',body:JSON.stringify({challenge:$('duelQ').value})}); $('duelOut').textContent=(j.verdict&&j.verdict.rationale)+'\n\n'+(j.verdict&&j.verdict.winning_plan||'').slice(0,1200);}catch(e){$('duelOut').textContent=e.message}}
async function armCapsule(){ try{ const j=await api('/v1/capsules',{method:'POST',body:JSON.stringify({message:$('capMsg').value, after_sec:Number($('capSec').value||120), action:$('capAct').value})}); $('capOut').textContent=JSON.stringify(j,null,2);}catch(e){$('capOut').textContent=e.message}}
async function listCapsules(){ try{ $('capOut').textContent=JSON.stringify(await api('/v1/capsules'),null,2);}catch(e){$('capOut').textContent=e.message}}
async function serendipity(){ try{ const j=await api('/v1/serendipity'); $('serOut').textContent=(j.links||[]).map(l=>l.a+' ↔ '+l.b+'\n  '+l.why).join('\n\n')||'No links yet — index more wiki / ship more.';}catch(e){$('serOut').textContent=e.message}}
async function proofs(){ try{ $('proofOut').textContent=JSON.stringify(await api('/v1/proofs'),null,2);}catch(e){$('proofOut').textContent=e.message}}
async function verifyProof(){ try{ $('proofOut').textContent=JSON.stringify(await api('/v1/proofs/verify'),null,2);}catch(e){$('proofOut').textContent=e.message}}
const $=id=>document.getElementById(id);
</script>
</body>
</html>
"""


def curiosities_html() -> str:
    return HTML
