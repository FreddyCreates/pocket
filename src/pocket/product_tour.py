"""High-end product presentation + guided tour — AIS / Fusion-Sense narrative."""

from __future__ import annotations

from typing import Any, Dict, List

from pocket import __version__, PRODUCT, LAB


def tour_steps() -> List[Dict[str, Any]]:
    return [
        {
            "id": "ais",
            "title": "Agentic Interface Synthesis",
            "body": "Software is no longer only a binary you open. AIS weaves host-grounded outcomes from live OS state — the death of the GUI–API divide.",
            "api": "GET /v1/product/presentation",
            "try": "Read the tour · then open the desk",
        },
        {
            "id": "sense",
            "title": "Fusion Sense (not a VLM tourist)",
            "body": "Live desktop → 200–900+ symbols (UIA + OCR + visual). Semantic anchors and click targets. Resident intelligence, not a screenshot summary.",
            "api": "GET /v1/vision/page",
            "try": "Full page in System rail",
        },
        {
            "id": "rfe",
            "title": "Recursive synthesis (wf1 gold)",
            "body": "Signed fusion packets materialize into HTML remake, 3D scene JSON, and GLSL — 702-symbol class density when the host is rich.",
            "api": "POST /v1/rfe/synthesize",
            "try": "Skill rfe_synthesize",
        },
        {
            "id": "vcomp",
            "title": "Virtual computer + missions",
            "body": "Workspace, multi-terminals, sense→act→re-sense. Multi-hour queues when you leave agents working — not overnight until you say so.",
            "api": "POST /v1/vcomp/open · POST /v1/missions/start",
            "try": "Open vcomp → shell → sense",
        },
        {
            "id": "agents",
            "title": "Codex · Grok · Claude · NEXUS",
            "body": "One seat: coding agents, plan mode, NEXUS MERIDIAN workers. Same host, same fusion layer, one API.",
            "api": "GET /v1/nexus · POST /v1/orchestrator/chat",
            "try": "+ Codex / + Grok / + NEXUS",
        },
        {
            "id": "studio",
            "title": "Product glass, not desktop crop",
            "body": "Lifelike iPhone & web stages from product-remade frames. Screen record is for work capture; viral glass is remade for the device.",
            "api": "POST /v1/studio/product_phone",
            "try": "Studio · product phone",
        },
        {
            "id": "api",
            "title": "One catalog for every client",
            "body": "Grok Build, Codex, Claude, phone, desk — GET /v1/api. Auth: Basic / X-Pocket-Access / sk_pocket_.",
            "api": "GET /v1/api",
            "try": "Open /v1/api after sign-in",
        },
    ]


def presentation() -> Dict[str, Any]:
    from pocket.nexus_bridge import nexus_available
    from pocket.rfe_kernel import status as rfe_status
    from pocket.virtual_computer import status as vcomp_status

    nx = nexus_available()
    rfe = rfe_status()
    vc = vcomp_status()
    return {
        "ok": True,
        "product": PRODUCT,
        "version": __version__,
        "lab": LAB,
        "tagline": "Agentic Interface Synthesis on the host — Fusion Sense, not a CLI paste",
        "seo": {
            "title": "The Death of the GUI-API Divide: Agentic Interface Synthesis & The Future of Software",
            "description": "Explore the transition from static GUIs to autonomous Agentic Interface Synthesis (AIS). Real-time visual-semantic feedback loops on the host.",
            "primary_keyword": "Agentic Interface Synthesis",
            "secondary_keywords": [
                "Human-Computer Interface",
                "Autonomous Software Agents",
                "Fusion Sense",
                "UI/UX Evolution",
                "AI Workflow Automation",
                "GUI-API Divide",
            ],
        },
        "benchmarks": {
            "wf1": {"density": 702, "outcome": "HTML+3D RFE", "status": "gold"},
            "wf2": {"density": 446, "outcome": "legacy friction", "status": "studied_failure"},
            "wf3": {"density": 591, "outcome": "semantic click-path", "status": "success"},
            "latency_law": "≈12% symbolic throughput loss per 100ms environment lag",
        },
        "positioning": {
            "doctrine": "Fusion-Sense (wf1) is the baseline. AIS: author host outcomes, not clerk the filing cabinet.",
            "not": "Not Grok-CLI-only. Not RPA pixel scripts. Not desktop-in-a-bezel demos.",
            "is": "Host co-pilot with fusion graph, RFE remake, vcomp/missions, NEXUS, product studio, sellable API.",
            "quote": "The software of the future will not be shipped as a binary; it will be cultivated as a state-aware organism.",
            "research": [
                "Death of the GUI-API Divide (this paper)",
                "Fusion-Sense Interface Paradigm",
                "RFE-v1 Architectural Synthesis",
                "Latency Horizon AIS",
            ],
        },
        "tour": tour_steps(),
        "nexus": nx,
        "rfe": {"ok": rfe.get("ok"), "schema": rfe.get("schema"), "packets": rfe.get("packets")},
        "vcomp": {"status": (vc.get("state") or {}).get("status"), "workspace": vc.get("workspace")},
        "links": {
            "desk": "/",
            "tour": "/tour",
            "studio": "/studio",
            "api": "/v1/api",
            "health": "/health",
            "research_folder": "Documents/POCKET_Research/Death_of_GUI_API_Divide_AIS/",
        },
    }


TOUR_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>The Death of the GUI-API Divide — POCKET · Agentic Interface Synthesis</title>
<meta name="description" content="Explore the transition from static GUIs to autonomous Agentic Interface Synthesis (AIS). Fusion Sense, RFE remake, and host co-pilots that author software on the glass."/>
<meta name="keywords" content="Agentic Interface Synthesis, Fusion Sense, GUI-API Divide, Autonomous Software Agents, AI Workflow Automation, HCI"/>
<meta property="og:title" content="The Death of the GUI-API Divide: Agentic Interface Synthesis"/>
<meta property="og:description" content="From clerks of the OS to authors of synthesized environments. POCKET host co-pilot."/>
<meta property="og:type" content="website"/>
<meta name="theme-color" content="#07070a"/>
<style>
:root{
  --bg:#050508; --panel:rgba(18,18,22,.85); --line:rgba(255,255,255,.08);
  --text:#f4f4f5; --muted:#a1a1aa; --accent:#34d399; --blue:#60a5fa; --violet:#a78bfa; --amber:#fbbf24;
  --glow:0 0 80px rgba(52,211,153,.12);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:"Segoe UI",ui-sans-serif,system-ui,sans-serif;color:var(--text);min-height:100vh;
background:
  radial-gradient(1000px 600px at 15% -15%,rgba(52,211,153,.14),transparent 55%),
  radial-gradient(900px 500px at 95% 5%,rgba(96,165,250,.12),transparent 50%),
  radial-gradient(700px 400px at 50% 100%,rgba(167,139,250,.08),transparent 45%),
  var(--bg)}
.wrap{max-width:1120px;margin:0 auto;padding:28px 20px 96px}
.nav{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:40px;padding:12px 14px;border:1px solid var(--line);border-radius:16px;background:rgba(10,10,12,.7);backdrop-filter:blur(16px);position:sticky;top:12px;z-index:20}
.mark{width:38px;height:38px;border-radius:12px;background:linear-gradient(135deg,#34d399,#22d3ee 55%,#60a5fa);display:grid;place-items:center;font-weight:900;color:#052e16;box-shadow:var(--glow)}
.nav strong{letter-spacing:-.04em;font-size:15px}
.nav .grow{flex:1}
.nav a{color:var(--muted);text-decoration:none;font-size:12px;font-weight:650;padding:8px 12px;border:1px solid transparent;border-radius:999px}
.nav a:hover{color:var(--text);border-color:var(--line)}
.nav a.primary{background:linear-gradient(180deg,#34d399,#10b981);color:#052e16;border:0;box-shadow:0 8px 24px rgba(16,185,129,.25)}
.hero{display:grid;grid-template-columns:1.2fr .8fr;gap:28px;align-items:start;margin-bottom:36px}
@media(max-width:880px){.hero{grid-template-columns:1fr}}
.pill{display:inline-flex;align-items:center;gap:8px;font-size:11px;font-weight:750;letter-spacing:.08em;text-transform:uppercase;color:var(--accent);margin-bottom:14px}
.pill i{width:6px;height:6px;border-radius:50%;background:var(--accent);box-shadow:0 0 12px var(--accent)}
h1{font-size:clamp(30px,5.2vw,48px);letter-spacing:-.045em;margin:0 0 14px;line-height:1.05;font-weight:800}
.lead{font-size:17px;color:var(--muted);line-height:1.6;margin:0 0 18px;max-width:560px}
.quote{border-left:3px solid var(--accent);padding:10px 0 10px 16px;margin:18px 0;color:#d4d4d8;font-size:14px;line-height:1.55;font-style:italic}
.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-top:18px}
@media(max-width:600px){.stats{grid-template-columns:1fr}}
.stat{border:1px solid var(--line);border-radius:14px;padding:14px;background:var(--panel)}
.stat b{display:block;font-size:22px;letter-spacing:-.03em;color:var(--accent)}
.stat span{font-size:11px;color:var(--muted)}
.card{background:linear-gradient(180deg,rgba(255,255,255,.04),transparent),var(--panel);border:1px solid var(--line);border-radius:18px;padding:18px 18px 16px;box-shadow:0 24px 60px rgba(0,0,0,.35)}
.card h3{margin:0 0 8px;font-size:15px;letter-spacing:-.02em}
.card p{margin:0;font-size:13px;color:var(--muted);line-height:1.55}
.card code{display:block;margin-top:12px;font-size:11px;color:var(--accent);font-family:ui-monospace,Consolas,monospace;word-break:break-all}
.sec{margin:40px 0 16px;font-size:12px;font-weight:750;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px}
.diff{display:grid;grid-template-columns:1fr 1fr;gap:14px}
@media(max-width:700px){.diff{grid-template-columns:1fr}}
.diff h4{margin:0 0 10px;font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted)}
.diff ul{margin:0;padding-left:18px;color:var(--muted);font-size:13px;line-height:1.6}
.bench{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
.bench th,.bench td{border-bottom:1px solid var(--line);padding:10px 8px;text-align:left}
.bench th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.06em}
.bench td.gold{color:var(--accent);font-weight:700}
.cta-row{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}
.cta-row a{text-decoration:none;font-size:13px;font-weight:700;padding:12px 18px;border-radius:12px;border:1px solid var(--line);color:var(--text)}
.cta-row a.p{background:linear-gradient(180deg,#34d399,#10b981);color:#052e16;border:0}
.foot{margin-top:48px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:12px;line-height:1.6}
.badge{display:inline-block;font-size:10px;font-weight:800;padding:3px 8px;border-radius:999px;border:1px solid #14532d;background:#052e16;color:#86efac}
</style>
</head>
<body>
<div class="wrap">
  <nav class="nav">
    <div class="mark">P</div>
    <strong>POCKET</strong>
    <span style="font-size:11px;color:var(--muted)">Agentic Interface Synthesis</span>
    <div class="grow"></div>
    <a href="#benchmarks">Benchmarks</a>
    <a href="#pillars">Fusion Sense</a>
    <a href="#tour">Tour</a>
    <a href="/studio">Studio</a>
    <a href="/v1/api">API</a>
    <a class="primary" href="/">Open desk</a>
  </nav>

  <section class="hero">
    <div>
      <div class="pill"><i></i> Phase transition · GUI–API divide</div>
      <h1>The death of the GUI–API divide.<br/>The birth of synthesized environments.</h1>
      <p class="lead">For forty years we were clerks behind glass — clicking filing cabinets. <strong style="color:var(--text)">Agentic Interface Synthesis</strong> turns the host into a living graph of intent. You do not only use software. You author host-grounded outcomes.</p>
      <div class="quote">“The software of the future will not be shipped as a binary; it will be cultivated as a state-aware organism.”</div>
      <div class="cta-row">
        <a class="p" href="/">Enter the desk</a>
        <a href="/studio">Product studio</a>
        <a href="#tour">Walk the tour</a>
      </div>
    </div>
    <div class="card">
      <div class="pill">wf-series · live host</div>
      <h3>Symbolic density is the KPI</h3>
      <p>Not LOC/hour. How much of the living desktop the agent can bind into actionable structure — then remake and act.</p>
      <div class="stats">
        <div class="stat"><b>702</b><span>wf1 Fusion Sense gold</span></div>
        <div class="stat"><b>591</b><span>wf3 web click-path</span></div>
        <div class="stat"><b>12%</b><span>loss / 100ms lag</span></div>
      </div>
      <p style="margin-top:14px;font-size:12px;color:var(--muted)">Latency is the intelligence governor. Close vision → execution.</p>
    </div>
  </section>

  <div class="sec" id="benchmarks">Empirical benchmarks</div>
  <div class="card">
    <table class="bench">
      <thead><tr><th>ID</th><th>Context</th><th>Density</th><th>Outcome</th><th>Status</th></tr></thead>
      <tbody>
        <tr><td class="gold">wf1</td><td>Fusion Sense + Remake</td><td class="gold">702</td><td>HTML + 3D RFE assembly</td><td><span class="badge">GOLD</span></td></tr>
        <tr><td>wf2</td><td>Notepad + Explorer</td><td>446</td><td>Semantic drift / friction</td><td>Studied</td></tr>
        <tr><td>wf3</td><td>Edge + GitHub</td><td>591</td><td>Semantic click-path</td><td>Success</td></tr>
      </tbody>
    </table>
  </div>

  <div class="sec">Not “just Grok CLI”</div>
  <div class="diff">
    <div class="card">
      <h4>Chat / CLI alone</h4>
      <ul>
        <li>Prompt → text / files</li>
        <li>No host symbol graph</li>
        <li>Brittle when UI moves</li>
        <li>No product remake pipeline</li>
      </ul>
    </div>
    <div class="card">
      <h4>POCKET · AIS host</h4>
      <ul>
        <li>Fusion Sense: UIA + OCR + visual</li>
        <li>RFE remake + signed packets</li>
        <li>Vcomp, missions, NEXUS</li>
        <li>Product phone/web stages</li>
        <li>One sellable API catalog</li>
      </ul>
    </div>
  </div>

  <div class="sec" id="pillars">Fusion Sense pillars</div>
  <div class="grid">
    <div class="card"><h3>1. State snapshotting</h3><p>Desktop → structured JSON symbol graph — a digital twin of the glass, not a tourist screenshot.</p></div>
    <div class="card"><h3>2. Semantic anchoring</h3><p>Intent-based controls: kind, text, bbox, click — RPA dies when pixels shift; AIS does not.</p></div>
    <div class="card"><h3>3. Recursive synthesis</h3><p>Micro-modules with re-sense: sense → act → verify → remake. Sanity guards on system-level risk.</p></div>
  </div>

  <div class="sec" id="tour">Product tour</div>
  <div class="grid" id="steps"></div>

  <div class="sec">Research & doctrine</div>
  <div class="card">
    <p>Full paper: <strong>The Death of the GUI-API Divide</strong> · Fusion-Sense Interface Paradigm · RFE-v1 · Latency Horizon — under Documents/POCKET_Research. Product doctrine: Fusion-Sense (wf1) is the baseline for every engine.</p>
    <code>GET /v1/product/presentation · GET /v1/api · POST /v1/rfe/synthesize</code>
  </div>

  <p class="foot">ItsNotAI Labs · POCKET · From User to Author · The screen becomes a shadow of intent.</p>
</div>
<script>
const STEPS = __STEPS__;
document.getElementById('steps').innerHTML = STEPS.map((s,i)=>`
  <div class="card">
    <div class="pill"><i></i> 0${i+1}</div>
    <h3>${s.title}</h3>
    <p>${s.body}</p>
    <code>${s.api||''}</code>
    <p style="margin-top:10px;font-size:12px;color:#86efac">Try: ${s.try||''}</p>
  </div>`).join('');
</script>
</body>
</html>
"""


def tour_html() -> str:
    """Product hub (Overview) — connected entry to Desktop, API, Studio.

    Research manifesto retained in docs/research; /tour is the cohesive product front door.
    """
    from pocket.product_shell import hub_html

    return hub_html()
