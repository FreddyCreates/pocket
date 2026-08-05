"""Public documentation + downloads hub (research surface)."""

from __future__ import annotations

from pathlib import Path

from pocket.license_gate import license_meta


def docs_hub_html() -> str:
    lic = license_meta()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>POCKET Docs Hub — Research</title>
<meta name="theme-color" content="#09090b"/>
<style>
:root{{--bg:#09090b;--panel:#141416;--line:rgba(255,255,255,.1);--text:#e4e4e7;--muted:#a1a1aa;--fg:#fafafa;--accent:#10a37f}}
*{{box-sizing:border-box}}
body{{margin:0;font-family:ui-sans-serif,system-ui,sans-serif;background:var(--bg);color:var(--text);line-height:1.55}}
a{{color:var(--accent);text-decoration:none}}
.wrap{{max-width:960px;margin:0 auto;padding:40px 20px 80px}}
h1{{letter-spacing:-.03em;color:var(--fg);margin:0 0 8px}}
.lead{{color:var(--muted);max-width:640px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:14px;margin-top:28px}}
.card{{border:1px solid var(--line);border-radius:14px;padding:18px;background:var(--panel)}}
.card h2{{margin:0 0 8px;font-size:15px;color:var(--fg)}}
.card p{{margin:0;font-size:13px;color:var(--muted)}}
.nav{{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}}
.nav a{{border:1px solid var(--line);padding:8px 12px;border-radius:9px;color:var(--fg);font-size:13px;font-weight:600}}
.pill{{display:inline-block;font-size:11px;border:1px solid var(--line);padding:3px 8px;border-radius:999px;color:var(--muted)}}
</style>
</head>
<body>
<main class="wrap">
  <span class="pill">ItsNotAI Labs · research surface</span>
  <h1>POCKET documentation hub</h1>
  <p class="lead">Product docs, security model, WSL native agent story, and researcher-only downloads. Commercial production needs a separate license.</p>
  <div class="nav">
    <a href="/download">Downloads</a>
    <a href="/license">License</a>
    <a href="/desk">Desk</a>
    <a href="/phone">Phone</a>
    <a href="/developers">API</a>
  </div>
  <div class="grid">
    <a class="card" href="/download"><h2>Downloads</h2><p>Windows packages after Researcher License accept. License id: {lic.get("id")}.</p></a>
    <a class="card" href="/license/text"><h2>Researcher License</h2><p>Non-commercial research &amp; evaluation only. Full legal text.</p></a>
    <a class="card" href="/v1/wsl"><h2>WSL native agent</h2><p>JSON probe — first-class Linux hands on the host (auth for run).</p></a>
    <div class="card"><h2>Security model</h2><p>Founder host ≠ market seat. Market never gets founder personal disk. See repo docs/SECURITY.md.</p></div>
    <div class="card"><h2>Editions</h2><p>Founder POCKET (your machine) vs Market seats (their sandbox). Invite ≠ laptop tour.</p></div>
    <div class="card"><h2>Repos map</h2><p><code>pocket</code> runtime · <code>pocket-app</code> hub · org: ItsNotAILABS.</p></div>
    <div class="card"><h2>Phone</h2><p>Mobile web app for plan / code / real-world / Novae on the go.</p></div>
    <div class="card"><h2>WSL story</h2><p>Native Linux agent: distros, ~/pocket-wsl workspace, NL + shell, safety policy.</p></div>
  </div>
</main>
</body>
</html>
"""


def license_page_html() -> str:
    lic = license_meta()
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>{lic.get("title")}</title>
<style>
body{{margin:0;font-family:ui-sans-serif,system-ui,sans-serif;background:#09090b;color:#e4e4e7;line-height:1.55}}
.wrap{{max-width:720px;margin:0 auto;padding:40px 20px}}
h1{{color:#fafafa;letter-spacing:-.03em}}
a{{color:#10a37f}}
.card{{border:1px solid rgba(255,255,255,.1);border-radius:14px;padding:20px;background:#141416}}
</style>
</head>
<body>
<main class="wrap">
  <h1>POCKET Researcher License</h1>
  <div class="card">
    <p><strong>{lic.get("id")}</strong> — {lic.get("summary")}</p>
    <p><a href="/license/text">Full text</a> · <a href="/download">Downloads</a> · <a href="/docs/hub">Docs hub</a></p>
  </div>
</main>
</body>
</html>
"""


def license_text() -> str:
    root = Path(__file__).resolve().parents[2]
    for p in (root / "LICENSE-RESEARCHER.md", root / "LICENSE"):
        if p.exists():
            return p.read_text(encoding="utf-8")
    return "LICENSE-RESEARCHER.md missing on host."
