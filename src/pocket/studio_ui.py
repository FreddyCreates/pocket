"""POCKET Studio — web editing desk for viral exports from SPECULUM recordings."""

STUDIO_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>POCKET Studio</title>
<style>
:root{
  --bg:#09090b;--panel:#121214;--line:rgba(255,255,255,.08);--text:#fafafa;--muted:#a1a1aa;
  --accent:#34d399;--accent2:#10b981;--violet:#a78bfa;--blue:#60a5fa;
  --font:ui-sans-serif,system-ui,"Segoe UI",sans-serif;
  --shadow:0 16px 48px rgba(0,0,0,.45);
}
*{box-sizing:border-box}
body{margin:0;font-family:var(--font);background:radial-gradient(900px 500px at 0% 0%,rgba(52,211,153,.08),transparent 50%),radial-gradient(800px 400px at 100% 0%,rgba(167,139,250,.08),transparent 45%),var(--bg);color:var(--text);min-height:100vh}
.pnav{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 20px;border-bottom:1px solid rgba(255,255,255,.08);background:rgba(0,0,0,.92);position:sticky;top:0;z-index:30;backdrop-filter:blur(14px)}
.pnav .brand{display:flex;align-items:center;gap:10px;font-weight:600;letter-spacing:-.03em;font-size:14px;color:#f5f5f5;text-decoration:none;margin-right:8px}
.pnav .brand i{width:22px;height:22px;border-radius:6px;background:#10a37f;display:grid;place-items:center;font-size:11px;font-weight:800;color:#041;font-style:normal}
.pnav .links{display:flex;gap:2px;flex-wrap:wrap}
.pnav .links a{color:#8e8e8e;text-decoration:none;font-size:13px;font-weight:500;padding:7px 12px;border-radius:8px}
.pnav .links a:hover{color:#ececec;background:#111}
.pnav .links a.on{color:#f5f5f5;background:#161616}
.pnav .sp{flex:1}
.pnav .pill{font-size:11px;color:#8e8e8e;border:1px solid rgba(255,255,255,.08);padding:5px 10px;border-radius:999px}
.pnav .cta{font-size:13px;font-weight:600;color:#041;background:#10a37f;padding:8px 14px;border-radius:8px;text-decoration:none}
.pnav .back{font-size:13px;font-weight:600;color:#e4e4e7;background:transparent;border:1px solid rgba(255,255,255,.12);padding:7px 12px;border-radius:8px;cursor:pointer}
.pnav .back:hover{background:#111}
main{display:grid;grid-template-columns:1fr 360px;gap:20px;padding:20px 24px 40px;max-width:1280px;margin:0 auto}
@media(max-width:960px){main{grid-template-columns:1fr}}
.card{background:linear-gradient(180deg,rgba(255,255,255,.02),transparent),var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:var(--shadow)}
.card h2{margin:0 0 12px;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.rec{display:flex;gap:12px;padding:12px;border-radius:12px;border:1px solid transparent;cursor:pointer;margin-bottom:8px;align-items:center}
.rec:hover,.rec.on{border-color:var(--line);background:rgba(255,255,255,.03)}
.rec b{display:block;font-size:13px}
.rec span{font-size:11px;color:var(--muted)}
.presets{display:grid;gap:8px}
.preset{border:1px solid var(--line);border-radius:12px;padding:12px;cursor:pointer;background:transparent;text-align:left;color:inherit;width:100%}
.preset:hover,.preset.on{border-color:var(--accent);background:rgba(52,211,153,.06)}
.preset b{display:block;font-size:13px}
.preset small{color:var(--muted);font-size:11px;line-height:1.4}
label{display:block;font-size:11px;color:var(--muted);margin:10px 0 4px;font-weight:650}
input,textarea{width:100%;padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:#0c0c0e;color:var(--text);font:inherit}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;border:0;border-radius:10px;padding:12px 16px;font-weight:750;cursor:pointer;font-size:13px}
.btn.primary{background:linear-gradient(180deg,#34d399,#10b981);color:#052e16;width:100%;margin-top:14px;box-shadow:0 4px 20px rgba(16,185,129,.3)}
.btn.ghost{background:transparent;border:1px solid var(--line);color:var(--text);width:100%;margin-top:8px}
.btn:disabled{opacity:.45;cursor:not-allowed}
#log{font-family:ui-monospace,Consolas,monospace;font-size:11px;white-space:pre-wrap;max-height:220px;overflow:auto;background:#050506;border-radius:10px;padding:12px;color:#86efac;border:1px solid var(--line)}
.exports a{color:var(--accent);text-decoration:none;font-size:12px}
.exports li{margin:6px 0}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#18181b;border:1px solid var(--line);padding:10px 16px;border-radius:10px;display:none;z-index:99}
.toast.show{display:block}
.badge{font-size:10px;font-weight:700;padding:3px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.badge.on{color:#86efac;border-color:#14532d;background:#052e16}
/* boot splash (shared production feel) */
.boot-splash{position:fixed;inset:0;z-index:200;display:flex;flex-direction:column;align-items:center;justify-content:center;background:#050508;transition:opacity .4s ease,visibility .4s}
.boot-splash.done{opacity:0;visibility:hidden;pointer-events:none}
.boot-splash .m{width:48px;height:48px;border-radius:12px;background:linear-gradient(145deg,#10a37f,#0a7a5f);color:#041;display:grid;place-items:center;font-weight:800;font-size:20px;box-shadow:0 0 0 1px rgba(16,163,127,.4),0 12px 36px rgba(16,163,127,.22)}
.boot-splash .t{margin-top:14px;font-weight:650;letter-spacing:-.03em}
.boot-splash .s{margin-top:4px;font-size:12px;color:#71717a}
</style>
</head>
<body>
<div class="boot-splash" id="bootSplash"><div class="m">P</div><div class="t">POCKET Studio</div><div class="s">Same session as Desktop</div></div>
<header class="pnav">
  <button type="button" class="back" onclick="goBack()">← Back</button>
  <a class="brand" href="/desk"><i>P</i>POCKET</a>
  <nav class="links" aria-label="Product">
    <a href="/tour">Overview</a>
    <a href="/desk">Desktop</a>
    <a href="/developers">API</a>
    <a class="on" href="/studio">Studio</a>
  </nav>
  <div class="sp"></div>
  <span class="badge" id="ffBadge">ffmpeg …</span>
  <span class="pill" id="authPill">auth…</span>
  <a class="cta" href="/desk">Open Desktop</a>
</header>
<main>
  <section>
    <div class="card">
      <h2>Recordings</h2>
      <div id="recs"><div style="color:var(--muted);font-size:13px">Loading…</div></div>
      <button class="btn ghost" type="button" onclick="loadAll()">Refresh</button>
    </div>
    <div class="card" style="margin-top:16px">
      <h2>Exports</h2>
      <ul class="exports" id="exports"></ul>
    </div>
  </section>
  <aside>
    <div class="card">
      <h2>Preset</h2>
      <div class="presets" id="presets"></div>
      <label>Title</label>
      <input id="title" value="POCKET"/>
      <label>Subtitle / caption</label>
      <input id="subtitle" value="Real host co-pilot demo"/>
      <label>CTA</label>
      <input id="cta" value="ItsNotAI Labs"/>
      <label>Brand</label>
      <input id="brand" value="ItsNotAI Labs"/>
      <button class="btn primary" id="btnRender" type="button" onclick="doRender()">Render selected</button>
      <button class="btn ghost" type="button" onclick="doBatch()">Viral pack (phone + web + story + clean)</button>
      <button class="btn ghost" type="button" onclick="doLatest()">Polish latest recording</button>
    </div>
    <div class="card" style="margin-top:16px">
      <h2>Job log</h2>
      <div id="log">Ready.</div>
    </div>
  </aside>
</main>
<div class="toast" id="toast"></div>
<script>
const auth = {
  user: sessionStorage.getItem('pocket_user') || localStorage.getItem('pocket_user') || '',
  pass: sessionStorage.getItem('pocket_pass') || localStorage.getItem('pocket_pass') || '',
  token: sessionStorage.getItem('pocket_token') || localStorage.getItem('pocket_token') || '',
};
let recordings = [], selected = null, preset = 'viral_phone';
const bootAt = Date.now();

function storeAuth(user, token) {
  auth.user = user || auth.user || 'pocket';
  auth.token = token || '';
  sessionStorage.setItem('pocket_user', auth.user);
  sessionStorage.setItem('pocket_token', auth.token);
  localStorage.setItem('pocket_user', auth.user);
  localStorage.setItem('pocket_token', auth.token);
  const pill = document.getElementById('authPill');
  if (pill) pill.textContent = auth.user || 'signed in';
}
function headers() {
  const h = {'Content-Type':'application/json'};
  if (auth.token) h['Authorization'] = 'Bearer ' + auth.token;
  else if (auth.user && auth.pass) h['Authorization'] = 'Basic ' + btoa(auth.user + ':' + auth.pass);
  if (auth.pass) h['X-Pocket-Access'] = auth.pass;
  return h;
}
async function api(path, opt={}) {
  const r = await fetch(path, {...opt, headers:{...headers(), ...(opt.headers||{})}});
  if (r.status === 401) {
    // One-shot desktop re-auth (same host as desk) then retry
    const ok = await ensureDesktopAuth(true);
    if (ok) {
      const r2 = await fetch(path, {...opt, headers:{...headers(), ...(opt.headers||{})}});
      if (r2.status === 401) { toast('Still unauthorized — open Desktop once'); throw new Error('auth'); }
      const j2 = await r2.json();
      if (!r2.ok) throw new Error(j2.error || r2.statusText);
      return j2;
    }
    toast('Sign in on Desktop first (same browser profile)');
    throw new Error('auth');
  }
  const j = await r.json();
  if (!r.ok) throw new Error(j.error || r.statusText);
  return j;
}
function toast(m){ const t=document.getElementById('toast'); t.textContent=m; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'), 2800); }
function log(m){ const el=document.getElementById('log'); el.textContent = (typeof m==='string'?m:JSON.stringify(m,null,2)).slice(0,8000); }
function goBack(){
  try{
    if (history.length > 1 && document.referrer && document.referrer.indexOf(location.origin) === 0) {
      history.back(); return;
    }
  }catch(_){}
  location.href = '/desk';
}
function dismissSplash(){
  const el = document.getElementById('bootSplash');
  if (!el) return;
  const wait = Math.max(0, 700 - (Date.now() - bootAt));
  setTimeout(()=>{ el.classList.add('done'); }, wait);
}
async function ensureDesktopAuth(force){
  // Mirror desk tokens; on localhost auto-mint the same operator session as Desktop
  if (!force) {
    if (!sessionStorage.getItem('pocket_token') && localStorage.getItem('pocket_token')) {
      sessionStorage.setItem('pocket_token', localStorage.getItem('pocket_token'));
      sessionStorage.setItem('pocket_user', localStorage.getItem('pocket_user') || 'pocket');
      auth.token = sessionStorage.getItem('pocket_token');
      auth.user = sessionStorage.getItem('pocket_user') || 'pocket';
    }
    if (auth.token) {
      try {
        const r = await fetch('/v1/auth/me', {method:'POST', headers: headers(), body:'{}'});
        if (r.ok) {
          const j = await r.json();
          if (j && j.user) storeAuth((j.user.user || j.user.display || auth.user), auth.token);
          return true;
        }
      } catch(_){}
    }
  }
  const host = location.hostname;
  if (host !== '127.0.0.1' && host !== 'localhost') return !!auth.token;
  try {
    const r = await fetch('/v1/auth/desktop', {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'});
    if (!r.ok) return false;
    const j = await r.json();
    if (!j.ok || !j.token) return false;
    storeAuth((j.user && j.user.user) || 'pocket', j.token);
    return true;
  } catch(_) { return false; }
}

async function loadAll(){
  try{
    const st = await api('/v1/studio');
    document.getElementById('ffBadge').textContent = st.ffmpeg ? 'ffmpeg ready' : 'ffmpeg missing';
    document.getElementById('ffBadge').className = 'badge ' + (st.ffmpeg?'on':'');
    recordings = st.recordings_list || (await api('/v1/studio/recordings')).recordings || [];
    const exports = st.exports_list || (await api('/v1/studio/exports')).exports || [];
    renderRecs();
    renderExports(exports);
    const presets = st.presets || (await api('/v1/studio/presets')).presets || [];
    renderPresets(presets);
  }catch(e){ log('Load failed: '+e.message); }
}
function renderRecs(){
  const box = document.getElementById('recs');
  if (!recordings.length){ box.innerHTML='<div style="color:var(--muted);font-size:13px">No recordings yet. Run a demo with record on the desk.</div>'; return; }
  box.innerHTML = recordings.map((r,i)=>`
    <div class="rec ${selected===r.path?'on':''}" onclick="selectRec(${i})">
      <div style="width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,#34d39933,#60a5fa33);display:grid;place-items:center;font-size:11px;font-weight:800;color:var(--accent)">MP4</div>
      <div style="min-width:0;flex:1"><b>${r.name}</b><span>${r.size_mb} MB</span></div>
    </div>`).join('');
}
function selectRec(i){ selected = recordings[i].path; renderRecs(); log('Selected '+recordings[i].name); }
function renderPresets(list){
  const box = document.getElementById('presets');
  const arr = list.length ? list : [
    {id:'viral_phone',label:'Viral iPhone / Reels',desc:'9:16 phone bezel'},
    {id:'viral_web',label:'Viral Web Ad',desc:'16:9 browser chrome'},
    {id:'clean_demo',label:'Clean Demo',desc:'16:9 product'},
    {id:'story_stack',label:'Story Stack',desc:'9:16 beats'},
  ];
  box.innerHTML = arr.map(p=>`
    <button type="button" class="preset ${preset===p.id?'on':''}" onclick="preset='${p.id}'; renderPresets(${JSON.stringify(arr).replace(/"/g,'&quot;')})">
      <b>${p.label||p.id}</b><small>${p.desc||p.aspect||''}</small>
    </button>`).join('');
}
function renderExports(list){
  const ul = document.getElementById('exports');
  if (!list.length){ ul.innerHTML='<li style="color:var(--muted);font-size:12px">No exports yet</li>'; return; }
  ul.innerHTML = list.map(e=>`<li><a href="/v1/studio/file?name=${encodeURIComponent(e.name)}" target="_blank">${e.name}</a> <span style="color:var(--muted);font-size:11px">${e.size_mb} MB</span></li>`).join('');
}
function meta(){
  return {
    title: document.getElementById('title').value,
    subtitle: document.getElementById('subtitle').value,
    caption: document.getElementById('subtitle').value,
    cta: document.getElementById('cta').value,
    brand: document.getElementById('brand').value,
  };
}
async function doRender(){
  if (!selected){ toast('Select a recording'); return; }
  const btn=document.getElementById('btnRender'); btn.disabled=true;
  try{
    log('Rendering '+preset+'…');
    const j = await api('/v1/studio/render',{method:'POST',body:JSON.stringify({source:selected,preset,...meta()})});
    log(j); toast(j.message||'done'); loadAll();
  }catch(e){ log(String(e)); toast(e.message); }
  btn.disabled=false;
}
async function doBatch(){
  if (!selected){ toast('Select a recording'); return; }
  try{
    log('Viral pack rendering…');
    const j = await api('/v1/studio/batch',{method:'POST',body:JSON.stringify({source:selected,...meta()})});
    log(j); toast(j.message||'batch done'); loadAll();
  }catch(e){ toast(e.message); log(String(e)); }
}
async function doLatest(){
  try{
    log('Polishing latest recording…');
    const j = await api('/v1/studio/auto',{method:'POST',body:JSON.stringify(meta())});
    log(j); toast(j.message||'auto pack done'); loadAll();
  }catch(e){ toast(e.message); log(String(e)); }
}
(async function bootStudio(){
  // Sync storage from desk (same origin / Edge app profile)
  if (!auth.token && localStorage.getItem('pocket_token')) {
    storeAuth(localStorage.getItem('pocket_user')||'pocket', localStorage.getItem('pocket_token'));
  }
  await ensureDesktopAuth(false);
  const pill = document.getElementById('authPill');
  if (pill) pill.textContent = auth.token ? (auth.user || 'signed in') : 'need desk login';
  await loadAll();
  dismissSplash();
})();
</script>
</body>
</html>
"""
