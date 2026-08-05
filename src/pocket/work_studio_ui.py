"""Work Studio — designed surface for work types, loops, swarm, dual-loop, world model."""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<meta name="theme-color" content="#07070a"/>
<title>POCKET · Work Studio</title>
<style>
:root{
  --bg:#07070a;--bg2:#0c0c10;--panel:#121218;--panel2:#18181f;
  --line:rgba(255,255,255,.08);--text:#e8e8ed;--muted:#8b8b9a;--fg:#fafafa;
  --accent:#10a37f;--violet:#a78bfa;--pink:#f472b6;--blue:#60a5fa;--amber:#fbbf24;
  --font:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --r:14px;
}
*{box-sizing:border-box}
html,body{height:100%;margin:0}
body{font-family:var(--font);background:var(--bg);color:var(--text);-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
button,input,textarea,select{font:inherit;color:inherit}
button{cursor:pointer;border:0;background:none}
.app{min-height:100%;display:flex;flex-direction:column}
.top{
  display:flex;align-items:center;gap:12px;padding:12px 18px;
  border-bottom:1px solid var(--line);background:rgba(7,7,10,.9);backdrop-filter:blur(16px);position:sticky;top:0;z-index:10
}
.mark{
  width:28px;height:28px;border-radius:9px;display:grid;place-items:center;font-weight:800;font-size:13px;color:#041;
  background:linear-gradient(145deg,var(--accent),#0a7a5f);box-shadow:0 0 0 1px rgba(16,163,127,.35)
}
.brand{font-weight:700;letter-spacing:-.03em;color:var(--fg)}
.brand small{display:block;font-weight:500;font-size:11px;color:var(--muted);letter-spacing:0}
.nav{display:flex;gap:4px;margin-left:12px;flex-wrap:wrap}
.nav a,.nav button{
  padding:7px 12px;border-radius:9px;font-size:12.5px;font-weight:600;color:var(--muted)
}
.nav a:hover,.nav button:hover{color:var(--fg);background:rgba(255,255,255,.04)}
.nav a.on{color:var(--fg);background:var(--panel2)}
.grow{flex:1}
.pill{
  font-size:11px;font-weight:650;padding:4px 10px;border-radius:999px;border:1px solid var(--line);color:var(--muted)
}
.pill.on{color:#6ee7b7;border-color:rgba(16,163,127,.4);background:rgba(16,163,127,.1)}
.pill.warn{color:#fde68a;border-color:rgba(251,191,36,.35)}
.wrap{max-width:1180px;width:100%;margin:0 auto;padding:22px 18px 80px}
.hero{margin-bottom:22px}
.hero h1{margin:0 0 8px;font-size:clamp(24px,3vw,32px);letter-spacing:-.04em;color:var(--fg);font-weight:650}
.hero p{margin:0;max-width:640px;color:var(--muted);line-height:1.55;font-size:14.5px}
.grid{display:grid;grid-template-columns:1.1fr .9fr;gap:16px}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
.card{
  background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:16px 16px 14px
}
.card h2{margin:0 0 4px;font-size:14px;font-weight:650;color:var(--fg);letter-spacing:-.02em}
.card .sub{font-size:12px;color:var(--muted);margin-bottom:12px;line-height:1.4}
.dual{
  display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:8px
}
.sys{
  border-radius:12px;padding:12px;border:1px solid var(--line);background:var(--bg2);min-height:110px
}
.sys.cortex{border-color:rgba(96,165,250,.3);background:linear-gradient(160deg,rgba(96,165,250,.08),transparent)}
.sys.sub{border-color:rgba(167,139,250,.3);background:linear-gradient(160deg,rgba(167,139,250,.08),transparent)}
.sys b{display:block;font-size:12px;margin-bottom:6px}
.sys.cortex b{color:var(--blue)}
.sys.sub b{color:var(--violet)}
.sys p{margin:0;font-size:12px;color:var(--muted);line-height:1.45}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px}
.btn{
  display:inline-flex;align-items:center;gap:6px;padding:9px 14px;border-radius:10px;
  font-size:12.5px;font-weight:700;border:1px solid transparent
}
.btn-primary{background:var(--accent);color:#041}
.btn-primary:hover{filter:brightness(1.06)}
.btn-ghost{border-color:var(--line);color:var(--fg);background:transparent}
.btn-ghost:hover{background:rgba(255,255,255,.04)}
.btn-pink{background:linear-gradient(135deg,#db2777,#7c3aed);color:#fff}
.btn-danger{border-color:rgba(248,113,113,.4);color:#fca5a5}
input,textarea,select{
  width:100%;background:var(--bg2);border:1px solid var(--line);border-radius:10px;
  padding:10px 12px;font-size:13.5px;outline:none
}
input:focus,textarea:focus{border-color:rgba(16,163,127,.45);box-shadow:0 0 0 2px rgba(16,163,127,.12)}
label{display:block;font-size:11px;font-weight:650;color:var(--muted);margin:10px 0 5px;letter-spacing:.04em;text-transform:uppercase}
.types{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:8px}
.type{
  border:1px solid var(--line);border-radius:12px;padding:10px;background:var(--bg2);cursor:default
}
.type .ic{font-size:16px;margin-bottom:4px}
.type b{display:block;font-size:12.5px;color:var(--fg)}
.type span{font-size:11px;color:var(--muted);line-height:1.35}
.loop{
  border:1px solid var(--line);border-radius:12px;padding:12px;margin-bottom:8px;background:var(--bg2)
}
.loop .head{display:flex;justify-content:space-between;gap:8px;align-items:center}
.loop b{color:var(--fg);font-size:13px}
.steps{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px}
.chip-step{
  font-size:11px;padding:4px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted)
}
.mono{font-family:var(--mono);font-size:11.5px;color:var(--muted);white-space:pre-wrap;max-height:180px;overflow:auto}
.stat{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.stat div{background:var(--bg2);border:1px solid var(--line);border-radius:10px;padding:10px}
.stat span{display:block;font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.stat b{display:block;margin-top:4px;font-size:16px;color:var(--fg)}
.toast{
  position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:var(--panel2);
  border:1px solid var(--line);padding:10px 14px;border-radius:12px;font-size:13px;opacity:0;transition:opacity .2s;z-index:50
}
.toast.show{opacity:1}
</style>
</head>
<body>
<div class="app">
  <header class="top">
    <div class="mark">P</div>
    <div class="brand">Work Studio<small>loops · types · swarm · world model</small></div>
    <nav class="nav">
      <a href="/desk">Desk</a>
      <a href="/phone">Phone</a>
      <a href="/work" class="on">Studio</a>
      <a href="/docs/hub">Docs</a>
    </nav>
    <div class="grow"></div>
    <span class="pill" id="swarmPill">swarm …</span>
  </header>
  <main class="wrap">
    <div class="hero">
      <h1>Design agent labor once. Run it forever.</h1>
      <p>Compose <b style="color:var(--fg)">work types</b> and <b style="color:var(--fg)">work loops</b> with one prompt.
      Cortex talks. Subcortex silently updates the world model. Always-on swarm keeps pulses shipping.</p>
    </div>

    <div class="grid">
      <section class="card">
        <h2>Cortex · Subcortex</h2>
        <div class="sub">System 1 streams dialogue. System 2 works while you read — no log spam.</div>
        <div class="dual">
          <div class="sys cortex">
            <b>Cortex (System 1)</b>
            <p>Conversational prose, coding explanations, product narrative. Beautiful stream for the human.</p>
          </div>
          <div class="sys sub">
            <b>Subcortex (System 2)</b>
            <p>Silent SQLite world-model: archetypes, prose, facts, syntax specs, timeline writes.</p>
          </div>
        </div>
        <label>Try dual-loop</label>
        <textarea id="dualGoal" rows="2" placeholder="Write a tight product story about multi-agent desks, or explain pathlib.Path"></textarea>
        <div class="row">
          <button class="btn btn-primary" type="button" onclick="runDual()">Talk + silent work</button>
          <button class="btn btn-ghost" type="button" onclick="refreshWorld()">World model</button>
        </div>
        <pre class="mono" id="dualOut" style="margin-top:12px"></pre>
      </section>

      <section class="card">
        <h2>Always-on swarm</h2>
        <div class="sub">Continuous multi-agent pulses. Rotates use cases + work loops. Host stays productive.</div>
        <div class="stat" id="swarmStats">
          <div><span>Status</span><b id="sOn">—</b></div>
          <div><span>Pulses</span><b id="sPulses">—</b></div>
          <div><span>Interval</span><b id="sIv">—</b></div>
        </div>
        <div class="row">
          <button class="btn btn-pink" type="button" onclick="swarmStart()">Start swarm</button>
          <button class="btn btn-ghost" type="button" onclick="swarmPulse()">Pulse now</button>
          <button class="btn btn-danger btn-ghost" type="button" onclick="swarmStop()">Stop</button>
        </div>
        <pre class="mono" id="swarmOut" style="margin-top:12px"></pre>
      </section>

      <section class="card">
        <h2>Work types</h2>
        <div class="sub">Atomic labor units. Cortex-facing or Subcortex-silent.</div>
        <div class="types" id="types"></div>
        <label>Create type</label>
        <input id="typeName" placeholder="Name e.g. Security review"/>
        <input id="typeDesc" placeholder="Description" style="margin-top:8px"/>
        <div class="row">
          <select id="typeLayer" style="width:auto;min-width:140px">
            <option value="cortex">Cortex</option>
            <option value="subcortex">Subcortex</option>
          </select>
          <button class="btn btn-primary" type="button" onclick="createType()">Add type</button>
        </div>
      </section>

      <section class="card">
        <h2>Work loops</h2>
        <div class="sub">Ordered chains of types. Generate from plain English.</div>
        <div id="loops"></div>
        <label>Generate from goal</label>
        <textarea id="loopGoal" rows="2" placeholder="e.g. Research plot beats, write a short story, fact-check, ship a static page"></textarea>
        <div class="row">
          <button class="btn btn-primary" type="button" onclick="genLoop()">Generate loop</button>
          <button class="btn btn-ghost" type="button" onclick="refreshStudio()">Refresh</button>
        </div>
        <pre class="mono" id="loopOut" style="margin-top:10px"></pre>
      </section>

      <section class="card" style="grid-column:1/-1">
        <h2>World model datasets</h2>
        <div class="sub">Commercial targets: Narrative Archetype Graph · Literary Prose · Common Sense triples · Syntactic API specs.</div>
        <div class="stat" id="wmStats"></div>
        <label>Search world model</label>
        <div class="row">
          <input id="wmQ" placeholder="Shakespeare Hamlet · pathlib · hero journey" style="flex:1"/>
          <button class="btn btn-primary" type="button" onclick="wmSearch()">Search</button>
        </div>
        <pre class="mono" id="wmOut" style="margin-top:10px"></pre>
      </section>
    </div>
  </main>
</div>
<div class="toast" id="toast"></div>
<script>
const $ = id => document.getElementById(id);
let token = localStorage.getItem('pocket_token') || '';
function toast(t){const el=$('toast');el.textContent=t;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2200)}
function headers(){
  const h={'Content-Type':'application/json'};
  if(token){
    h['Authorization']='Bearer '+token;
    h['X-Pocket-Token']=token; // session tokens accepted here
  }
  return h;
}
async function api(path, opts={}){
  const r = await fetch(path, {...opts, headers:{...headers(), ...(opts.headers||{})}, credentials:'same-origin'});
  const text = await r.text();
  let j={}; try{j=text?JSON.parse(text):{}}catch(_){j={raw:text}}
  if(!r.ok) throw new Error(j.error||j.message||('HTTP '+r.status));
  return j;
}
function esc(s){return String(s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}

async function refreshStudio(){
  try{
    const cat = await api('/v1/work-studio');
    const types = cat.types||[];
    $('types').innerHTML = types.map(t=>`
      <div class="type" style="border-color:${esc(t.color||'#333')}33">
        <div class="ic">${esc(t.icon||'●')}</div>
        <b>${esc(t.name)}</b>
        <span>${esc(t.layer)} · ${esc(t.description||'')}</span>
      </div>`).join('');
    const loops = cat.loops||[];
    $('loops').innerHTML = loops.map(L=>`
      <div class="loop">
        <div class="head">
          <b style="color:${esc(L.color||'#10a37f')}">${esc(L.name)}</b>
          <span class="pill ${L.always_on_eligible?'on':''}">${L.always_on_eligible?'swarm-ready':'manual'}</span>
        </div>
        <div class="sub" style="margin:4px 0 0">${esc(L.description||'')}</div>
        <div class="steps">${(L.steps||[]).map(s=>`<span class="chip-step">${esc(s)}</span>`).join('')}</div>
      </div>`).join('') || '<div class="sub">No loops yet</div>';
  }catch(e){
    $('types').innerHTML = '<div class="sub">Sign in on /desk first, then return — or open studio on localhost as operator.</div>';
  }
  refreshSwarm();
  refreshWorld();
}

async function refreshSwarm(){
  try{
    const s = await api('/v1/swarm');
    $('sOn').textContent = s.running ? 'ON' : 'off';
    $('sPulses').textContent = s.pulses||0;
    $('sIv').textContent = (s.interval_sec||90)+'s';
    $('swarmPill').textContent = s.running ? 'swarm on' : 'swarm off';
    $('swarmPill').className = 'pill '+(s.running?'on':'');
    $('swarmOut').textContent = JSON.stringify(s.last_result||{history:s.history}, null, 2).slice(0,1200);
  }catch(e){
    $('swarmPill').textContent = 'swarm ?';
  }
}

async function refreshWorld(){
  try{
    const w = await api('/v1/world-model');
    const c = w.counts||{};
    $('wmStats').innerHTML = `
      <div><span>Archetypes</span><b>${c.archetypes||0}</b></div>
      <div><span>Prose</span><b>${c.prose_standards||0}</b></div>
      <div><span>Facts</span><b>${c.facts||0}</b></div>
      <div><span>Syntax</span><b>${c.syntax_specs||0}</b></div>
      <div><span>Narrative</span><b>${c.narrative_state||0}</b></div>
      <div><span>Sub logs</span><b>${c.subcortex_log||0}</b></div>`;
  }catch(e){
    $('wmStats').innerHTML = '<div class="sub">World model needs auth</div>';
  }
}

async function runDual(){
  const goal = $('dualGoal').value.trim();
  if(!goal){toast('Enter a goal');return}
  try{
    const j = await api('/v1/dual',{method:'POST',body:JSON.stringify({goal})});
    $('dualOut').textContent = j.text || JSON.stringify(j,null,2);
    toast(j.subcortex_done?'Cortex+Subcortex ready':'Cortex ready · Subcortex finishing');
  }catch(e){toast(e.message);$('dualOut').textContent=e.message}
}

async function swarmStart(){
  try{ const j=await api('/v1/swarm/start',{method:'POST',body:'{}'}); toast('Swarm on'); refreshSwarm(); $('swarmOut').textContent=JSON.stringify(j,null,2).slice(0,1000);}catch(e){toast(e.message)}
}
async function swarmStop(){
  try{ await api('/v1/swarm/stop',{method:'POST',body:'{}'}); toast('Swarm stopped'); refreshSwarm();}catch(e){toast(e.message)}
}
async function swarmPulse(){
  try{ const j=await api('/v1/swarm/pulse',{method:'POST',body:'{}'}); toast('Pulse fired'); refreshSwarm(); $('swarmOut').textContent=JSON.stringify(j,null,2).slice(0,1500);}catch(e){toast(e.message)}
}
async function createType(){
  const name=$('typeName').value.trim(); if(!name){toast('Name required');return}
  try{
    await api('/v1/work-types',{method:'POST',body:JSON.stringify({name, description:$('typeDesc').value, layer:$('typeLayer').value})});
    toast('Type created'); $('typeName').value=''; refreshStudio();
  }catch(e){toast(e.message)}
}
async function genLoop(){
  const goal=$('loopGoal').value.trim(); if(!goal){toast('Describe the loop');return}
  try{
    const j=await api('/v1/work-loops/generate',{method:'POST',body:JSON.stringify({goal})});
    $('loopOut').textContent=JSON.stringify(j.loop||j,null,2);
    toast('Loop generated'); refreshStudio();
  }catch(e){toast(e.message)}
}
async function wmSearch(){
  const q=$('wmQ').value.trim(); if(!q)return;
  try{
    const j=await api('/v1/world-model/search?q='+encodeURIComponent(q));
    $('wmOut').textContent=JSON.stringify(j.results||j,null,2).slice(0,3000);
  }catch(e){toast(e.message)}
}

// local desktop auto auth attempt
(async function boot(){
  try{
    const r=await fetch('/v1/auth/desktop',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
    const j=await r.json();
    if(j.token){ token=j.token; localStorage.setItem('pocket_token', token); }
  }catch(_){}
  refreshStudio();
  setInterval(refreshSwarm, 15000);
})();
</script>
</body>
</html>
"""


def work_studio_html() -> str:
    return STUDIO_HTML
