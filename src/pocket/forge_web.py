"""Companion site: sovereign forge (next-level git, not commercial GitHub).

Served at /forge — Medina Memory–inspired calm sovereign aesthetic, product not SaaS hard-sell.
"""

from __future__ import annotations


def forge_landing_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>POCKET Forge — Sovereign Git</title>
<style>
:root{--bg:#07080c;--fg:#e8eaef;--muted:#8b93a7;--line:#1c2230;--accent:#6ee7b7;--dim:#12151e}
*{box-sizing:border-box}
body{margin:0;font-family:ui-sans-serif,system-ui,Segoe UI,sans-serif;background:radial-gradient(1200px 600px at 20% -10%,#12201a 0%,var(--bg) 55%);color:var(--fg);line-height:1.55}
a{color:var(--accent);text-decoration:none}
.wrap{max-width:920px;margin:0 auto;padding:48px 22px 80px}
.badge{display:inline-block;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);border:1px solid var(--line);padding:4px 10px;border-radius:999px}
h1{font-size:clamp(1.8rem,4vw,2.6rem);letter-spacing:-.03em;margin:18px 0 10px;font-weight:650}
.lead{color:var(--muted);font-size:1.05rem;max-width:38rem}
.grid{display:grid;gap:14px;margin:36px 0;grid-template-columns:repeat(auto-fit,minmax(220px,1fr))}
.card{background:var(--dim);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.card h3{margin:0 0 8px;font-size:14px;font-weight:600}
.card p{margin:0;color:var(--muted);font-size:13px}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin-top:28px}
.btn{display:inline-flex;align-items:center;padding:10px 16px;border-radius:10px;font-weight:600;font-size:14px;border:1px solid var(--line)}
.btn.primary{background:var(--accent);color:#042;border-color:transparent}
.btn.ghost{background:transparent;color:var(--fg)}
code{font-family:ui-monospace,monospace;font-size:12px;background:#0c0f16;padding:2px 6px;border-radius:4px}
footer{margin-top:48px;color:var(--muted);font-size:12px}
</style>
</head>
<body>
<div class="wrap">
  <span class="badge">POCKET · Sovereign Forge</span>
  <h1>Git without the landlord.</h1>
  <p class="lead">
    Create repositories inside POCKET. Same <code>git</code> you know — vaulted on your host,
    exportable as zip, cloneable by path. Companion to the multi-agent desk: cowork demos,
    proofs, and code that stays yours.
  </p>
  <div class="cta">
    <a class="btn primary" href="/desk">Open desk</a>
    <a class="btn ghost" href="/download">Download POCKET</a>
    <a class="btn ghost" href="/get">Get / install</a>
    <a class="btn ghost" href="https://github.com/FreddyCreates/pocket" target="_blank" rel="noopener">Source</a>
  </div>
  <div class="grid">
    <div class="card"><h3>Vault repos</h3><p>Create git projects under the host vault with <code>pocket.toml</code>. No account tax.</p></div>
    <div class="card"><h3>Real git</h3><p>Clone with standard git. Zip export to your files. TOML metadata, not platform lock-in.</p></div>
    <div class="card"><h3>Cowork + record</h3><p>Desktop embodiment and screen record for demos — not only terminal coding.</p></div>
    <div class="card"><h3>Ghost math</h3><p>Deterministic hash chains and stats agents — compute, don't guess.</p></div>
  </div>
  <p class="lead" style="font-size:14px">
    Inspired by memory-first systems: calm surfaces, durable artifacts, sovereignty over the feed.
    Decentralized hosting is the roadmap — today the forge is host-local and exportable.
  </p>
  <footer>ItsNotAI Labs · Medina Tech · POCKET Forge alpha</footer>
</div>
</body>
</html>
"""
