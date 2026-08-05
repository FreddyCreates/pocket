"""POCKET Phone — simplified mobile web app for agentic day ops.

Coding · planning · real-world tasks on the go. Uses same auth + sessions API.
Does not expose founder personal disk to market seats.
"""

PHONE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,maximum-scale=1"/>
<meta name="theme-color" content="#050508"/>
<meta name="apple-mobile-web-app-capable" content="yes"/>
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"/>
<meta name="mobile-web-app-capable" content="yes"/>
<meta name="description" content="POCKET Phone — code, plan, real-world tasks on the go"/>
<link rel="manifest" href="/phone/manifest.webmanifest"/>
<title>POCKET · Phone</title>
<style>
:root{
  --bg:#050508;--panel:#121216;--panel2:#1a1a20;--line:rgba(255,255,255,.08);
  --text:#e8e8ed;--muted:#8b8b98;--fg:#fafafa;--accent:#10a37f;--accent2:#34d399;
  --violet:#a78bfa;--blue:#60a5fa;--amber:#fbbf24;--red:#f87171;
  --safe-b:env(safe-area-inset-bottom,0px);--safe-t:env(safe-area-inset-top,0px);
  --font:ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%;margin:0}
body{
  font-family:var(--font);background:var(--bg);color:var(--text);
  overflow:hidden;-webkit-font-smoothing:antialiased;color-scheme:dark;
  padding:var(--safe-t) 0 0;
}
button,input,textarea{font:inherit;color:inherit}
button{cursor:pointer;border:0;background:none}
button:disabled{opacity:.4}
.app{display:flex;flex-direction:column;height:100dvh;height:100vh;max-width:520px;margin:0 auto;position:relative}
.top{
  flex:0 0 auto;display:flex;align-items:center;gap:10px;padding:10px 14px 8px;
  border-bottom:1px solid var(--line);background:rgba(5,5,8,.92);backdrop-filter:blur(16px);z-index:5
}
.brand{display:flex;align-items:center;gap:8px;font-weight:700;letter-spacing:-.03em;color:var(--fg);font-size:15px}
.mark{
  width:28px;height:28px;border-radius:9px;display:grid;place-items:center;font-size:13px;font-weight:800;color:#041;
  background:linear-gradient(145deg,var(--accent),#0a7a5f);box-shadow:0 0 0 1px rgba(16,163,127,.35),0 6px 20px rgba(16,163,127,.2)
}
.chip{font-size:10px;font-weight:600;padding:3px 8px;border-radius:999px;border:1px solid var(--line);color:var(--muted)}
.chip.on{color:#6ee7b7;border-color:rgba(16,163,127,.4);background:rgba(16,163,127,.1)}
.grow{flex:1}
.icon-btn{width:40px;height:40px;border-radius:12px;border:1px solid var(--line);background:var(--panel);color:var(--text);font-size:16px}
.modes{
  flex:0 0 auto;display:flex;gap:8px;padding:10px 12px 6px;overflow-x:auto;scrollbar-width:none;
  -webkit-overflow-scrolling:touch
}
.modes::-webkit-scrollbar{display:none}
.modes button{
  flex:0 0 auto;padding:10px 14px;border-radius:999px;border:1px solid var(--line);
  background:var(--panel);color:var(--muted);font-size:12.5px;font-weight:600;white-space:nowrap
}
.modes button.on{color:#041;background:var(--accent);border-color:transparent}
.modes button.novae{border-color:rgba(167,139,250,.35);color:#c4b5fd}
.modes button.novae.on{background:linear-gradient(135deg,#7c3aed,#10a37f);color:#fff}
.chat{
  flex:1;min-height:0;overflow:auto;padding:12px 14px 16px;
  display:flex;flex-direction:column;gap:10px;-webkit-overflow-scrolling:touch
}
.empty{
  margin:auto;text-align:center;padding:24px 16px;color:var(--muted);max-width:320px
}
.empty h2{margin:0 0 8px;color:var(--fg);font-size:20px;font-weight:650;letter-spacing:-.03em}
.empty p{margin:0;font-size:13.5px;line-height:1.5}
.quick{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:16px}
.quick button{
  border:1px solid var(--line);background:var(--panel);color:var(--text);
  border-radius:999px;padding:8px 12px;font-size:12px;font-weight:550
}
.bubble{max-width:92%;animation:rise .28s ease both}
@keyframes rise{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
.bubble.user{align-self:flex-end}
.bubble.agent{align-self:flex-start}
.bubble .body{
  padding:12px 14px;border-radius:16px;font-size:15px;line-height:1.5;white-space:pre-wrap;word-break:break-word
}
.bubble.user .body{background:var(--panel2);border:1px solid var(--line);color:var(--fg);border-bottom-right-radius:6px}
.bubble.agent .body{background:transparent;padding:4px 2px;color:var(--text)}
.bubble.agent .meta{font-size:11px;color:var(--muted);margin-bottom:4px;display:flex;align-items:center;gap:6px}
.bubble.agent .body pre,.bubble.agent .body code{font-family:var(--mono);font-size:12.5px}
.bubble.agent .body pre{
  background:#0a0a0c;border:1px solid var(--line);border-radius:10px;padding:10px;overflow:auto;max-height:240px;color:#b7f0c6
}
/* Thinking animation */
.think{
  align-self:flex-start;display:flex;align-items:center;gap:10px;padding:8px 4px;
  color:var(--muted);font-size:12.5px;font-weight:500
}
.think-orb{
  width:28px;height:28px;border-radius:50%;position:relative;
  background:radial-gradient(circle at 35% 35%,#6ee7b7,var(--accent) 45%,#0a7a5f 80%);
  box-shadow:0 0 0 0 rgba(16,163,127,.45);animation:pulse 1.4s ease-in-out infinite
}
.think-orb::after{
  content:"";position:absolute;inset:-4px;border-radius:50%;
  border:2px solid transparent;border-top-color:var(--violet);border-right-color:var(--accent2);
  animation:spin 1s linear infinite
}
.think-dots span{
  display:inline-block;width:5px;height:5px;margin:0 2px;border-radius:50%;background:var(--accent2);
  animation:dot 1.2s ease-in-out infinite
}
.think-dots span:nth-child(2){animation-delay:.15s}
.think-dots span:nth-child(3){animation-delay:.3s}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 rgba(16,163,127,.4);transform:scale(1)}50%{box-shadow:0 0 0 10px rgba(16,163,127,0);transform:scale(1.05)}}
@keyframes spin{to{transform:rotate(360deg)}}
@keyframes dot{0%,80%,100%{opacity:.25;transform:translateY(0)}40%{opacity:1;transform:translateY(-3px)}}
.composer{
  flex:0 0 auto;padding:8px 12px calc(10px + var(--safe-b));
  border-top:1px solid var(--line);background:rgba(5,5,8,.95);backdrop-filter:blur(14px)
}
.composer .row{display:flex;gap:8px;align-items:flex-end}
.composer textarea{
  flex:1;min-height:44px;max-height:120px;resize:none;border-radius:14px;border:1px solid var(--line);
  background:var(--panel);padding:12px 14px;font-size:16px;line-height:1.4;outline:none
}
.composer textarea:focus{border-color:rgba(16,163,127,.45);box-shadow:0 0 0 2px rgba(16,163,127,.15)}
.send{
  width:48px;height:48px;border-radius:14px;background:var(--accent);color:#041;font-weight:800;font-size:16px
}
.send:active{transform:scale(.96)}
.nav{
  flex:0 0 auto;display:grid;grid-template-columns:repeat(4,1fr);gap:2px;
  padding:6px 8px calc(8px + var(--safe-b));border-top:1px solid var(--line);background:#0a0a0e
}
.nav button{padding:8px 4px;border-radius:12px;color:var(--muted);font-size:10px;font-weight:600}
.nav button span{display:block;font-size:18px;margin-bottom:2px}
.nav button.on{color:var(--accent2);background:rgba(16,163,127,.08)}
/* gate */
.gate{
  position:fixed;inset:0;z-index:50;display:flex;align-items:flex-end;justify-content:center;
  background:rgba(0,0,0,.72);backdrop-filter:blur(8px);padding:16px
}
.gate.hidden{display:none}
.gate .card{
  width:100%;max-width:400px;background:var(--panel);border:1px solid var(--line);
  border-radius:20px 20px 16px 16px;padding:22px 18px calc(18px + var(--safe-b))
}
.gate h2{margin:0 0 6px;font-size:20px;color:var(--fg);letter-spacing:-.03em}
.gate p{margin:0 0 14px;font-size:13px;color:var(--muted);line-height:1.45}
.gate label{display:block;font-size:11px;font-weight:600;color:var(--muted);margin:10px 0 4px;text-transform:uppercase;letter-spacing:.04em}
.gate input{
  width:100%;padding:12px 14px;border-radius:12px;border:1px solid var(--line);background:#0a0a0c;font-size:16px
}
.gate .primary{
  width:100%;margin-top:16px;padding:14px;border-radius:12px;background:var(--accent);color:#041;font-weight:700;font-size:15px
}
.gate .err{color:var(--red);font-size:12.5px;margin-top:10px;min-height:1.2em}
.sheet{
  position:fixed;inset:0;z-index:40;display:none;align-items:flex-end;background:rgba(0,0,0,.55)
}
.sheet.open{display:flex}
.sheet .panel{
  width:100%;max-width:520px;margin:0 auto;background:var(--panel);border-radius:18px 18px 0 0;
  padding:14px 14px calc(16px + var(--safe-b));max-height:70dvh;overflow:auto;border:1px solid var(--line)
}
.sheet h3{margin:0 0 10px;font-size:14px;color:var(--fg)}
.novae-card{
  border:1px solid var(--line);border-radius:14px;padding:12px;margin-bottom:8px;background:#0c0c10
}
.novae-card b{display:block;color:var(--fg);font-size:14px}
.novae-card small{color:var(--muted);font-size:12px;line-height:1.4}
.novae-card .row{display:flex;gap:8px;margin-top:10px}
.novae-card .row button{
  flex:1;padding:10px;border-radius:10px;border:1px solid var(--line);font-weight:600;font-size:12.5px
}
.novae-card .row button.go{background:var(--accent);color:#041;border:0}
.toast{
  position:fixed;left:50%;bottom:calc(90px + var(--safe-b));transform:translateX(-50%);
  background:var(--panel2);border:1px solid var(--line);color:var(--fg);padding:10px 14px;border-radius:12px;
  font-size:13px;z-index:60;opacity:0;pointer-events:none;transition:opacity .2s;max-width:90%
}
.toast.show{opacity:1}
@media (prefers-reduced-motion:reduce){
  *,*::before,*::after{animation:none!important;transition:none!important}
}
</style>
</head>
<body>
<div class="app">
  <header class="top">
    <div class="brand"><div class="mark">P</div>POCKET</div>
    <span class="chip" id="modeChip">Phone</span>
    <div class="grow"></div>
    <span class="chip" id="userChip">…</span>
    <button class="icon-btn" type="button" onclick="openSheet()" title="More">☰</button>
  </header>

  <div class="modes" id="modes" role="tablist">
    <button type="button" class="on" data-mode="plan" onclick="pickMode(this)">Plan</button>
    <button type="button" data-mode="codex" onclick="pickMode(this)">Code</button>
    <button type="button" data-mode="grok" onclick="pickMode(this)">Grok</button>
    <button type="button" class="novae" data-mode="novae_grok" onclick="pickMode(this)">Grok Novae</button>
    <button type="button" class="novae" data-mode="novae_codex" onclick="pickMode(this)">Codex Novae</button>
    <button type="button" data-mode="web" onclick="pickMode(this)">Research</button>
    <button type="button" data-mode="offload" onclick="pickMode(this)">Real-world</button>
  </div>

  <main class="chat" id="chat" aria-live="polite">
    <div class="empty" id="empty">
      <div class="mark" style="margin:0 auto 14px">P</div>
      <h2>On the go</h2>
      <p>Plan the day, ship code, research, or queue real-world tasks. Agents run on the lab host — your phone is the remote desk.</p>
      <div class="quick">
        <button type="button" onclick="quick('Plan my top 3 for today and first step for each')">Day plan</button>
        <button type="button" onclick="quick('Review the current workspace and suggest the next code change')">Code next</button>
        <button type="button" onclick="quick('Research and summarize what I should do about: ')">Research</button>
        <button type="button" onclick="activateNovae('GROK_NOVAE')">Activate Grok Novae</button>
      </div>
    </div>
  </main>

  <div class="composer">
    <div class="row">
      <textarea id="input" rows="1" placeholder="Message… plan · code · real-world" disabled></textarea>
      <button class="send" id="sendBtn" type="button" disabled onclick="sendMsg()">↑</button>
    </div>
  </div>

  <nav class="nav" aria-label="Phone nav">
    <button type="button" class="on" onclick="focusChat()"><span>💬</span>Chat</button>
    <button type="button" onclick="pickModeBtn('plan')"><span>🗓</span>Plan</button>
    <button type="button" onclick="pickModeBtn('novae_codex')"><span>⚡</span>Novae</button>
    <button type="button" onclick="openSheet()"><span>⚙</span>More</button>
  </nav>
</div>

<div class="gate" id="gate">
  <div class="card">
    <h2>Unlock phone desk</h2>
    <p>Founder: ACCESS.txt. Members: your seat username + password (not founder disk).</p>
    <label>Username</label>
    <input id="loginUser" autocomplete="username" placeholder="pocket or your seat"/>
    <label>Password</label>
    <input id="loginPass" type="password" autocomplete="current-password"/>
    <button class="primary" type="button" id="loginBtn">Continue</button>
    <div class="err" id="loginErr"></div>
  </div>
</div>

<div class="sheet" id="sheet" onclick="if(event.target===this)closeSheet()">
  <div class="panel">
    <h3>Phone · platform</h3>
    <div class="novae-card">
      <b>Full desk</b>
      <small>Open the complete desktop UI if you need rails and agents.</small>
      <div class="row"><button type="button" class="go" onclick="location.href='/desk'">Open desk</button></div>
    </div>
    <div id="novaeList"><div class="novae-card"><small>Loading Novae…</small></div></div>
    <div class="novae-card">
      <b>Status</b>
      <small id="statusLine">—</small>
      <div class="row">
        <button type="button" onclick="refreshStatus()">Refresh</button>
        <button type="button" onclick="doLogout()">Sign out</button>
      </div>
    </div>
  </div>
</div>
<div class="toast" id="toast"></div>

<script>
const $ = id => document.getElementById(id);
let token = localStorage.getItem('pocket_token') || '';
let activeId = null;
let mode = 'plan';
let pollTimer = null;
let me = null;

function toast(t){
  const el=$('toast'); el.textContent=t; el.classList.add('show');
  setTimeout(()=>el.classList.remove('show'), 2200);
}
function esc(s){
  return String(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}
function authHeaders(){
  const h={'Content-Type':'application/json','X-Pocket-Device':'phone'};
  if(token) h['Authorization']='Bearer '+token;
  return h;
}
async function api(path, opts={}){
  const r = await fetch(path,{...opts, headers:{...authHeaders(), ...(opts.headers||{})}});
  const text = await r.text();
  let j={}; try{ j=text?JSON.parse(text):{}; }catch(_){ j={raw:text}; }
  if(!r.ok) throw new Error(j.error||j.message||('HTTP '+r.status));
  return j;
}

async function tryMe(){
  try{
    me = await api('/v1/auth/me');
    if(me && (me.user||me.ok!==false)){
      $('gate').classList.add('hidden');
      $('userChip').textContent = me.display || me.user || 'signed in';
      $('userChip').classList.add('on');
      $('input').disabled=false; $('sendBtn').disabled=false;
      await refreshStatus();
      await loadNovae();
      return true;
    }
  }catch(_){}
  $('gate').classList.remove('hidden');
  $('userChip').textContent='signed out';
  return false;
}

$('loginBtn').onclick = async ()=>{
  $('loginErr').textContent='';
  try{
    const j = await fetch('/v1/auth/login',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({username:$('loginUser').value.trim(), password:$('loginPass').value, remember:true})
    }).then(r=>r.json());
    if(!j.ok && !j.token && !j.session_token){
      throw new Error(j.error||'Login failed');
    }
    token = j.token || j.session_token || j.access_token || '';
    if(token) localStorage.setItem('pocket_token', token);
    // cookie session may also be set by server
    toast('Unlocked');
    await tryMe();
  }catch(e){
    $('loginErr').textContent=e.message||String(e);
  }
};

function pickMode(btn){
  document.querySelectorAll('.modes button').forEach(b=>b.classList.remove('on'));
  btn.classList.add('on');
  mode = btn.dataset.mode || 'plan';
  $('modeChip').textContent = btn.textContent.trim();
  activeId = null;
  showEmpty();
}
function pickModeBtn(m){
  const b=document.querySelector('.modes button[data-mode="'+m+'"]');
  if(b) pickMode(b);
}
function focusChat(){ $('input').focus(); }
function openSheet(){ $('sheet').classList.add('open'); loadNovae(); refreshStatus(); }
function closeSheet(){ $('sheet').classList.remove('open'); }

function showEmpty(){
  $('chat').innerHTML = $('empty') ? '' : '';
  const chat=$('chat');
  chat.innerHTML=`<div class="empty" id="empty">
    <div class="mark" style="margin:0 auto 14px">P</div>
    <h2>${esc(modeLabel())}</h2>
    <p>Send a message. Agents work on the lab host. Market seats stay in their sandbox — never founder personal files.</p>
    <div class="quick">
      <button type="button" onclick="quick('What should I do next? Be concrete.')">Next step</button>
      <button type="button" onclick="quick('Break this into a 5-step plan: ')">5-step plan</button>
      <button type="button" onclick="ensureSession()">Start ${esc(modeLabel())}</button>
    </div>
  </div>`;
}
function modeLabel(){
  return ({plan:'Plan',codex:'Code',grok:'Grok',novae_grok:'Grok Novae',novae_codex:'Codex Novae',web:'Research',offload:'Real-world'}[mode]||mode);
}

function quick(t){
  $('input').value=t;
  $('input').focus();
  if(t.endsWith(': ')||t.endsWith('about: ')) return;
  sendMsg();
}

async function ensureSession(){
  if(activeId) return activeId;
  // Novae: activate instance first (binds workspace)
  if(mode==='novae_grok'||mode==='novae_codex'){
    const id = mode==='novae_grok'?'GROK_NOVAE':'CODEX_NOVAE';
    try{
      const n = await api('/v1/novae/activate',{method:'POST',body:JSON.stringify({id, goal:'phone activate'})});
      if(n.session_id){ activeId=n.session_id; return activeId; }
    }catch(e){ toast(e.message); }
  }
  const j = await api('/v1/sessions',{method:'POST',body:JSON.stringify({
    mode, title: modeLabel()+' · phone',
    device:{kind:'phone',label:'Phone',remote:true}
  })});
  activeId = j.id;
  return activeId;
}

function thinkingEl(engine){
  const d=document.createElement('div');
  d.className='think'; d.id='thinking';
  d.innerHTML=`<div class="think-orb"></div><span>${esc(engine||mode)} thinking</span><span class="think-dots"><span></span><span></span><span></span></span>`;
  return d;
}

function formatBody(raw){
  const s=String(raw||'');
  // light fenced code
  if(s.includes('```')){
    return esc(s).replace(/```(\w*)\n([\s\S]*?)```/g,(_,lang,code)=>'<pre>'+code+'</pre>');
  }
  return esc(s);
}

async function sendMsg(){
  const text = ($('input').value||'').trim();
  if(!text) return;
  $('input').value='';
  try{
    await ensureSession();
  }catch(e){ toast('Start failed: '+e.message); return; }
  // clear empty
  if($('empty')) $('empty').remove();
  const chat=$('chat');
  const u=document.createElement('div');
  u.className='bubble user';
  u.innerHTML=`<div class="body">${esc(text)}</div>`;
  chat.appendChild(u);
  chat.appendChild(thinkingEl(mode));
  chat.scrollTop=chat.scrollHeight;
  try{
    await api('/v1/sessions/'+activeId+'/messages',{
      method:'POST',
      body:JSON.stringify({text, device:{kind:'phone',label:'Phone',remote:true}})
    });
    startPoll();
  }catch(e){
    const t=$('thinking'); if(t) t.remove();
    toast(e.message);
  }
}

function startPoll(){
  if(pollTimer) clearInterval(pollTimer);
  pollTimer=setInterval(refreshTranscript, 900);
  refreshTranscript();
}

async function refreshTranscript(){
  if(!activeId) return;
  try{
    const s = await api('/v1/sessions/'+activeId);
    const chat=$('chat');
    const stick = chat.scrollHeight - chat.scrollTop - chat.clientHeight < 100;
    chat.innerHTML='';
    const msgs=s.messages||[];
    if(!msgs.length){ showEmpty(); return; }
    let anyRun=false;
    msgs.forEach(m=>{
      const u=document.createElement('div');
      u.className='bubble user';
      u.innerHTML=`<div class="body">${esc(m.text||'')}</div>`;
      chat.appendChild(u);
      const streaming = m.status==='running'||m.status==='queued';
      if(streaming) anyRun=true;
      if(streaming && !(m.result||m.error)){
        chat.appendChild(thinkingEl(m.engine||s.mode));
      } else if(m.result||m.error||m.status==='done'||m.status==='failed'||m.status==='cancelled'){
        const a=document.createElement('div');
        a.className='bubble agent';
        const raw=m.result||m.error||(m.status==='cancelled'?'Stopped.':'');
        a.innerHTML=`<div class="meta"><span class="chip ${streaming?'on':''}">${esc(m.engine||s.mode)}</span> ${esc(m.status||'')}${m.stream_tokens?(' · ~'+m.stream_tokens+' tok'):''}</div>
          <div class="body">${formatBody(raw)}</div>`;
        chat.appendChild(a);
      }
    });
    if(!anyRun && pollTimer){ clearInterval(pollTimer); pollTimer=null; }
    if(stick) chat.scrollTop=chat.scrollHeight;
  }catch(e){ /* keep polling */ }
}

async function activateNovae(id){
  try{
    const n = await api('/v1/novae/activate',{method:'POST',body:JSON.stringify({id, goal:'phone hands'})});
    toast((n.title||id)+' active');
    if(n.mode){
      const b=document.querySelector('.modes button[data-mode="'+n.mode+'"]');
      if(b) pickMode(b);
    }
    if(n.session_id) activeId=n.session_id;
    closeSheet();
  }catch(e){ toast(e.message); }
}

async function loadNovae(){
  const box=$('novaeList');
  if(!box) return;
  try{
    const j = await api('/v1/novae');
    const agents=j.agents||[];
    box.innerHTML='';
    agents.forEach(a=>{
      const el=document.createElement('div');
      el.className='novae-card';
      el.innerHTML=`<b style="color:${esc(a.color||'#a78bfa')}">${esc(a.title||a.id)}</b>
        <small>${esc(a.tagline||'')} · ${a.active?'active':'standby'} · runs ${a.runs||0}</small>
        <div class="row">
          <button type="button" class="go" onclick="activateNovae('${esc(a.id)}')">Activate</button>
          <button type="button" onclick="pickModeBtn('${esc(a.mode)}');closeSheet()">Chat</button>
        </div>`;
      box.appendChild(el);
    });
  }catch(e){
    box.innerHTML='<div class="novae-card"><small>Sign in to load Novae hands.</small></div>';
  }
}

async function refreshStatus(){
  try{
    const h = await fetch('/health').then(r=>r.json());
    const heart = (h.heartbeat&&h.heartbeat.ok)?'heart ok':'heart warm';
    $('statusLine').textContent = `v${h.version||'?'} · ${heart} · ${location.host}`;
    $('modeChip').classList.add('on');
  }catch(_){
    $('statusLine').textContent='Host unreachable — wake lab PC / tunnel';
  }
}

async function doLogout(){
  try{ await api('/v1/auth/logout',{method:'POST',body:'{}'}); }catch(_){}
  token=''; localStorage.removeItem('pocket_token');
  location.reload();
}

$('input').addEventListener('keydown', e=>{
  if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); sendMsg(); }
});
// auto-grow
$('input').addEventListener('input', function(){
  this.style.height='auto'; this.style.height=Math.min(120, this.scrollHeight)+'px';
});

(async function boot(){
  await tryMe();
  // If already authed via cookie without bearer
  if($('gate').classList.contains('hidden')) showEmpty();
  // service worker optional — skip if none
})();
</script>
</body>
</html>
"""

PHONE_MANIFEST = """{
  "name": "POCKET Phone",
  "short_name": "POCKET",
  "description": "Code, plan, and real-world tasks on the go",
  "start_url": "/phone",
  "display": "standalone",
  "background_color": "#050508",
  "theme_color": "#050508",
  "orientation": "portrait-primary",
  "icons": []
}
"""


def phone_html() -> str:
    return PHONE_HTML


def phone_manifest() -> str:
    return PHONE_MANIFEST
