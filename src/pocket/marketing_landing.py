"""One-app marketing landing: Desktop · API · Studio · MESIE — all clickable."""

from __future__ import annotations

from pocket import COMPANY, LAB, ORG, __version__
from pocket.product_shell import SHELL_CSS, shell_nav

GITHUB = "https://github.com/ItsNotAILABS/pocket"


def get_app_html() -> str:
    """Standalone-feeling Get page — share this URL for distribution."""
    nav = shell_nav(active="get")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Get POCKET — {COMPANY} company host platform</title>
<meta name="description" content="POCKET by {LAB}: company multi-agent host. Team seats, Edge app, Windows download, sellable API."/>
<meta name="theme-color" content="#09090b"/>
<style>
:root{{--bg:#09090b;--panel:#141416;--line:rgba(255,255,255,.1);--text:#e4e4e7;--muted:#a1a1aa;--fg:#fafafa;--accent:#10a37f;--accent2:#0d8c6c}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);line-height:1.55;-webkit-font-smoothing:antialiased}}
a{{color:inherit;text-decoration:none}}
{SHELL_CSS}
.wrap{{max-width:880px;margin:0 auto;padding:48px 22px 80px}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:12px}}
h1{{font-size:clamp(28px,4vw,40px);letter-spacing:-.04em;margin:0 0 12px;color:var(--fg)}}
.lead{{color:var(--muted);max-width:560px;margin:0 0 32px;font-size:16px}}
.step{{border:1px solid var(--line);border-radius:16px;padding:22px;background:var(--panel);margin-bottom:14px}}
.step h2{{margin:0 0 8px;font-size:17px;color:var(--fg);letter-spacing:-.02em}}
.step p{{margin:0 0 12px;color:var(--muted);font-size:14px}}
.step ol{{margin:0 0 12px;padding-left:18px;color:var(--muted);font-size:13.5px}}
.step li{{margin:4px 0}}
.btn{{display:inline-flex;align-items:center;padding:11px 16px;border-radius:10px;font-weight:700;font-size:13.5px;border:1px solid transparent;margin-right:8px;margin-top:4px}}
.btn-primary{{background:var(--accent);color:#041}}
.btn-primary:hover{{background:var(--accent2)}}
.btn-ghost{{border-color:var(--line);color:var(--fg)}}
.btn-ghost:hover{{background:rgba(255,255,255,.06)}}
code{{color:var(--accent);font-size:12.5px}}
.note{{font-size:13px;color:var(--muted);border:1px solid var(--line);border-radius:12px;padding:14px 16px;background:#0c0c0e;margin-top:20px}}
.foot{{margin-top:36px;font-size:12px;color:var(--muted)}}
.foot a{{color:var(--muted);margin-right:12px}}
.foot a:hover{{color:var(--fg)}}
</style>
</head>
<body>
{nav}
<main class="wrap">
  <div class="eyebrow">{COMPANY} · {LAB} · company edition</div>
  <h1>Get POCKET</h1>
  <p class="lead">Company multi-agent host for your team. <strong>Market seats</strong> get their own sandbox — never the operator’s personal disk. Built for organizations that keep data on their infrastructure.</p>

  <div class="step" id="web">
    <h2>1 · Create a market seat</h2>
    <p>Open the desk → <strong>Create my seat</strong> with a <code>pk_seat_…</code> invite. You work in your platform space (files + local sandbox + git). You do not browse the operator’s disk.</p>
    <a class="btn btn-primary" href="/desk">Open desk</a>
    <a class="btn btn-ghost" href="/tour">Overview</a>
  </div>

  <div class="step" id="edge">
    <h2>2 · Edge app (what you like on this PC)</h2>
    <p>Opens as a real window — not a random tab. On the operator PC, use the <strong>POCKET</strong> desktop shortcut
    (install ship script once) so the host auto-starts, then Edge opens <code>/desk</code> as an app.</p>
    <ol>
      <li>Operator: run <code>scripts\\Install-POCKET-Ship.ps1</code> once.</li>
      <li>Double-click <strong>POCKET</strong> on the Desktop anytime.</li>
      <li>Or in Edge: ⋯ → Apps → <strong>Install this site as an app</strong>.</li>
    </ol>
    <a class="btn btn-primary" href="/desk">Open desk (then Install as app)</a>
  </div>

  <div class="step" id="exe">
    <h2>3 · Electron / Windows .exe</h2>
    <p>Classic download for users who want an installer/portable. Marketing site can point here after pay/account.</p>
    <a class="btn btn-primary" href="/download">Download page</a>
    <a class="btn btn-ghost" href="/download/desktop">Direct Windows package</a>
    <a class="btn btn-ghost" href="{GITHUB}/releases" target="_blank" rel="noopener">GitHub Releases</a>
  </div>

  <div class="step" id="multi">
    <h2>Company multi-user seats</h2>
    <p>Invite-gated team accounts (not open SaaS). Operator mints <code>pk_seat_…</code> keys.
    Members create <strong>their own</strong> username + password → RBAC + quotas. Founder disk stays private.</p>
  </div>

  <div class="step" id="api">
    <h2>API (builders)</h2>
    <p>Machine access for agents and scripts — separate from human download.</p>
    <a class="btn btn-ghost" href="/developers">Developers / API</a>
  </div>

  <div class="note">
    <strong>Product rule:</strong> never thrash the host or Cloudflare tunnel.
    Always-on keeps <code>:8787</code> up; Edge/Electron only open the UI.
    Funnel later: marketing site → pay/account → download Electron or open cloud desk.
  </div>

  <div class="foot">
    <a href="/tour">Overview</a>
    <a href="/desk">Desk</a>
    <a href="/download">Download</a>
    <a href="/studio">Studio</a>
    <span>v{__version__} · {COMPANY} · {LAB}</span>
  </div>
</main>
</body>
</html>
"""


def landing_html() -> str:
    nav = shell_nav(active="overview")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>POCKET — {COMPANY} company multi-agent host</title>
<meta name="description" content="POCKET by {LAB}: company host co-pilot. Desktop, API, Studio, team seats. Your infrastructure."/>
<meta name="theme-color" content="#09090b"/>
<style>
:root{{--bg:#09090b;--panel:#141416;--line:rgba(255,255,255,.1);--text:#e4e4e7;--muted:#a1a1aa;--fg:#fafafa;--accent:#10a37f;--accent2:#0d8c6c}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);line-height:1.55;-webkit-font-smoothing:antialiased}}
a{{color:inherit;text-decoration:none;cursor:pointer}}
{SHELL_CSS}
.pnav a,.pnav .cta,.pnav .ghost,.btn,.card-link,.go{{pointer-events:auto!important;position:relative;z-index:2}}
.hero{{padding:64px 22px 48px;border-bottom:1px solid var(--line);position:relative}}
.hero-inner{{max-width:1040px;margin:0 auto;position:relative;z-index:1}}
.eyebrow{{font-size:12px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:14px}}
h1{{font-size:clamp(32px,5vw,48px);line-height:1.08;letter-spacing:-.04em;margin:0 0 14px;color:var(--fg);max-width:18ch}}
.lead{{font-size:17px;color:var(--muted);max-width:540px;margin:0 0 24px}}
.cta-row{{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:28px}}
.btn{{display:inline-flex;align-items:center;padding:12px 18px;border-radius:10px;font-weight:700;font-size:14px;border:1px solid transparent}}
.btn-primary{{background:var(--accent);color:#041}}
.btn-primary:hover{{background:var(--accent2)}}
.btn-ghost{{border-color:var(--line);color:var(--fg)}}
.btn-ghost:hover{{background:rgba(255,255,255,.06)}}
.proof{{display:flex;flex-wrap:wrap;gap:8px}}
.proof span{{font-size:12px;color:var(--muted);border:1px solid var(--line);padding:6px 11px;border-radius:999px}}
.section{{max-width:1040px;margin:0 auto;padding:56px 22px}}
.section h2{{font-size:28px;letter-spacing:-.03em;margin:0 0 8px;color:var(--fg)}}
.section .sub{{color:var(--muted);margin:0 0 24px}}
.grid4{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}}
@media(max-width:1000px){{.grid4{{grid-template-columns:1fr 1fr}}}}
@media(max-width:640px){{.grid4{{grid-template-columns:1fr}}}}
/* ENTIRE card is one link — always clickable */
a.card-link{{
  display:flex;flex-direction:column;min-height:220px;padding:22px;border-radius:16px;
  border:1px solid var(--line);background:var(--panel);transition:border-color .15s,transform .12s;
  color:inherit
}}
a.card-link:hover{{border-color:rgba(16,163,127,.45);transform:translateY(-2px);background:#16161a}}
a.card-link .tag{{font-size:11px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:var(--accent);margin-bottom:8px}}
a.card-link h3{{margin:0 0 8px;font-size:18px;color:var(--fg)}}
a.card-link p{{margin:0;font-size:13.5px;color:var(--muted);flex:1}}
a.card-link .go{{margin-top:16px;font-weight:700;font-size:13px;color:var(--accent)}}
.live{{display:flex;align-items:center;gap:8px;font-size:12px;color:var(--muted);margin-top:20px}}
.live i{{width:8px;height:8px;border-radius:50%;background:var(--accent);display:inline-block;animation:pulse 1.2s infinite}}
@keyframes pulse{{50%{{opacity:.35}}}}
.foot{{border-top:1px solid var(--line);padding:22px;font-size:12px;color:var(--muted)}}
.foot-inner{{max-width:1040px;margin:0 auto;display:flex;flex-wrap:wrap;gap:12px;justify-content:space-between}}
.foot a{{color:var(--muted);margin-left:12px}}
.foot a:hover{{color:var(--fg)}}
</style>
</head>
<body>
{nav}
<section class="hero">
  <div class="hero-inner">
    <div class="eyebrow">One platform · not four products</div>
    <h1>Desktop, API, Studio &amp; MESIE — same host.</h1>
    <p class="lead">Click any surface. Same sign-in. Same runtime worker (873ms heartbeat). Built to use, not babysit.</p>
    <div class="cta-row">
      <a class="btn btn-primary" href="/desk">Use web app now</a>
      <a class="btn btn-ghost" href="/get">How people get POCKET</a>
      <a class="btn btn-ghost" href="/download">Windows .exe</a>
      <a class="btn btn-ghost" href="/developers">API</a>
      <a class="btn btn-ghost" href="/studio">Studio</a>
    </div>
    <div class="proof">
      <span>Web app (most stable)</span>
      <span>Edge app window</span>
      <span>Windows .exe</span>
      <span>v{__version__}</span>
    </div>
    <div class="live"><i></i> <span id="heartLabel">Runtime heartbeat…</span></div>
  </div>
</section>

<section class="section" id="get">
  <h2>How people get POCKET</h2>
  <p class="sub">Three real doors — pick one. No separate product to babysit.</p>
  <div class="grid4">
    <a class="card-link" href="/desk">
      <div class="tag">1 · Web app</div>
      <h3>Use in the browser</h3>
      <p>Share <code style="color:var(--accent)">/desk</code> or your public host. Most stable. Same Edge profile as the app window.</p>
      <span class="go">Open web app →</span>
    </a>
    <a class="card-link" href="/get#edge">
      <div class="tag">2 · Edge app</div>
      <h3>Install as app</h3>
      <p>Edge → ··· → Apps → Install this site as an app. Launches from your website, stays on.</p>
      <span class="go">How to install →</span>
    </a>
    <a class="card-link" href="/download">
      <div class="tag">3 · Windows .exe</div>
      <h3>Download package</h3>
      <p>Portable or installer. Desktop shortcut. Wraps the same desk UI.</p>
      <span class="go">Download .exe →</span>
    </a>
    <a class="card-link" href="/developers">
      <div class="tag">API</div>
      <h3>Builders &amp; agents</h3>
      <p>sk_pocket keys for Grok, Codex, Claude, scripts. Not the human UI — the machine door.</p>
      <span class="go">Open API →</span>
    </a>
  </div>
</section>

<section class="section" id="products">
  <h2>Everything is one click</h2>
  <p class="sub">Whole cards are links — nothing is decorative-only.</p>
  <div class="grid4">
    <a class="card-link" href="/desk">
      <div class="tag">Web desk</div>
      <h3>Operator desk</h3>
      <p>Most stable surface — chat, agents, vision, mesh. Same UI the .exe wraps.</p>
      <span class="go">Open web desk →</span>
    </a>
    <a class="card-link" href="/get">
      <div class="tag">Get</div>
      <h3>Give people a link</h3>
      <p>Web app, Edge install, and .exe download in one place — ready for marketing.</p>
      <span class="go">Get POCKET →</span>
    </a>
    <a class="card-link" href="/developers">
      <div class="tag">API</div>
      <h3>Builder keys</h3>
      <p>sk_pocket keys, catalog, complete. Same host as Desktop.</p>
      <span class="go">Open API →</span>
    </a>
    <a class="card-link" href="/studio">
      <div class="tag">Studio</div>
      <h3>Product demos</h3>
      <p>Phone/web remakes and packs for marketing and beta.</p>
      <span class="go">Open Studio →</span>
    </a>
  </div>
</section>

<footer class="foot">
  <div class="foot-inner">
    <div>© {COMPANY} · {LAB} · POCKET company edition</div>
    <div>
      <a href="/desk">Desktop</a>
      <a href="/download">Download</a>
      <a href="/developers">API</a>
      <a href="/studio">Studio</a>
      <a href="/desk?agent=mesie">MESIE</a>
    </div>
  </div>
</footer>
<script>
(async function(){{
  try{{
    const r=await fetch('/health');
    const j=await r.json();
    const h=j.heartbeat||{{}};
    const el=document.getElementById('heartLabel');
    if(el){{
      if(h.beat!=null) el.textContent='Runtime beat #'+h.beat+' · '+(h.interval_ms||873)+'ms · host live';
      else el.textContent='Host live · start runtime-worker for 873ms heart';
    }}
  }}catch(e){{
    const el=document.getElementById('heartLabel');
    if(el) el.textContent='Host offline — run Launch-POCKET.cmd';
  }}
}})();
</script>
</body>
</html>
"""
