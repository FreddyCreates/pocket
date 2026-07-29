"""Shared product chrome — same nav/thread across Overview, Desktop, API, Studio."""

from __future__ import annotations

# Injected into Overview + Developers (and can mirror in desk top bar).
SHELL_CSS = """
.pnav{display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:11px 18px;border-bottom:1px solid rgba(255,255,255,.07);background:rgba(9,9,11,.94);position:sticky;top:0;z-index:30;backdrop-filter:blur(16px)}
.pnav .brand{display:flex;align-items:center;gap:9px;font-weight:650;letter-spacing:-.03em;font-size:13.5px;color:#fafafa;text-decoration:none;margin-right:6px}
.pnav .brand i{width:22px;height:22px;border-radius:7px;background:linear-gradient(145deg,#10a37f,#0a7a5f);display:grid;place-items:center;font-size:11px;font-weight:800;color:#041;font-style:normal;box-shadow:0 0 0 1px rgba(16,163,127,.3)}
.pnav .links{display:flex;gap:1px;flex-wrap:wrap;background:rgba(255,255,255,.03);padding:2px;border-radius:9px;border:1px solid rgba(255,255,255,.07)}
.pnav .links a{color:#71717a;text-decoration:none;font-size:12.5px;font-weight:550;padding:6px 12px;border-radius:7px}
.pnav .links a:hover{color:#e4e4e7;background:rgba(255,255,255,.05)}
.pnav .links a.on{color:#fafafa;background:#1a1a1e;box-shadow:0 0 0 1px rgba(255,255,255,.05)}
.pnav .sp{flex:1}
.pnav .pill{font-size:11px;color:#71717a;border:1px solid rgba(255,255,255,.07);padding:5px 10px;border-radius:999px}
.pnav .cta{font-size:12.5px;font-weight:650;color:#041;background:#10a37f;padding:8px 14px;border-radius:8px;text-decoration:none}
.pnav .cta:hover{background:#0d8c6c;text-decoration:none}
.pnav .ghost{font-size:12.5px;color:#71717a;border:1px solid rgba(255,255,255,.07);padding:7px 12px;border-radius:8px;text-decoration:none}
.pnav .ghost:hover{color:#e4e4e7;text-decoration:none}
"""


def shell_nav(*, active: str = "overview") -> str:
    """active: overview | desktop | api | studio | download | get | mesie"""
    def cls(name: str) -> str:
        return ' class="on"' if name == active else ""

    return f"""
<header class="pnav">
  <a class="brand" href="/tour"><i>P</i>POCKET</a>
  <nav class="links" aria-label="Product">
    <a href="/"{cls("overview")}>Overview</a>
    <a href="/desk"{cls("desktop")}>Desktop</a>
    <a href="/get"{cls("get")}>Get app</a>
    <a href="/download"{cls("download")}>Download</a>
    <a href="/developers"{cls("api")}>API</a>
    <a href="/studio"{cls("studio")}>Studio</a>
    <a href="/desk?agent=mesie"{cls("mesie")}>MESIE</a>
  </nav>
  <div class="sp"></div>
  <span class="pill">Web app · Edge · .exe</span>
  <a class="ghost" href="/get">How to get</a>
  <a class="cta" href="/desk">Open web app</a>
</header>
"""


PRODUCT_HUB_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>POCKET — Desktop · API · Studio</title>
<meta name="description" content="POCKET host co-pilot: Desktop for you, API for Grok/Codex/Claude, Studio for product demos."/>
<meta name="theme-color" content="#000"/>
<style>
:root{--bg:#09090b;--panel:#141416;--line:rgba(255,255,255,.07);--text:#e4e4e7;--muted:#71717a;--accent:#10a37f;--fg:#fafafa}
*{box-sizing:border-box}body{margin:0;font-family:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;background:var(--bg);color:var(--text);line-height:1.5;-webkit-font-smoothing:antialiased}
__SHELL_CSS__
.wrap{max-width:980px;margin:0 auto;padding:48px 22px 88px}
h1{font-size:clamp(28px,4.2vw,40px);letter-spacing:-.04em;font-weight:600;margin:0 0 12px;line-height:1.1;color:var(--fg)}
.lead{font-size:15.5px;color:var(--muted);max-width:540px;margin:0 0 32px;line-height:1.55}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin:28px 0}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.card{border:1px solid var(--line);border-radius:14px;padding:22px;background:var(--panel);display:flex;flex-direction:column;min-height:210px;transition:border-color .15s,box-shadow .15s}
.card:hover{border-color:rgba(16,163,127,.28);box-shadow:0 0 0 1px rgba(16,163,127,.08)}
.card h3{margin:0 0 8px;font-size:16px;font-weight:600;letter-spacing:-.02em;color:var(--fg)}
.card p{margin:0;font-size:13px;color:var(--muted);flex:1;line-height:1.5}
.card .go{margin-top:16px;display:inline-flex;align-items:center;gap:6px;font-size:13px;font-weight:650;color:#041;background:var(--accent);padding:9px 14px;border-radius:8px;text-decoration:none;width:fit-content}
.card .go:hover{background:#0d8c6c}
.card .meta{font-size:11px;color:var(--muted);margin-top:10px}
.note{border:1px solid var(--line);border-radius:12px;padding:16px 18px;background:#0c0c0e;margin-top:28px;font-size:13px;color:var(--muted)}
.note strong{color:var(--fg)}
.note code{color:var(--accent);font-size:12px}
.foot{margin-top:40px;font-size:12px;color:var(--muted)}
</style>
</head>
<body>
__SHELL_NAV__
<main class="wrap">
  <h1>One product. Three ways in.</h1>
  <p class="lead">Desktop is the operator desk. API is how Grok, Codex, Claude, and apps call the same host. Studio turns captures into product demos. Same sign-in. Same engines.</p>

  <div class="grid">
    <div class="card">
      <h3>Desktop</h3>
      <p>Cursor-style agent desk on this PC. Codex, Grok, Claude, NEXUS, Fusion Sense, multi-session chat. Open via POCKET Desktop app or the browser desk.</p>
      <a class="go" href="/desk">Open Desktop →</a>
      <div class="meta">Also: Desktop shortcut · python -m pocket desktop</div>
    </div>
    <div class="card">
      <h3>API</h3>
      <p>Keys (<code style="color:var(--accent)">sk_pocket_…</code>), curl snippets, catalog. For Grok Build, Codex automation, and customer integrations.</p>
      <a class="go" href="/developers">Open API →</a>
      <div class="meta">Auth: operator password or API key</div>
    </div>
    <div class="card">
      <h3>Studio</h3>
      <p>Product phone/web remakes and work screencasts from host recordings — not a separate product brain.</p>
      <a class="go" href="/studio">Open Studio →</a>
      <div class="meta">Uses the same host runtime</div>
    </div>
  </div>

  <div class="note">
    <strong>Sign-in</strong> uses the host credentials in
    <code>%USERPROFILE%\.pocket\ACCESS.txt</code>
    — usually <strong>Username: pocket</strong> and the <strong>Password:</strong> line in that file.
    Phone/public URL uses the same password. API customers use <strong>Bearer sk_pocket_…</strong> after you create a key on the API page.
  </div>

  <p class="foot">POCKET · ItsNotAI Labs · Overview · Desktop · API · Studio stay linked in the top bar on every surface.</p>
</main>
</body>
</html>
"""


def hub_html() -> str:
    return (
        PRODUCT_HUB_HTML.replace("__SHELL_CSS__", SHELL_CSS)
        .replace("__SHELL_NAV__", shell_nav(active="overview"))
    )
