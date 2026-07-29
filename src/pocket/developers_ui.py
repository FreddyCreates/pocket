"""POCKET API — customer-facing developers page (OpenAI-style simplicity)."""

from pocket.product_shell import SHELL_CSS, shell_nav


def developers_html() -> str:
    return DEVELOPERS_HTML.replace("__SHELL_CSS__", SHELL_CSS).replace(
        "__SHELL_NAV__", shell_nav(active="api")
    )


DEVELOPERS_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>POCKET API</title>
<meta name="description" content="POCKET API — host co-pilot for Grok, Codex, Claude. Keys, fusion, agents."/>
<style>
:root{
  --bg:#000;--panel:#111;--line:rgba(255,255,255,.08);--text:#ececec;--muted:#8e8e8e;
  --accent:#10a37f;--accent2:#1a7f64;--danger:#ef4444;--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
  --sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;
}
*{box-sizing:border-box}body{margin:0;font-family:var(--sans);background:var(--bg);color:var(--text);line-height:1.5}
a{color:var(--accent);text-decoration:none}a:hover{text-decoration:underline}
__SHELL_CSS__
.wrap{max-width:880px;margin:0 auto;padding:48px 24px 96px}
h1{font-size:40px;letter-spacing:-.04em;font-weight:600;margin:0 0 12px;line-height:1.1}
.sub{font-size:17px;color:var(--muted);max-width:560px;margin:0 0 32px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:24px 0 40px}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
.card{border:1px solid var(--line);border-radius:12px;padding:18px;background:var(--panel)}
.card h3{margin:0 0 6px;font-size:14px;font-weight:600}
.card p{margin:0;font-size:13px;color:var(--muted)}
.card code{display:block;margin-top:10px;font-size:11px;font-family:var(--mono);color:#c4c4c4;background:#0a0a0a;padding:10px;border-radius:8px;overflow:auto}
h2{font-size:20px;letter-spacing:-.02em;font-weight:600;margin:40px 0 12px}
.step{display:flex;gap:14px;margin:0 0 18px}
.n{width:28px;height:28px;border-radius:50%;background:var(--panel);border:1px solid var(--line);display:grid;place-items:center;font-size:12px;font-weight:700;flex:0 0 auto;color:var(--muted)}
.step h4{margin:2px 0 4px;font-size:14px;font-weight:600}
.step p{margin:0;font-size:13px;color:var(--muted)}
pre{background:#0a0a0a;border:1px solid var(--line);border-radius:10px;padding:14px 16px;font-size:12px;font-family:var(--mono);overflow:auto;color:#d4d4d4;line-height:1.55}
.btnrow{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}
button.btn,a.btn{font:inherit;font-size:13px;font-weight:600;border-radius:8px;padding:9px 14px;border:1px solid var(--line);background:var(--panel);color:var(--text);cursor:pointer;text-decoration:none}
button.btn.p,a.btn.p{background:var(--accent);color:#041;border:0}
button.btn:hover{border-color:rgba(255,255,255,.16)}
button.btn.p:hover{background:var(--accent2)}
#keyBox{display:none;margin:12px 0;padding:14px;border:1px solid #14532d;background:#052e16;border-radius:10px}
#keyBox code{font-family:var(--mono);font-size:12px;word-break:break-all;color:#86efac}
#keyList{margin-top:12px;font-size:13px;color:var(--muted)}
#keyList .row{display:flex;justify-content:space-between;gap:8px;padding:10px 0;border-bottom:1px solid var(--line)}
.toast{position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#222;border:1px solid var(--line);padding:10px 16px;border-radius:8px;font-size:13px;display:none;z-index:50}
.gate{position:fixed;inset:0;background:rgba(0,0,0,.75);display:none;align-items:center;justify-content:center;z-index:40}
.gate .box{width:min(380px,92vw);background:#111;border:1px solid var(--line);border-radius:14px;padding:22px}
.gate label{display:block;font-size:12px;color:var(--muted);margin:10px 0 4px}
.gate input{width:100%;background:#0a0a0a;border:1px solid var(--line);border-radius:8px;padding:10px;color:var(--text);font:inherit}
.foot{margin-top:64px;padding-top:20px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
</style>
</head>
<body>
__SHELL_NAV__
<div style="display:flex;gap:8px;justify-content:flex-end;padding:10px 20px;border-bottom:1px solid rgba(255,255,255,.06)">
  <button class="btn" type="button" id="authBtn" onclick="openGate()" style="font:inherit;font-size:13px;border:1px solid rgba(255,255,255,.08);background:#111;color:#8e8e8e;padding:7px 12px;border-radius:8px;cursor:pointer">Sign in</button>
  <button class="btn p" type="button" onclick="createKey()" style="font:inherit;font-size:13px;font-weight:600;border:0;background:#10a37f;color:#041;padding:8px 14px;border-radius:8px;cursor:pointer">Create API key</button>
</div>

<main class="wrap">
  <h1>API — same product as Desktop</h1>
  <p class="sub">Keys for Grok, Codex, Claude, and apps. Engines run on the host you operate in <a href="/">Desktop</a>. Overview: <a href="/tour">product home</a>.</p>
  <p style="font-size:13px;color:var(--muted);margin:-12px 0 24px">Sign-in for keys: username/password from <code style="color:var(--accent)">%USERPROFILE%\.pocket\ACCESS.txt</code> (usually user <strong style="color:var(--text)">pocket</strong>).</p>

  <div class="grid">
    <div class="card">
      <h3>Chat</h3>
      <p>OpenAI-shaped messages → host agents.</p>
      <code>POST /v1/ai/chat</code>
    </div>
    <div class="card">
      <h3>Agents</h3>
      <p>Researcher, coder, security, squad…</p>
      <code>POST /v1/ai/agents/{id}/run</code>
    </div>
    <div class="card">
      <h3>Fusion</h3>
      <p>Live screen symbols + remake.</p>
      <code>GET /v1/vision/page</code>
    </div>
    <div class="card">
      <h3>Orchestrate</h3>
      <p>NL plan → real host skills.</p>
      <code>POST /v1/orchestrator/chat</code>
    </div>
  </div>

  <h2>Get started</h2>
  <div class="step"><div class="n">1</div><div><h4>Sign in as operator</h4><p>Use your POCKET host password (ACCESS.txt). Keys are created by the operator seat.</p></div></div>
  <div class="step"><div class="n">2</div><div><h4>Create a secret key</h4><p>Shown once. Prefix <code style="color:var(--accent)">sk_pocket_</code></p></div></div>
  <div class="step"><div class="n">3</div><div><h4>Call the API</h4><p>Bearer auth. Base URL is this host (or your public tunnel).</p></div></div>

  <div class="btnrow">
    <button class="btn p" type="button" onclick="createKey()">Create API key</button>
    <button class="btn" type="button" onclick="listKeys()">List keys</button>
    <button class="btn" type="button" onclick="copyBase()">Copy base URL</button>
    <a class="btn" href="/v1/ai">Open catalog JSON</a>
  </div>
  <div id="keyBox"><div style="font-size:12px;color:#86efac;margin-bottom:6px">Copy now — will not be shown again</div><code id="keySecret"></code></div>
  <div id="keyList"></div>

  <h2>Grok / Codex / curl</h2>
<pre id="snippet">BASE=http://127.0.0.1:8787
KEY=sk_pocket_YOUR_KEY

# Health (no auth)
curl -s $BASE/health

# Chat
curl -s $BASE/v1/ai/chat \
  -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"agent":"planner","messages":[{"role":"user","content":"Plan a host demo"}]}'

# Fusion page (operator or key)
curl -s $BASE/v1/vision/page \
  -H "Authorization: Bearer $KEY"

# Full catalog
curl -s $BASE/v1/api -H "Authorization: Bearer $KEY"
</pre>

  <h2>For Grok Build</h2>
  <p style="color:var(--muted);font-size:14px">Point tools at <strong style="color:var(--text)">$BASE</strong> with header <code style="color:var(--accent)">Authorization: Bearer sk_pocket_…</code>. Use <code style="color:var(--text)">/v1/api</code> as the capability map, then <code style="color:var(--text)">/v1/ai/*</code>, <code style="color:var(--text)">/v1/vision/page</code>, <code style="color:var(--text)">/v1/rfe/synthesize</code>, <code style="color:var(--text)">/v1/orchestrator/chat</code>.</p>

  <h2>For Codex CLI</h2>
  <p style="color:var(--muted);font-size:14px">Prefer host skills via Desktop when coding on this PC. For remote automation, same Bearer key + <code style="color:var(--text)">POST /v1/ai/agents/coder/run</code> with <code style="color:var(--text)">{"task":"…","sync":true}</code>.</p>

  <div class="foot">POCKET API · ItsNotAI Labs · Keys are host-local until you expose the tunnel. Desktop remains the operator UI.</div>
</main>
<div class="toast" id="toast"></div>
<div class="gate" id="gate">
  <div class="box">
    <h3 style="margin:0 0 8px;font-size:16px">Operator sign-in</h3>
    <p style="margin:0;font-size:13px;color:var(--muted)">Required to create keys</p>
    <p style="font-size:12px;color:var(--muted);margin:0 0 8px">Same credentials as Desktop: <code style="color:var(--accent)">%USERPROFILE%\.pocket\ACCESS.txt</code></p>
    <label>Username</label>
    <input id="u" value="pocket" autocomplete="username"/>
    <label>Password (ACCESS.txt)</label>
    <input id="p" type="password" autocomplete="current-password" placeholder="from ACCESS.txt"/>
    <div class="btnrow" style="margin-top:14px">
      <button class="btn p" type="button" onclick="doLogin()">Continue</button>
      <button class="btn" type="button" onclick="closeGate()">Cancel</button>
    </div>
  </div>
</div>
<script>
const BASE=location.origin;
let AUTH=localStorage.getItem('pocket_auth')||'';
function toast(m){const t=document.getElementById('toast');t.textContent=m;t.style.display='block';setTimeout(()=>t.style.display='none',2800)}
function openGate(){document.getElementById('gate').style.display='flex'}
function closeGate(){document.getElementById('gate').style.display='none'}
async function doLogin(){
  const user=document.getElementById('u').value.trim();
  const pass=document.getElementById('p').value;
  const r=await fetch(BASE+'/v1/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:user,password:pass})});
  const j=await r.json().catch(()=>({}));
  if(!r.ok){toast(j.error||'Login failed');return}
  // Prefer Basic for subsequent API
  AUTH='Basic '+btoa(user+':'+pass);
  localStorage.setItem('pocket_auth',AUTH);
  if(j.token) localStorage.setItem('pocket_token',j.token);
  document.getElementById('authBtn').textContent='Signed in';
  closeGate();toast('Signed in');listKeys();
}
function headers(json){
  const h={}; if(json) h['Content-Type']='application/json';
  if(AUTH) h['Authorization']=AUTH;
  const t=localStorage.getItem('pocket_token'); if(t&&!AUTH) h['Authorization']='Bearer '+t;
  return h;
}
async function createKey(){
  if(!AUTH&&!localStorage.getItem('pocket_token')){openGate();toast('Sign in first');return}
  const r=await fetch(BASE+'/v1/ai/keys',{method:'POST',headers:headers(true),body:JSON.stringify({name:'api-'+Date.now(),tier:'pro'})});
  const j=await r.json().catch(()=>({}));
  if(!r.ok){ if(r.status===401){openGate();toast('Sign in required');return} toast(j.error||'Failed');return}
  document.getElementById('keyBox').style.display='block';
  document.getElementById('keySecret').textContent=j.key||j.secret||JSON.stringify(j);
  toast('Key created — copy it now');
  listKeys();
}
async function listKeys(){
  if(!AUTH&&!localStorage.getItem('pocket_token'))return;
  const r=await fetch(BASE+'/v1/ai/keys',{headers:headers()});
  const j=await r.json().catch(()=>({}));
  const el=document.getElementById('keyList');
  const keys=j.keys||j||[];
  if(!Array.isArray(keys)||!keys.length){el.innerHTML='<div class="row"><span>No keys yet</span></div>';return}
  el.innerHTML=keys.map(k=>`<div class="row"><span>${k.name||k.id} · ${k.prefix||''} · ${k.tier||''}</span><span>${k.revoked?'revoked':'active'}</span></div>`).join('');
}
function copyBase(){navigator.clipboard.writeText(BASE);toast('Base URL copied')}
if(AUTH||localStorage.getItem('pocket_token')){document.getElementById('authBtn').textContent='Signed in';listKeys()}
// fix base in snippet for this host
document.getElementById('snippet').textContent=document.getElementById('snippet').textContent.replace('http://127.0.0.1:8787',BASE);
</script>
</body>
</html>
"""
