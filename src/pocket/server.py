"""POCKET Multi-Agent Platform â€” agents, tokenomics, deploys, Grok research pulls."""

from __future__ import annotations

import argparse
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path  # used for PUBLIC_URL + docs
from typing import Optional
from urllib.parse import parse_qs, urlparse  # studio file query

from pocket.app_ui import HTML
from pocket.studio_ui import STUDIO_HTML
from pocket.auth import (
    auth_summary,
    clear_auth_failures,
    is_authorized,
    is_rate_limited,
    path_is_public,
    record_auth_failure,
    security_headers,
)
from pocket.rbac import (
    allow_admin_action,
    allow_agent,
    allow_mode,
    can_access_owned,
    is_admin,
    principal as rbac_principal,
)
from pocket.executor import available_engines
from pocket.grok_bridge import can_codex_start_grok, write_pull_package
from pocket.jobs import WORK_DIR, create_job, get, list_jobs
from pocket.live import connect_all_down, connect_service, lan_ip, probe_all
from pocket.platform import (
    deploy_log_tail,
    deploy_process,
    deploy_static,
    list_deploys,
    platform_manifest,
    stop_deploy,
    workspace_tools,
)
from pocket.sessions import (
    add_user_message,
    bind_job,
    complete_message,
    create_session,
    delete_session,
    get as get_session,
    get_usage,
    list_sessions,
    rename,
)
from pocket.terminals import (
    create_terminal,
    get_terminal,
    list_terminals,
    send_terminal,
    stop_terminal,
)
from pocket.tokenomics import (
    cost_analysis_20_users,
    estimate_session_cost,
    mint,
    snapshot as token_snapshot,
)
from pocket.organism import snapshot as organism_snapshot
from pocket.uploads import upload_file
from pocket.worker import ensure_pool, process_one

PORT = int(os.environ.get("POCKET_PORT", "8787"))
DOCS_ROOT = Path(__file__).resolve().parents[2] / "docs" / "research"
_worker_started = False
_worker_lock = threading.Lock()

DOC_MAP = {
    "tokenomics": "POCKET_TOKENOMICS_PAPER.md",
    "usage-cost": "POCKET_USAGE_COST_PAPER.md",
    "platform": "POCKET_PLATFORM_PAPER.md",
    "ship": "POCKET_SHIP_STORY_PAPER.md",
    "guppy": "POCKET_GUPPY_DESK_AGENT_PAPER.md",
    "desktop-autonomy": "POCKET_DESKTOP_AUTONOMY_PAPER.md",
    "engines-beyond-code": "POCKET_ENGINES_BEYOND_CODE_PAPER.md",
    "lab-claims": "POCKET_LAB_SYSTEMS_CLAIMS_PAPER.md",
    "host-copilot": "POCKET_HOST_COPILOT_VISION_PAPER.md",
    "browser": "POCKET_BROWSER_MODE_PAPER.md",
    "live-desk": "POCKET_LIVE_DESK_PRODUCTION.md",
    "agents-named": "POCKET_NAMED_AGENTS_REGISTER.md",
    "latin": "POCKET_LATIN_WORKERS.md",
    "alive": "POCKET_ALIVE_AUTONOMOUS.md",
    "skills": "POCKET_SKILLS_AND_DAEMON.md",
    "orchestrator": "POCKET_ORCHESTRATOR_VISION.md",
    "real-skills": "POCKET_REAL_SKILLS.md",
    "vision-workers": "POCKET_VISION_WORKERS_FIRST_CLASS.md",
    "pixel": "POCKET_PIXEL_TRANSLATOR.md",
    "api-first": "POCKET_PLATFORM_API_FIRST.md",
}
DOCS_ROOT_MAIN = Path(__file__).resolve().parents[2] / "docs"


def _organism_status(n: int, eng: dict, pub, tok: dict) -> dict:
    try:
        from pocket.platform import list_deploys

        deploys = len([d for d in list_deploys() if d.get("status") == "running"])
    except Exception:
        deploys = 0
    try:
        modes = [s.get("mode") or "?" for s in list_sessions(20)]
        jobs_running = sum(1 for s in list_sessions(30) if s.get("status") == "running")
    except Exception:
        modes, jobs_running = [], 0
    return organism_snapshot(
        worker_alive=_worker_started,
        sessions=n,
        jobs_running=jobs_running,
        deploys=deploys,
        pock=int(tok.get("balance") or 0),
        public=bool(pub and str(pub).startswith("http")),
        codex=bool(eng.get("codex")),
        grok=bool(eng.get("grok")),
        modes=modes,
    )


def _openapi_spec() -> dict:
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "POCKET AI API",
            "version": __import__("pocket").__version__,
            "description": "POCKET platform API — orchestrator, vision, workers, campaigns. Auth: Basic or Bearer sk_pocket_…",
        },
        "paths": {
            "/v1/ai": {"get": {"summary": "Product catalog"}},
            "/v1/ai/agents": {"get": {"summary": "List headless agents"}},
            "/v1/ai/agents/{id}/run": {"post": {"summary": "Run headless agent"}},
            "/v1/ai/chat": {"post": {"summary": "Chat completion (OpenAI-shaped)"}},
            "/v1/ai/jobs": {"post": {"summary": "Async job"}},
            "/v1/ai/jobs/{id}": {"get": {"summary": "Poll job"}},
            "/v1/ai/keys": {"post": {"summary": "Create API key (admin)"}},
            "/v1/ai/usage": {"get": {"summary": "Key usage"}},
            "/v1/ready": {"get": {"summary": "Production A-Z readiness"}},
            "/health": {"get": {"summary": "Liveness"}},
        },
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "sk_pocket_"}
            }
        },
        "security": [{"bearerAuth": []}],
    }


def ensure_embedded_worker() -> None:
    global _worker_started
    with _worker_lock:
        if _worker_started:
            return
        _worker_started = True
        ensure_pool()
        try:
            from pocket.autonomy import ensure_runner

            ensure_runner()
        except Exception:
            pass
        try:
            from pocket.worker_daemon import ensure_daemon

            ensure_daemon()
        except Exception:
            pass
        try:
            from pocket.live_vision import ensure_vision

            ensure_vision()
        except Exception:
            pass

        def _loop():
            while True:
                try:
                    if not process_one():
                        time.sleep(0.5)
                    else:
                        time.sleep(0.1)
                except Exception as e:
                    print(f"[embedded worker] {e}", flush=True)
                    time.sleep(1.5)

        for i in range(2):
            t = threading.Thread(target=_loop, name=f"pocket-dispatch-{i}", daemon=True)
            t.start()
        print("[POCKET] multi-agent worker pool started", flush=True)


def status() -> dict:
    eng = available_engines()
    pub = (os.environ.get("POCKET_PUBLIC_URL") or "").strip() or None
    # Named tunnel env file written by Setup-Cloudflare-Named-Tunnel.ps1
    if not pub:
        root_pocket = Path(__file__).resolve().parents[2] / ".pocket"
        envf = root_pocket / "cloudflare-named.env"
        if envf.exists():
            try:
                for line in envf.read_text(encoding="utf-8").splitlines():
                    if line.startswith("POCKET_PUBLIC_URL="):
                        pub = line.split("=", 1)[1].strip() or None
                        break
            except Exception:
                pass
    if not pub:
        puf = Path(__file__).resolve().parents[2] / "PUBLIC_URL.txt"
        if puf.exists():
            try:
                import re as _re

                m = _re.search(r"https://[^\s]+", puf.read_text(encoding="utf-8"))
                if m:
                    pub = m.group(0).rstrip("/")
            except Exception:
                pass
    ip = lan_ip()
    n = len(list_sessions(100))
    tok = token_snapshot()
    return {
        "ok": True,
        "product": "POCKET",
        "full": "POCKET Multi-Agent Platform",
        "version": __import__("pocket").__version__,
        "schema": "pocket.status.v1",
        "tagline": "POCKET — host co-pilot platform API (workers · vision · campaigns)",
        "lan_ip": ip,
        "port": PORT,
        "url": f"http://{ip}:{PORT}/",
        "local": f"http://127.0.0.1:{PORT}/",
        "public_url": pub,
        "access": auth_summary(),
        "engine": {
            **eng,
            "worker_alive": _worker_started,
            "workspace": str(WORK_DIR),
            "grok_cli": can_codex_start_grok(),
        },
        "usage": get_usage(),
        "tokenomics": {
            "balance": tok.get("balance"),
            "unit": tok.get("unit"),
            "lifetime_burned": tok.get("lifetime_burned"),
        },
        "organism": _organism_status(n, eng, pub, tok),
        "sessions_open": n,
        "session_cost_estimate": estimate_session_cost(n),
        "cost_20_users": cost_analysis_20_users(),
        "public_url_file": str(Path(__file__).resolve().parents[2] / "PUBLIC_URL.txt"),
        "how": {
            "desktop": f"http://127.0.0.1:{PORT}/",
            "phone_same_wifi": f"http://{ip}:{PORT}/",
            "phone_anywhere": pub or "Run Setup-Cloudflare-Named-Tunnel.ps1 with your CF domain",
            "docs": list(DOC_MAP.keys()),
            "value": "Grok coding agent (real) + plan handoff + Codex + local deploy + POCK.",
            "modes": {
                "grok": "Real Grok coding agent (grok --single)",
                "handoff": "Plan handoff â€” research package, no agent exec",
                "codex": "Codex coding agent",
            },
            "tunnel": {
                "setup": r"scripts\Setup-Cloudflare-Named-Tunnel.ps1 -Hostname pocket.YOURDOMAIN.com",
                "run": r"scripts\Start-Cloudflare-Named.ps1",
                "guide": "docs/CLOUDFLARE_NAMED_TUNNEL.md",
            },
        },
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _sec_headers(self):
        for k, v in security_headers():
            self.send_header(k, v)

    def _client_ip(self) -> str:
        from pocket.auth import _client_ip

        return _client_ip(self.headers, getattr(self, "client_address", None))

    def _reject_unauthorized(self, reason: str = "authentication required"):
        raw = json.dumps({"error": reason, "auth": True}).encode("utf-8")
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="POCKET", charset="UTF-8"')
        self.send_header("Content-Type", "application/json")
        self._sec_headers()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _reject_limited(self):
        raw = json.dumps({"error": "too many failed logins — wait 5 minutes"}).encode("utf-8")
        self.send_response(429)
        self.send_header("Content-Type", "application/json")
        self._sec_headers()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _require_auth(self, path: str = "/") -> bool:
        if path_is_public(path):
            return True
        ip = self._client_ip()
        if is_rate_limited(ip):
            self._reject_limited()
            return False
        if is_authorized(self.headers):
            clear_auth_failures(ip)
            return True
        record_auth_failure(ip)
        self._reject_unauthorized()
        return False

    def _cors_origin(self) -> str:
        """Allow local desk + Electron; never wildcard for credentialed APIs."""
        origin = (self.headers.get("Origin") or "").strip()
        if origin in (
            "http://127.0.0.1:8787",
            "http://localhost:8787",
            "null",  # some Electron contexts
        ) or origin.startswith("http://127.0.0.1:") or origin.startswith("http://localhost:"):
            return origin if origin and origin != "null" else "http://127.0.0.1:8787"
        # Same-origin browser requests often omit Origin
        return "http://127.0.0.1:8787"

    def _json(self, code: int, obj: dict):
        raw = json.dumps(obj, default=str).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", self._cors_origin())
        self.send_header("Access-Control-Allow-Credentials", "true")
        self._sec_headers()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _text(self, code: int, text: str, ctype: str = "text/markdown; charset=utf-8"):
        raw = text.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self._sec_headers()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _html(self, html: str):
        raw = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._sec_headers()
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        if n <= 0:
            return {}
        # Cap body size 2MB
        if n > 2_000_000:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode("utf-8"))
        except Exception:
            return {}

    def do_OPTIONS(self):
        # Preflight for local desk / Electron
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self._cors_origin())
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-Pocket-Access, X-Pocket-Token, X-API-Key, X-Pocket-Device",
        )
        self._sec_headers()
        self.end_headers()

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        q = parse_qs(u.query)
        if not self._require_auth(path):
            return

        if path in ("/", "/tour", "/product", "/present", "/landing", "/home"):
            # Full marketing landing for Desktop + API + Studio bundle
            try:
                from pocket.marketing_landing import landing_html

                return self._html(landing_html())
            except Exception:
                from pocket.product_tour import tour_html

                return self._html(tour_html())
        # Get / install guide (shareable marketing URL)
        if path in ("/get", "/get/", "/start", "/install", "/install/"):
            from pocket.marketing_landing import get_app_html

            return self._html(get_app_html())
        # --- Desktop Electron package downloads (public) ---
        if path in ("/download", "/download/"):
            from pocket.desktop_releases import download_page_html

            return self._html(download_page_html())
        if path in ("/v1/desktop/releases", "/v1/releases/desktop"):
            from pocket.desktop_releases import catalog

            return self._json(200, catalog())
        if path in ("/download/desktop", "/download/windows", "/download/desktop/windows"):
            from pocket.desktop_releases import preferred_artifact, list_artifacts

            qkind = (q.get("kind") or ["portable"])[0]
            qarch = (q.get("arch") or [None])[0]
            art = preferred_artifact(arch=qarch, kind=qkind)
            if not art:
                arts = list_artifacts()
                return self._json(
                    404,
                    {
                        "error": "no desktop package built yet",
                        "hint": "On host: cd desktop-electron && npm run dist && python -m pocket desktop-pack",
                        "page": "/download",
                        "artifacts": arts,
                    },
                )
            # Redirect to file URL so browsers get Content-Disposition attachment
            loc = art.get("url") or f"/download/files/{art.get('name')}"
            self.send_response(302)
            self.send_header("Location", loc)
            self._sec_headers()
            self.end_headers()
            return
        if path.startswith("/download/files/"):
            from pocket.desktop_releases import resolve_file
            import mimetypes

            name = path.split("/download/files/", 1)[-1]
            fp = resolve_file(name)
            if not fp:
                return self._json(404, {"error": "release file not found", "name": name})
            data = fp.read_bytes()
            ctype = mimetypes.guess_type(fp.name)[0] or "application/octet-stream"
            if fp.suffix.lower() == ".exe":
                ctype = "application/vnd.microsoft.portable-executable"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header(
                "Content-Disposition",
                f'attachment; filename="{fp.name}"',
            )
            self.send_header("Cache-Control", "public, max-age=300")
            self._sec_headers()
            self.end_headers()
            self.wfile.write(data)
            return
        if path in ("/desk", "/app", "/desktop", "/chat"):
            return self._html(HTML)
        if path in ("/developers", "/api", "/docs/api"):
            from pocket.developers_ui import developers_html

            return self._html(developers_html())
        if path in ("/studio", "/studio/"):
            return self._html(STUDIO_HTML)
        if path in ("/health", "/v1/health"):
            from pocket import __version__ as _pv

            heart = {"ok": True, "interval_ms": 873}
            try:
                from pathlib import Path
                import time as _t

                hf = Path.home() / ".pocket" / "runtime_heartbeat.json"
                if hf.exists():
                    heart = json.loads(hf.read_text(encoding="utf-8"))
                    heart["stale"] = (_t.time() - float(heart.get("ts") or 0)) > 3.0
            except Exception:
                pass
            return self._json(
                200,
                {
                    "ok": True,
                    "service": "pocket",
                    "version": _pv,
                    "heart": "beating",
                    "heartbeat": heart,
                    "brain": "online",
                    "auth": "required-for-app",
                    "product": True,
                    "api": "platform",
                    "surfaces": ["landing", "desk", "api", "studio", "mesie"],
                    "default_codex_cwd": "E:\\PARALLAX-Exchange-Clearinghouse",
                },
            )
        if path in ("/v1/runtime/heartbeat", "/v1/heartbeat"):
            from pathlib import Path
            import time as _t

            hf = Path.home() / ".pocket" / "runtime_heartbeat.json"
            if not hf.exists():
                return self._json(200, {"ok": True, "worker": False, "note": "start: python -m pocket runtime-worker"})
            try:
                data = json.loads(hf.read_text(encoding="utf-8"))
                data["age_ms"] = int((_t.time() - float(data.get("ts") or 0)) * 1000)
                data["alive"] = data["age_ms"] < 2500
                return self._json(200, data)
            except Exception as e:
                return self._json(200, {"ok": False, "error": str(e)[:120]})
        if path == "/v1/ready":
            from pocket.production import checklist

            return self._json(200, checklist())
        if path == "/v1/legal":
            legal = DOCS_ROOT_MAIN / "LEGAL.md"
            if legal.exists():
                return self._text(200, legal.read_text(encoding="utf-8"))
            return self._json(404, {"ok": False, "error": "LEGAL.md missing"})
        if path == "/v1/ai/openapi":
            return self._json(200, _openapi_spec())
        if path == "/v1/product":
            from pocket.product import doctor

            return self._json(200, doctor())
        if path == "/v1/doctor":
            from pocket.product import doctor

            return self._json(200, doctor())
        if path == "/v1/organism":
            st = status()
            return self._json(200, st.get("organism") or organism_snapshot())
        if path == "/v1/cost/20-users":
            return self._json(200, cost_analysis_20_users())
        if path == "/v1/terminals":
            return self._json(200, {"terminals": list_terminals()})
        if path.startswith("/v1/terminals/"):
            tid = path.split("/v1/terminals/", 1)[-1].split("/")[0]
            if path.endswith("/log") or path.endswith(tid):
                t = get_terminal(tid)
                if not t:
                    return self._json(404, {"error": "terminal not found"})
                return self._json(200, t)
        if path.startswith("/v1/deploys/") and path.endswith("/log"):
            did = path.split("/v1/deploys/", 1)[-1].replace("/log", "")
            return self._json(200, deploy_log_tail(did))
        if path == "/v1/status":
            try:
                return self._json(200, status())
            except Exception as e:
                return self._json(
                    200,
                    {
                        "ok": True,
                        "product": "POCKET",
                        "version": __import__("pocket").__version__,
                        "degraded": True,
                        "error": str(e)[:300],
                        "local": f"http://127.0.0.1:{PORT}/desk",
                        "engine": {"worker_alive": _worker_started},
                    },
                )
        if path == "/v1/auth/me":
            u = rbac_principal(self.headers)
            if (u.get("role") or "none") == "none":
                return self._json(401, {"ok": False, "error": "auth required"})
            return self._json(200, {"ok": True, "user": u})
        if path == "/v1/live":
            return self._json(200, probe_all())
        if path == "/v1/usage":
            return self._json(200, get_usage())
        if path == "/v1/tokenomics":
            return self._json(200, token_snapshot())
        if path == "/v1/platform":
            return self._json(200, platform_manifest())
        if path == "/v1/deploys":
            return self._json(200, {"deploys": list_deploys()})
        if path == "/v1/workspace/tools":
            ws = (q.get("workspace") or ["workspace"])[0]
            return self._json(200, workspace_tools(ws))
        if path == "/v1/grok/can-start":
            return self._json(200, can_codex_start_grok())
        if path == "/v1/safety":
            from pocket.safety import policy_summary

            return self._json(200, policy_summary())
        if path == "/v1/device":
            from pocket.device import device_from_request

            # Public-ish after auth: report how server sees this client
            return self._json(200, {"ok": True, "device": device_from_request(self.headers, {})})

        # --- Sellable AI API (headless agents product) ---
        if path in ("/v1/ai", "/v1/ai/pricing"):
            from pocket.sell_api import product_manifest

            return self._json(200, product_manifest())
        if path == "/v1/ai/agents":
            from pocket.agents import list_agents

            agents = list_agents(sellable_only=True)
            return self._json(200, {"ok": True, "agents": agents, "count": len(agents)})
        if path.startswith("/v1/ai/agents/"):
            from pocket.agents import get_agent

            aid = path.split("/v1/ai/agents/", 1)[-1].split("/")[0]
            a = get_agent(aid)
            if not a:
                return self._json(404, {"ok": False, "error": "agent not found"})
            return self._json(200, {"ok": True, "agent": a})
        if path == "/v1/ai/keys":
            from pocket.sell_api import keys_list

            p = rbac_principal(self.headers)
            if is_admin(p):
                return self._json(200, keys_list())
            return self._json(200, keys_list(owner=p.get("user") or ""))
        if path == "/v1/ai/usage":
            from pocket.api_keys import extract_bearer, usage_for, verify_key

            p = rbac_principal(self.headers)
            raw = extract_bearer(self.headers)
            kid = ""
            if raw:
                rec = verify_key(raw)
                kid = (rec or {}).get("id") or ""
            if kid:
                return self._json(200, usage_for(kid))
            if is_admin(p):
                return self._json(200, usage_for(""))
            return self._json(200, usage_for(owner=p.get("user") or ""))
        if path.startswith("/v1/ai/jobs/"):
            jid = path.split("/v1/ai/jobs/", 1)[-1].split("/")[0]
            job = get(jid)
            if not job:
                return self._json(404, {"ok": False, "error": "job not found"})
            p = rbac_principal(self.headers)
            if job.get("owner") and not can_access_owned(p, job.get("owner") or ""):
                return self._json(403, {"ok": False, "error": "not your job"})
            return self._json(
                200,
                {
                    "ok": True,
                    "id": job.get("id"),
                    "status": job.get("status"),
                    "agent_id": job.get("agent_id"),
                    "mode": job.get("mode"),
                    "engine": job.get("engine"),
                    "result": job.get("result") or "",
                    "error": job.get("error") or "",
                    "created_at": job.get("created_at"),
                    "finished_at": job.get("finished_at"),
                },
            )

        if path == "/v1/desktop/apps":
            from pocket.desktop import list_apps

            return self._json(200, {"apps": list_apps()})
        if path == "/v1/guppy":
            from pocket.guppy import identity
            from pocket.autonomy import list_schedules, runner_status

            return self._json(
                200,
                {
                    **identity(),
                    "schedules": list_schedules(),
                    "runner": runner_status(),
                },
            )
        if path == "/v1/autonomy/schedules":
            from pocket.autonomy import list_schedules, runner_status

            return self._json(200, {"schedules": list_schedules(), "runner": runner_status()})
        if path == "/v1/live/events":
            from pocket.live_events import list_events, snapshot

            after = int((q.get("after") or ["0"])[0] or 0)
            return self._json(
                200,
                {
                    "events": list_events(after_seq=after, limit=100),
                    "snapshot": snapshot(),
                },
            )
        if path in ("/v1/live/vision", "/v1/vision"):
            from pocket.live_vision import latest_frame, ensure_vision

            ensure_vision()
            include = (q.get("image") or ["1"])[0] != "0"
            return self._json(200, latest_frame(include_image=include))
        if path in ("/v1/vision/observe", "/v1/observe"):
            from pocket.vision_core import observe

            return self._json(200, observe(with_ui_map=True, with_ocr=True, with_understand=True))
        if path == "/v1/vision/ui_map":
            from pocket.vision_core import build_ui_map

            return self._json(200, build_ui_map())
        if path in ("/v1/vision/understand", "/v1/pixel/understand", "/v1/pixel/translate"):
            from pocket.pixel_translator import understand

            return self._json(200, understand(include_image=False))
        if path in ("/v1/pixel/text", "/v1/vision/ocr"):
            from pocket.pixel_translator import translate_to_text_only

            return self._json(200, translate_to_text_only())
        if path in ("/v1/vision/page", "/v1/page/render", "/v1/vision/full"):
            from pocket.page_renderer import render_full_page

            q = parse_qs(urlparse(self.path).query)
            max_ui = int((q.get("max_ui") or ["800"])[0] or 800)
            grid = int((q.get("grid") or ["5"])[0] or 5)
            want_img = (q.get("image") or ["0"])[0] == "1"
            return self._json(
                200,
                render_full_page(
                    max_ui=max_ui,
                    include_ocr=True,
                    include_visual=True,
                    include_image=want_img,
                    visual_grid=grid,
                ),
            )
        if path in ("/v1/vision/stream", "/v1/vision/stream/latest"):
            from pocket.page_renderer import stream_latest, stream_status

            q = parse_qs(urlparse(self.path).query)
            after = int((q.get("after") or ["0"])[0] or 0)
            return self._json(200, {**stream_latest(after_seq=after), "status": stream_status()})
        if path == "/v1/vision/stream/status":
            from pocket.page_renderer import stream_status

            return self._json(200, stream_status())
        if path == "/v1/vision/find":
            from pocket.page_renderer import find_symbols

            q = parse_qs(urlparse(self.path).query)
            query = (q.get("q") or q.get("query") or [""])[0]
            return self._json(200, {"ok": True, "query": query, "hits": find_symbols(query)})
        if path == "/v1/api":
            # Single catalog for Grok / Codex / Claude / any HTTP client
            from pocket import __version__ as _pv
            from pocket.skill_suite import skill_count

            return self._json(
                200,
                {
                    "product": "POCKET",
                    "version": _pv,
                    "auth": "Basic  OR  X-Pocket-Access  OR  Bearer sk_pocket_…",
                    "skill_count": skill_count(),
                    "groups": {
                        "vision": {
                            "understand": "GET /v1/vision/understand",
                            "page_full": "GET /v1/vision/page?max_ui=800&grid=5",
                            "page_post": "POST /v1/vision/page  body:{max_ui,ocr,visual,image,grid}",
                            "pixel_text": "GET /v1/pixel/text",
                            "live_frame": "GET /v1/live/vision",
                            "stream": "GET /v1/vision/stream?after=0",
                            "stream_start": "POST /v1/vision/stream/start  body:{interval,max_ui}",
                            "stream_stop": "POST /v1/vision/stream/stop",
                            "stream_status": "GET /v1/vision/stream/status",
                            "find": "GET /v1/vision/find?q=Save  or  POST /v1/vision/find",
                            "click": "POST /v1/vision/click",
                            "observe": "GET /v1/vision/observe",
                            "ui_map": "GET /v1/vision/ui_map",
                        },
                        "agents": {
                            "chat": "POST /v1/orchestrator/chat",
                            "plan": "POST /v1/orchestrator/plan",
                            "skill": "POST /v1/skills/run  body:{skill:page_render|stream_start|…}",
                            "spawn": "POST /v1/workers/spawn",
                            "campaign": "POST /v1/campaigns/run",
                            "bridge_open": "POST /v1/bridge/open",
                        },
                        "studio": {
                            "ui": "GET /studio",
                            "status": "GET /v1/studio",
                            "auto": "POST /v1/studio/auto",
                            "render": "POST /v1/studio/render  presets: rotato_phone|x_screencast|macbook_web|clean_demo",
                            "batch": "POST /v1/studio/batch",
                        },
                        "imagine": {
                            "status": "GET /v1/imagine",
                            "compose": "POST /v1/imagine/compose  body:{mode:rotato_phone|macbook_web|clean}",
                            "product_dir": "OneDrive/imagine-studio (Creative Muse seed)",
                        },
                        "fusion": {
                            "remake": "POST /v1/fusion/remake  → RFE-v1 FULL_SYNTHESIS",
                            "page": "GET /v1/vision/page",
                        },
                        "rfe": {
                            "status": "GET /v1/rfe",
                            "synthesize": "POST /v1/rfe/synthesize  body:{instruction_set,refresh,max_ui}",
                            "verify": "POST /v1/rfe/verify",
                            "research": "Documents/POCKET_Research/RFE_Recursive_Fusion_Engine/",
                            "gold_standard": "wf1 ≥600 symbols → HTML + 3D + GLSL + signed packet",
                        },
                        "record": {
                            "start": "POST /v1/record/start",
                            "stop": "POST /v1/record/stop",
                            "status": "GET /v1/record/status",
                        },
                    },
                    "skills_vision": [
                        "page_render",
                        "full_page",
                        "page_symbols",
                        "stream_start",
                        "stream_stop",
                        "stream_latest",
                        "understand",
                        "pixel_text",
                        "see_screen",
                        "fusion_remake",
                        "imagine_compose",
                    ],
                    "skills_studio": [
                        "studio_auto",
                        "studio_render",
                        "viral_pack",
                    ],
                    "vcomp": {
                        "open": "POST /v1/vcomp/open",
                        "status": "GET /v1/vcomp",
                        "sense": "POST /v1/vcomp/sense",
                        "act": "POST /v1/vcomp/act",
                        "shell": "POST /v1/vcomp/shell",
                        "term": "POST /v1/vcomp/term",
                    },
                    "missions": {
                        "start": "POST /v1/missions/start  body:{goal,queue,max_hours}",
                        "list": "GET /v1/missions",
                        "enqueue": "POST /v1/missions/enqueue",
                        "stop": "POST /v1/missions/stop",
                    },
                    "workflows": {
                        "catalog": "GET /v1/workflows",
                        "run": "POST /v1/workflows/run  body:{id:wf1|wf2|wf3|wf4|wf5|all}",
                    },
                    "note": "Fusion-Sense is the baseline (wf1). RFE remake, vcomp/missions, product-native phone/web, NEXUS, tour at /tour. Not a CLI paste.",
                },
            )
        if path == "/v1/workers/dynamic":
            from pocket.dynamic_worker import list_active

            return self._json(200, {"workers": list_active()})
        if path == "/v1/subagents":
            from pocket.subagents_panel import list_subagents
            from pocket.mesh_disk import status as mesh_status

            r = list_subagents()
            r["mesh"] = mesh_status()
            return self._json(200, r)
        if path == "/v1/subagents/running":
            from pocket.subagents_panel import list_running

            return self._json(200, list_running())
        if path == "/v1/mesh":
            from pocket.mesh_disk import status as mesh_status
            from pocket.agent_hook import ensure_mesh_hook

            ensure_mesh_hook()
            return self._json(200, mesh_status())
        if path in ("/v1/protocols/mesh", "/v1/protocol/mesh", "/v1/hooks/mesh"):
            from pocket.agent_hook import protocol_report

            return self._json(200, protocol_report())
        if path.startswith("/v1/mesh/inbox/"):
            from pocket.mesh_disk import read_inbox

            aid = path.split("/v1/mesh/inbox/", 1)[-1].split("/")[0]
            return self._json(200, read_inbox(aid))
        if path == "/v1/mesh/channel":
            from pocket.mesh_disk import channel_tail
            from urllib.parse import parse_qs as _pqs

            q = _pqs(urlparse(self.path).query)
            ch = (q.get("name") or ["freq-0"])[0]
            return self._json(200, channel_tail(ch))
        if path == "/v1/bridge":
            from pocket.realtime_bridge import list_bridges

            return self._json(200, {"bridges": list_bridges()})
        if path.startswith("/v1/bridge/"):
            from pocket.realtime_bridge import get_bridge

            bid = path.split("/v1/bridge/", 1)[-1].split("/")[0]
            br = get_bridge(bid)
            if not br:
                return self._json(404, {"error": "bridge not found"})
            return self._json(
                200,
                {
                    "id": br.get("id"),
                    "status": br.get("status"),
                    "steps": br.get("steps"),
                    "recording_path": br.get("recording_path"),
                    "last_observe_summary": br.get("last_observe_summary"),
                },
            )
        if path == "/v1/long_workers":
            # Alias import — never shadow module-level status() in this method
            from pocket.long_workers import status as long_workers_status

            return self._json(200, long_workers_status())
        if path == "/v1/purchase/playbooks":
            from pocket.purchase_playbooks import list_playbooks

            return self._json(200, {"playbooks": list_playbooks(), "auto_pay": False})
        if path == "/v1/campaigns":
            from pocket.campaigns import list_campaigns

            return self._json(200, {"campaigns": list_campaigns()})
        if path in ("/v1/imagine", "/v1/imagine/status"):
            from pocket.imagine_studio import status as imagine_status

            return self._json(200, imagine_status())
        if path in ("/v1/rfe", "/v1/rfe/status"):
            from pocket.rfe_kernel import status as rfe_status

            return self._json(200, rfe_status())
        if path in ("/v1/product/presentation", "/v1/presentation", "/v1/tour"):
            from pocket.product_tour import presentation

            return self._json(200, presentation())
        if path in ("/v1/product/channels", "/v1/channels"):
            from pocket.product_channels import channels

            return self._json(200, channels())
        if path in ("/v1/product/home", "/v1/home"):
            from pocket.product_channels import user_home_brief

            return self._json(200, user_home_brief())
        if path in ("/v1/sense/intent", "/v1/fusion/intent"):
            from pocket.sanity import intent_buffer

            return self._json(200, intent_buffer())
        if path in ("/v1/nexus", "/v1/nexus/status"):
            from pocket.nexus_bridge import nexus_available, list_capabilities

            info = nexus_available()
            caps = list_capabilities() if info.get("ok") else info
            return self._json(200, {"ok": True, "nexus": info, "capabilities": caps})
        if path in ("/v1/mesie", "/v1/mesie/status"):
            from pocket.mesie_bridge import status as mesie_status

            return self._json(200, mesie_status())
        if path in ("/v1/auro", "/v1/auro14b", "/v1/ro14b"):
            from pocket.auro14b_bridge import status as auro_status

            return self._json(200, auro_status())
        if path in ("/v1/stack", "/v1/lab/stack"):
            # Unified POCKET + NEXUS + MESIE + mesh status for left rail
            from pocket.nexus_bridge import nexus_available
            from pocket.mesie_bridge import mesie_available
            from pocket.mesh_disk import status as mesh_status
            from pocket.agent_hook import hook_status

            return self._json(
                200,
                {
                    "ok": True,
                    "pocket": {"product": "POCKET", "version": "2.0.1-alpha"},
                    "nexus": nexus_available(),
                    "mesie": mesie_available(),
                    "mesh": mesh_status(),
                    "hook": hook_status(),
                    "swarm": {
                        "novasbrain": r"E:\NOVASBRAIN",
                        "studio": r"E:\NOVASBRAIN\swarm_studio",
                        "phase": 31,
                        "note": "Stratum + gas ledger verified in NOVASBRAIN; not auto-mined from desk",
                    },
                },
            )
        if path in ("/v1/vcomp", "/v1/virtual-computer", "/v1/computer"):
            from pocket.virtual_computer import status as vcomp_status

            return self._json(200, vcomp_status())
        if path in ("/v1/missions", "/v1/mission"):
            from pocket.mission_loop import list_missions

            return self._json(200, {"missions": list_missions()})
        if path.startswith("/v1/missions/"):
            from pocket.mission_loop import get_mission

            mid = path.split("/v1/missions/", 1)[-1].split("/")[0]
            m = get_mission(mid)
            if not m:
                return self._json(404, {"error": "mission not found"})
            return self._json(200, m)
        if path in ("/v1/workflows", "/v1/workflows/catalog"):
            from pocket.workflows_alpha import catalog

            return self._json(200, {"workflows": catalog(), "alpha": True})
        if path == "/v1/studio":
            from pocket.video_studio import studio_status, list_recordings, list_exports, list_presets

            st = studio_status()
            st["recordings_list"] = list_recordings(30)
            st["exports_list"] = list_exports(30)
            st["presets"] = list_presets()
            return self._json(200, st)
        if path == "/v1/studio/recordings":
            from pocket.video_studio import list_recordings

            return self._json(200, {"recordings": list_recordings()})
        if path == "/v1/studio/exports":
            from pocket.video_studio import list_exports

            return self._json(200, {"exports": list_exports()})
        if path == "/v1/studio/presets":
            from pocket.video_studio import list_presets

            return self._json(200, {"presets": list_presets()})
        if path == "/v1/studio/file":
            from pocket.video_studio import EXPORTS

            q = parse_qs(urlparse(self.path).query)
            name = (q.get("name") or [""])[0]
            # only basename under exports
            safe = Path(name).name
            fp = EXPORTS / safe
            if not fp.is_file() or not str(fp.resolve()).startswith(str(EXPORTS.resolve())):
                return self._json(404, {"error": "file not found"})
            data = fp.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Content-Disposition", f'inline; filename="{safe}"')
            self._sec_headers()
            self.end_headers()
            self.wfile.write(data)
            return
        if path.startswith("/v1/campaigns/"):
            from pocket.campaigns import get_campaign

            cid = path.split("/v1/campaigns/", 1)[-1].split("/")[0]
            c = get_campaign(cid)
            if not c:
                return self._json(404, {"error": "campaign not found"})
            return self._json(200, c)
        if path == "/v1/platform/capabilities":
            from pocket.skill_suite import skill_count
            from pocket import __version__ as _pv

            return self._json(
                200,
                {
                    "version": _pv,
                    "skill_count": skill_count(),
                    "entrypoints": {
                        "chat": "POST /v1/orchestrator/chat",
                        "skill": "POST /v1/skills/run",
                        "spawn_worker": "POST /v1/workers/spawn",
                        "campaign": "POST /v1/campaigns/run",
                        "observe": "GET /v1/vision/observe",
                        "vision": "GET /v1/live/vision",
                        "plan": "POST /v1/orchestrator/plan",
                        "bridge_open": "POST /v1/bridge/open",
                        "bridge_observe": "POST /v1/bridge/{id}/observe",
                        "bridge_act": "POST /v1/bridge/{id}/act",
                        "bridge_close": "POST /v1/bridge/{id}/close",
                        "pixel_understand": "GET /v1/vision/understand",
                        "pixel_text": "GET /v1/pixel/text",
                        "studio": "GET /studio  ·  POST /v1/studio/auto",
                    },
                    "value_vs_chat_only": [
                        "Real desktop control with signed-in browser",
                        "Vision + UI map click-by-name",
                        "Pixel translator: semantic + OCR + pure visual fusion",
                        "Dynamic workers with memory brains",
                        "Screen record commercial demos",
                        "Multi-repo research campaigns",
                        "Same API for local host and remote VM",
                    ],
                    "clients": ["pocket-ui", "codex", "grok-build", "phone", "sk_pocket_ api keys"],
                },
            )
        if path == "/v1/host":
            from pocket.host_backend import get_host

            h = get_host()
            return self._json(200, {"backend": h.kind(), "note": "Local now; set ~/.pocket/host.json for remote VM"})
        if path == "/v1/cli/tools":
            from pocket.cli_tools import inventory

            return self._json(200, inventory())
        if path in ("/v1/workers", "/v1/alpha"):
            from pocket.alpha_workers import list_workers
            from pocket.skill_suite import all_skills, skill_count
            from pocket.worker_daemon import live_state, ensure_daemon
            from pocket.orchestrator import get_orchestrator

            ensure_daemon()
            return self._json(
                200,
                {
                    "workers": list_workers(),
                    "skills": all_skills(),
                    "skill_count": skill_count(),
                    "live": live_state(),
                    "orchestrator": get_orchestrator().catalog()["architecture"],
                    "guppy": "kept",
                },
            )
        if path in ("/v1/skills", "/v1/skill_suite"):
            from pocket.skill_suite import all_skills, skill_count

            return self._json(200, {"ok": True, "count": skill_count(), "skills": all_skills()})
        if path == "/v1/orchestrator":
            from pocket.orchestrator import get_orchestrator

            return self._json(200, get_orchestrator().catalog())
        if path in ("/v1/ai-workspace", "/v1/ai_workspace", "/v1/workspace/ai"):
            from pocket.ai_workspace import get_workspace_view, refresh_index

            # use module-level urlparse/parse_qs — local import shadows and crashes do_GET
            qs = {k: (v[0] if v else "") for k, v in parse_qs(urlparse(self.path).query).items()}
            ws = qs.get("workspace") or "parallax"
            sid = qs.get("session_id") or qs.get("session") or ""
            if qs.get("refresh") in ("1", "true", "yes"):
                refresh_index(ws, qs.get("cwd") or "")
            return self._json(200, get_workspace_view(ws, session_id=sid))
        if path in ("/v1/capabilities", "/v1/capability-map", "/v1/caps"):
            from pocket.capability_map import build_capability_map, capability_markdown

            cmap = build_capability_map()
            return self._json(200, {"ok": True, "map": cmap, "markdown": capability_markdown(cmap)})
        if path == "/v1/offload" and self.command == "GET":
            from pocket.offload_queue import list_tasks

            qs = {k: (v[0] if v else "") for k, v in parse_qs(urlparse(self.path).query).items()}
            return self._json(
                200,
                {
                    "ok": True,
                    "tasks": list_tasks(status=qs.get("status") or "", limit=int(qs.get("limit") or 40)),
                },
            )
        if path.startswith("/v1/offload/") and self.command == "GET":
            from pocket.offload_queue import get_task

            tid = path.split("/v1/offload/", 1)[-1].strip("/")
            t = get_task(tid)
            if not t:
                return self._json(404, {"ok": False, "error": "ticket not found"})
            return self._json(200, {"ok": True, "task": t})
        if path in ("/v1/task-market", "/v1/market"):
            from pocket.task_market import list_open

            return self._json(200, {"ok": True, "open": list_open()})
        if path in ("/v1/agent-bus", "/v1/mesh/bus"):
            from pocket.mesh_disk import channel_tail, decrypt_body

            qs = {k: (v[0] if v else "") for k, v in parse_qs(urlparse(self.path).query).items()}
            ch = qs.get("channel") or "freq-coding"
            tail = channel_tail(ch, limit=int(qs.get("limit") or 20))
            msgs = []
            for m in tail.get("messages") or []:
                body = m.get("body") or ""
                if m.get("body_cipher"):
                    try:
                        body = decrypt_body(m["body_cipher"])
                    except Exception:
                        pass
                msgs.append(
                    {
                        "from": m.get("from"),
                        "to": m.get("to"),
                        "kind": m.get("kind"),
                        "body": (body or "")[:400],
                        "hmac": (m.get("hmac_sha256") or "")[:16],
                        "at": m.get("at"),
                    }
                )
            return self._json(200, {"ok": True, "channel": ch, "messages": msgs})
        if path == "/v1/workers/live":
            from pocket.worker_daemon import live_state, ensure_daemon

            ensure_daemon()
            return self._json(200, live_state())
        if path == "/v1/github/repos":
            from pocket.repos import list_github_repos, gh_available

            return self._json(200, {**list_github_repos(5), "auth": gh_available()})
        if path == "/v1/nexus/status":
            from pocket.nexus_bridge import nexus_available

            return self._json(200, nexus_available())
        if path.startswith("/v1/docs/"):
            key = path.split("/v1/docs/", 1)[-1]
            fname = DOC_MAP.get(key)
            if not fname:
                return self._json(404, {"error": "doc not found", "keys": list(DOC_MAP)})
            fp = DOCS_ROOT / fname
            if not fp.exists():
                return self._json(404, {"error": "file missing", "path": str(fp)})
            return self._text(200, fp.read_text(encoding="utf-8"))
        if path == "/v1/sessions":
            p = rbac_principal(self.headers)
            lim = int((q.get("limit") or ["40"])[0])
            return self._json(
                200,
                {
                    "sessions": list_sessions(
                        lim, owner=p.get("user") or "", admin=is_admin(p)
                    )
                },
            )
        if path.startswith("/v1/sessions/"):
            sid = path.split("/v1/sessions/", 1)[-1].split("/")[0]
            sess = get_session(sid)
            if not sess:
                return self._json(404, {"error": "session not found"})
            p = rbac_principal(self.headers)
            if not can_access_owned(p, sess.get("owner") or "pocket"):
                return self._json(403, {"ok": False, "error": "not your session"})
            if sess.get("terminal_id"):
                t = get_terminal(sess["terminal_id"])
                if t:
                    sess = {**sess, "terminal": t}
            return self._json(200, sess)
        if path == "/v1/jobs":
            p = rbac_principal(self.headers)
            jobs = list_jobs(int((q.get("limit") or ["20"])[0]))
            if not is_admin(p):
                own = (p.get("user") or "").lower()
                jobs = [j for j in jobs if (j.get("owner") or "").lower() in ("", own)]
            return self._json(200, {"jobs": jobs})
        if path.startswith("/v1/jobs/"):
            jid = path.split("/v1/jobs/", 1)[-1].split("/")[0]
            job = get(jid)
            if not job:
                return self._json(404, {"error": "job not found"})
            p = rbac_principal(self.headers)
            if job.get("owner") and not can_access_owned(p, job.get("owner") or ""):
                return self._json(403, {"ok": False, "error": "not your job"})
            return self._json(200, job)
        return self._json(404, {"error": "not found"})

    def do_DELETE(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if not self._require_auth(path):
            return
        if path.startswith("/v1/sessions/"):
            sid = path.split("/v1/sessions/", 1)[-1].split("/")[0]
            sess = get_session(sid)
            p = rbac_principal(self.headers)
            if sess and not can_access_owned(p, sess.get("owner") or "pocket"):
                return self._json(403, {"ok": False, "error": "not your session"})
            try:
                from pocket.jobs import cancel_session_jobs

                cancel_session_jobs(sid, reason="session ended")
            except Exception:
                pass
            ok = delete_session(sid)
            return self._json(200 if ok else 404, {"ok": ok, "id": sid})
        if path.startswith("/v1/deploys/"):
            p = rbac_principal(self.headers)
            ok, msg = allow_admin_action(p, "deploy")
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            did = path.split("/v1/deploys/", 1)[-1]
            return self._json(200, stop_deploy(did))
        if path.startswith("/v1/terminals/"):
            p = rbac_principal(self.headers)
            ok, msg = allow_mode(p, "term")
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            tid = path.split("/v1/terminals/", 1)[-1]
            return self._json(200, stop_terminal(tid))
        if path.startswith("/v1/ai/keys/"):
            from pocket.api_keys import list_keys
            from pocket.sell_api import keys_revoke

            kid = path.split("/v1/ai/keys/", 1)[-1].split("/")[0]
            p = rbac_principal(self.headers)
            if not is_admin(p):
                mine = {k.get("id") for k in list_keys(owner=p.get("user") or "")}
                if kid not in mine:
                    return self._json(403, {"ok": False, "error": "not your key"})
            return self._json(200, keys_revoke(kid))
        return self._json(404, {"error": "not found"})

    def _api_key_id(self) -> str:
        try:
            from pocket.api_keys import extract_bearer, verify_key

            raw = extract_bearer(self.headers)
            if not raw:
                return ""
            rec = verify_key(raw)
            return (rec or {}).get("id") or ""
        except Exception:
            return ""

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        if not self._require_auth(path):
            return
        body = self._body()
        ensure_embedded_worker()

        # --- Sellable AI API ---
        if path in ("/v1/ai/chat", "/v1/ai/complete", "/v1/ai/jobs") or (
            path.startswith("/v1/ai/agents/") and path.endswith("/run")
        ):
            from pocket.ratelimit import hit

            p = rbac_principal(self.headers)
            rk = self._api_key_id() or p.get("user") or self._client_ip()
            heavy = path.endswith("/run") or path == "/v1/ai/jobs"
            ok_rl, reason = hit("api", rk, kind="api_heavy" if heavy else "api")
            if not ok_rl:
                return self._json(429, {"ok": False, "error": reason})

        if path == "/v1/ai/chat":
            from pocket.sell_api import chat_complete

            p = rbac_principal(self.headers)
            agent = body.get("agent") or body.get("model") or "planner"
            if agent == "auto":
                agent = "planner"
            ok, msg = allow_agent(p, agent)
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            return self._json(
                200,
                chat_complete(
                    body.get("messages") or [],
                    agent=agent,
                    workspace=body.get("workspace") or "workspace",
                    api_key_id=self._api_key_id(),
                    sync=body.get("sync", True) is not False,
                ),
            )
        if path == "/v1/ai/route":
            from pocket.agents import route_task

            return self._json(200, route_task(body.get("task") or body.get("text") or body.get("prompt") or ""))
        if path == "/v1/ai/jobs":
            from pocket.sell_api import run_agent_api

            p = rbac_principal(self.headers)
            aid = body.get("agent") or body.get("agent_id") or "planner"
            ok, msg = allow_agent(p, aid)
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            task = body.get("task") or body.get("text") or body.get("prompt") or ""
            if not task:
                return self._json(400, {"ok": False, "error": "task required"})
            return self._json(
                200,
                run_agent_api(
                    aid,
                    task,
                    workspace=body.get("workspace") or "workspace",
                    sync=False,
                    api_key_id=self._api_key_id(),
                    extra=body.get("extra") or "",
                ),
            )
        if path.startswith("/v1/ai/agents/") and path.endswith("/run"):
            from pocket.sell_api import run_agent_api

            p = rbac_principal(self.headers)
            aid = path.split("/v1/ai/agents/", 1)[-1].replace("/run", "").strip("/")
            ok, msg = allow_agent(p, aid)
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            task = body.get("task") or body.get("text") or body.get("prompt") or ""
            if not task:
                return self._json(400, {"ok": False, "error": "task required"})
            return self._json(
                200,
                run_agent_api(
                    aid,
                    task,
                    workspace=body.get("workspace") or "workspace",
                    sync=body.get("sync", True) is not False,
                    api_key_id=self._api_key_id(),
                    extra=body.get("extra") or "",
                ),
            )
        if path == "/v1/ai/keys":
            from pocket.sell_api import create_api_key_admin

            p = rbac_principal(self.headers)
            # Members may create a key for themselves only; admin can set owner
            owner = body.get("owner") or p.get("user") or "pocket"
            if not is_admin(p):
                owner = p.get("user") or "pocket"
                # members limited to starter tier by default
                if (body.get("tier") or "pro") not in ("starter", "pro"):
                    body = {**body, "tier": "starter"}
            return self._json(200, create_api_key_admin({**body, "owner": owner}, owner=owner))
        if path == "/v1/ai/complete":
            from pocket.sell_api import chat_complete

            p = rbac_principal(self.headers)
            agent = body.get("agent") or "planner"
            ok, msg = allow_agent(p, agent)
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            prompt = body.get("prompt") or body.get("text") or body.get("task") or ""
            return self._json(
                200,
                chat_complete(
                    [{"role": "user", "content": prompt}],
                    agent=agent,
                    workspace=body.get("workspace") or "workspace",
                    api_key_id=self._api_key_id(),
                ),
            )

        if path == "/v1/auth/login":
            from pocket.ratelimit import hit
            from pocket.users import issue_token, verify

            ip = self._client_ip()
            ok_rl, reason = hit("login", ip, kind="login")
            if not ok_rl:
                return self._json(429, {"ok": False, "error": reason})
            u = verify(body.get("user") or body.get("username") or "", body.get("password") or "")
            if not u:
                record_auth_failure(ip)
                return self._json(401, {"ok": False, "error": "bad credentials"})
            clear_auth_failures(ip)
            tok = issue_token(u["user"])
            return self._json(200, {"ok": True, "token": tok, "user": u})

        # Desktop-only: trusted local auto-login (127.0.0.1 only). Real apps embed runtime.
        if path in ("/v1/auth/desktop", "/v1/auth/local"):
            ip = self._client_ip()
            if ip not in ("127.0.0.1", "::1", "localhost"):
                return self._json(403, {"ok": False, "error": "desktop login only on localhost"})
            try:
                from pocket.auth import expected_user
                from pocket.users import issue_token, verify, list_users

                user = (expected_user() or "pocket").lower()
                # Prefer existing user record; else mint token for operator name
                users = {u["user"]: u for u in list_users()}
                if user in users:
                    rec = users[user]
                    u = {"user": user, "role": rec.get("role") or "admin", "display": rec.get("display") or "Operator"}
                else:
                    u = {"user": user, "role": "admin", "display": "Operator"}
                tok = issue_token(u["user"])
                return self._json(200, {"ok": True, "token": tok, "user": u, "desktop": True})
            except Exception as e:
                return self._json(500, {"ok": False, "error": str(e)[:200]})

        if path == "/v1/auth/register":
            from pocket.ratelimit import hit
            from pocket.users import issue_token, register

            ip = self._client_ip()
            ok_rl, reason = hit("register", ip, kind="register")
            if not ok_rl:
                return self._json(429, {"ok": False, "error": reason})
            res = register(
                body.get("user") or body.get("username") or "",
                body.get("password") or "",
                body.get("invite") or "",
                display=body.get("display") or "",
                accepted_terms=bool(body.get("accepted_terms") or body.get("terms")),
            )
            if not res.get("ok"):
                record_auth_failure(ip)
                return self._json(400, res)
            tok = issue_token(res["user"])
            return self._json(200, {**res, "token": tok})

        if path == "/v1/auth/logout":
            from pocket.users import revoke_token

            tok = (
                self.headers.get("X-Pocket-Token")
                or self.headers.get("x-pocket-token")
                or body.get("token")
                or ""
            )
            return self._json(200, {"ok": revoke_token(tok.strip())})

        if path == "/v1/auth/password":
            from pocket.users import change_password

            p = rbac_principal(self.headers)
            if (p.get("role") or "none") == "none":
                return self._json(401, {"ok": False, "error": "auth required"})
            user = body.get("user") or p.get("user") or ""
            if not is_admin(p) and user != p.get("user"):
                return self._json(403, {"ok": False, "error": "can only change own password"})
            return self._json(
                200,
                change_password(user, body.get("old_password") or "", body.get("new_password") or ""),
            )

        if path == "/v1/auth/invite/rotate":
            from pocket.users import rotate_invite

            p = rbac_principal(self.headers)
            ok, msg = allow_admin_action(p, "rotate_invite")
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            return self._json(200, rotate_invite())

        if path == "/v1/auth/me":
            u = rbac_principal(self.headers)
            if (u.get("role") or "none") == "none":
                return self._json(401, {"ok": False})
            return self._json(200, {"ok": True, "user": u})

        if path == "/v1/live/connect":
            sid = (body.get("service") or body.get("id") or "").strip()
            if sid == "all" or not sid:
                return self._json(200, connect_all_down())
            return self._json(200, connect_service(sid))

        if path == "/v1/files/upload":
            return self._json(
                200,
                upload_file(
                    workspace=body.get("workspace") or "workspace",
                    filename=body.get("filename") or "",
                    content_base64=body.get("content_base64") or "",
                    size=int(body.get("size") or 0),
                ),
            )

        if path == "/v1/desktop/open":
            from pocket.desktop import open_app

            return self._json(
                200,
                open_app(
                    body.get("app") or body.get("id") or "",
                    args=body.get("args") or "",
                    path=body.get("path") or "",
                ),
            )

        if path == "/v1/web/fetch":
            from pocket.web_research import fetch_url

            return self._json(200, fetch_url(body.get("url") or ""))

        if path == "/v1/web/search":
            from pocket.web_research import search_web

            return self._json(200, search_web(body.get("query") or body.get("q") or ""))

        if path == "/v1/nexus/run":
            from pocket.nexus_bridge import run_worker

            return self._json(
                200,
                run_worker(
                    body.get("worker") or "Bridge",
                    body.get("task") or "list_servers",
                    body.get("params") or {},
                ),
            )

        if path == "/v1/nexus/list":
            from pocket.nexus_bridge import list_capabilities

            return self._json(200, list_capabilities())

        if path == "/v1/tokenomics/mint":
            p = rbac_principal(self.headers)
            ok, msg = allow_admin_action(p, "mint")
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            return self._json(200, mint(int(body.get("amount") or 0), reason=body.get("reason") or "topup"))

        if path == "/v1/deploy":
            p = rbac_principal(self.headers)
            ok, msg = allow_admin_action(p, "deploy")
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            kind = (body.get("kind") or "static").lower()
            ws = body.get("workspace") or "workspace"
            title = body.get("title") or ""
            port = int(body.get("port") or 0)
            if kind == "static":
                return self._json(
                    200,
                    deploy_static(
                        workspace=ws,
                        subpath=body.get("subpath") or "",
                        title=title,
                        port=port,
                    ),
                )
            if kind in ("npm", "python", "py", "process"):
                return self._json(
                    200,
                    deploy_process(
                        kind="python" if kind in ("python", "py") else ("npm" if kind == "npm" else "npm"),
                        workspace=ws,
                        command=body.get("command") or "",
                        title=title,
                        port=port,
                        cwd_subpath=body.get("subpath") or "",
                    ),
                )
            return self._json(400, {"error": "kind must be static|npm|python", "hint": "optional command= override"})

        if path == "/v1/terminals":
            p = rbac_principal(self.headers)
            ok, msg = allow_mode(p, "term")
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            return self._json(
                200,
                {
                    "ok": True,
                    **create_terminal(
                        kind=body.get("kind") or "powershell",
                        workspace=body.get("workspace") or "workspace",
                        session_id=body.get("session_id") or "",
                    ),
                },
            )
        if path.startswith("/v1/terminals/") and path.endswith("/send"):
            tid = path.split("/v1/terminals/", 1)[-1].replace("/send", "")
            return self._json(200, send_terminal(tid, body.get("text") or body.get("command") or ""))

        if path == "/v1/grok/pull":
            # Force a full research plan package (no wait for session)
            path_md, pkg = write_pull_package(
                body.get("prompt") or body.get("text") or "status pull",
                body.get("cwd") or str(WORK_DIR),
            )
            return self._json(200, {"ok": True, "path": str(path_md), "package": pkg})

        if path == "/v1/sessions":
            from pocket.device import device_from_request

            p = rbac_principal(self.headers)
            mode = body.get("mode") or "codex"
            ok, msg = allow_mode(p, mode)
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            dev = device_from_request(self.headers, body)
            sess = create_session(
                mode=mode,
                title=body.get("title") or "",
                workspace=body.get("workspace") or "workspace",
                cwd=body.get("cwd") or "",
                client_device=dev,
                owner=p.get("user") or "pocket",
            )
            return self._json(200, {"ok": True, **sess})

        if path.startswith("/v1/sessions/") and path.endswith("/rename"):
            sid = path.split("/v1/sessions/", 1)[-1].replace("/rename", "")
            sess = rename(sid, body.get("title") or "")
            if not sess:
                return self._json(404, {"error": "not found"})
            return self._json(200, sess)

        if path.startswith("/v1/sessions/") and path.endswith("/messages"):
            from pocket.device import agent_context_line, device_from_request, should_inject_context
            from pocket.sessions import save as save_sess

            sid = path.split("/v1/sessions/", 1)[-1].replace("/messages", "")
            sess = get_session(sid)
            if not sess:
                return self._json(404, {"error": "session not found"})
            p = rbac_principal(self.headers)
            if not can_access_owned(p, sess.get("owner") or "pocket"):
                return self._json(403, {"ok": False, "error": "not your session"})
            ok, msg = allow_mode(p, sess.get("mode") or "codex")
            if not ok:
                return self._json(403, {"ok": False, "error": msg})
            text = (body.get("text") or body.get("prompt") or "").strip()
            if not text:
                return self._json(400, {"error": "text required"})
            dev = device_from_request(self.headers, body)
            sess["client_device"] = dev
            save_sess(sess)
            msg = add_user_message(sid, text)
            if not msg:
                return self._json(500, {"error": "message failed"})

            # Interactive terminal: send to long-lived PTY-like shell
            if (sess.get("mode") or "") == "term":
                tid = sess.get("terminal_id")
                if not tid:
                    term = create_terminal(
                        kind=body.get("term_kind") or "powershell",
                        workspace=sess.get("workspace") or "workspace",
                        session_id=sid,
                    )
                    tid = term.get("id")
                    sess["terminal_id"] = tid
                    save_sess(sess)
                res = send_terminal(tid, text)
                complete_message(
                    sid,
                    msg["id"],
                    result=res.get("log_tail") or res.get("error") or "",
                    error="" if res.get("ok") else (res.get("error") or "term error"),
                    engine="term",
                    status="done" if res.get("ok") else "failed",
                )
                return self._json(
                    200,
                    {
                        "ok": True,
                        "session_id": sid,
                        "message": msg,
                        "terminal": res,
                        "client_device": dev,
                        "poll_session": f"/v1/sessions/{sid}",
                    },
                )

            mode = sess.get("mode") or "codex"
            # One tab = one active agent turn: stop prior Grok/Codex/etc. so the new
            # prompt takes the floor instead of leaving the first job running forever.
            superseded: list = []
            interrupt = body.get("interrupt")
            if interrupt is None:
                interrupt = True  # default: new message ends prior work on this session
            if interrupt and mode not in ("term",):
                try:
                    from pocket.jobs import cancel_session_jobs

                    superseded = cancel_session_jobs(
                        sid,
                        reason="superseded by new message — reorganize on latest prompt",
                    )
                except Exception:
                    superseded = []
            job_prompt = text
            if should_inject_context(mode):
                job_prompt = (agent_context_line(dev) + text)[:20000]
            job = create_job(
                job_prompt,
                name=body.get("name") or "desk",
                mode=mode,
                workspace=body.get("workspace") or sess.get("workspace") or "workspace",
                cwd=body.get("cwd") or sess.get("cwd") or "",
                session_id=sid,
                message_id=msg["id"],
                client_device=dev,
                owner=sess.get("owner") or p.get("user") or "",
            )
            bind_job(sid, msg["id"], job["id"])
            return self._json(
                200,
                {
                    "ok": True,
                    "session_id": sid,
                    "message": msg,
                    "job": job,
                    "superseded_jobs": superseded,
                    "client_device": dev,
                    "poll_session": f"/v1/sessions/{sid}",
                },
            )

        if path in ("/v1/jobs", "/v1/code"):
            try:
                job = create_job(
                    body.get("prompt") or body.get("text") or "",
                    name=body.get("name") or "desk",
                    mode=body.get("mode") or "codex",
                    cwd=body.get("cwd") or "",
                    workspace=body.get("workspace") or "",
                )
            except ValueError as e:
                return self._json(400, {"error": str(e)})
            return self._json(200, {"ok": True, **job})

        # Stop a single job (Grok/Codex/etc.) — kills process tree when pid known
        if path.startswith("/v1/jobs/") and path.endswith("/cancel"):
            from pocket.jobs import cancel_job, get as get_job

            jid = path.split("/v1/jobs/", 1)[-1].replace("/cancel", "").strip("/")
            job = get_job(jid)
            if not job:
                return self._json(404, {"ok": False, "error": "job not found"})
            p = rbac_principal(self.headers)
            if job.get("owner") and not can_access_owned(p, job.get("owner") or ""):
                return self._json(403, {"ok": False, "error": "not your job"})
            out = cancel_job(jid, reason=(body.get("reason") or "cancelled by user"))
            return self._json(200, {"ok": True, "job": out})

        # Stop all work on a session tab without deleting the transcript
        if path.startswith("/v1/sessions/") and path.endswith("/stop"):
            from pocket.jobs import cancel_session_jobs

            sid = path.split("/v1/sessions/", 1)[-1].replace("/stop", "").strip("/")
            sess = get_session(sid)
            if not sess:
                return self._json(404, {"ok": False, "error": "session not found"})
            p = rbac_principal(self.headers)
            if not can_access_owned(p, sess.get("owner") or "pocket"):
                return self._json(403, {"ok": False, "error": "not your session"})
            cancelled = cancel_session_jobs(
                sid, reason=(body.get("reason") or "stopped by user")
            )
            try:
                from pocket.sessions import save as save_sess

                sess["status"] = "idle"
                save_sess(sess)
            except Exception:
                pass
            return self._json(
                200,
                {"ok": True, "session_id": sid, "cancelled_jobs": cancelled, "status": "idle"},
            )

        if path == "/v1/autonomy/schedules":
            from pocket.autonomy import create_schedule, ensure_runner

            prompt = (body.get("prompt") or body.get("text") or body.get("task") or "").strip()
            if not prompt:
                return self._json(400, {"error": "prompt required"})
            ensure_runner()
            rec = create_schedule(
                prompt=prompt,
                interval=body.get("interval") or "daily",
                title=body.get("title") or "",
                owner=(rbac_principal(self.headers).get("user") or "pocket"),
            )
            return self._json(200, {"ok": True, **rec})

        if path == "/v1/guppy/run":
            from pocket.guppy import run_guppy

            result, error, engine = run_guppy(
                body.get("prompt") or body.get("text") or "help",
                cwd=body.get("cwd") or "",
            )
            return self._json(
                200,
                {"ok": not bool(error), "result": result, "error": error, "engine": engine},
            )

        if path == "/v1/browser/run":
            from pocket.browser_mode import run_browser_job

            result, error, engine = run_browser_job(
                body.get("prompt") or body.get("text") or "help",
                cwd=body.get("cwd") or "",
                job={"browser_engine": body.get("engine") or body.get("browser_engine") or "auto"},
            )
            return self._json(
                200,
                {"ok": not bool(error), "result": result, "error": error, "engine": engine},
            )

        # Easy desk API — phone/desktop same shape as talking to an agent
        if path in ("/v1/desk", "/v1/desk/run", "/v1/archon"):
            from pocket.alpha_workers import run_alpha_job, run_worker, list_workers
            from pocket.worker_daemon import ensure_daemon, enqueue

            ensure_daemon()
            action = (body.get("action") or body.get("worker") or body.get("agent") or "").strip()
            prompt = (body.get("prompt") or body.get("text") or body.get("task") or "").strip()
            job_name = (body.get("job") or body.get("skill") or "orchestrate").strip()
            if body.get("async"):
                cmd = enqueue(action or "ARCHON", job_name if job_name != "orchestrate" else "grand_demo", prompt=prompt)
                return self._json(200, {"ok": True, "queued": cmd, "api": "desk-async"})
            if (body.get("list") or prompt.lower() in ("workers", "list", "help names")) and not action:
                return self._json(200, {"ok": True, "workers": list_workers()})
            if prompt.lower() in (
                "grand demo", "demo", "full demo", "interface demo", "ui demo",
                "focused demo",
            ) or job_name in ("grand_demo", "demo", "interface_demo", "focused_demo"):
                from pocket.skills_real import run_focused_demo

                r = run_focused_demo()
                return self._json(200, {"ok": r.get("ok"), "result": r, "engine": "archon", "api": "desk"})
            if action:
                result, error, engine = run_worker(
                    action,
                    job_name,
                    prompt=prompt,
                    params=body.get("params") or {},
                    cwd=body.get("cwd") or "",
                )
            else:
                result, error, engine = run_alpha_job(prompt or "help", cwd=body.get("cwd") or "")
            return self._json(
                200,
                {
                    "ok": not bool(error),
                    "result": result,
                    "error": error,
                    "engine": engine,
                    "api": "desk",
                    "hint": "POST {\"prompt\":\"interface demo\"} or {\"skill\":\"copilot_chat_send\",\"prompt\":\"…\"}",
                },
            )

        if path in ("/v1/live/vision", "/v1/vision"):
            from pocket.live_vision import latest_frame, ensure_vision

            ensure_vision()
            return self._json(200, latest_frame(include_image=True))
        if path in ("/v1/skills/run", "/v1/skill"):
            from pocket.orchestrator import get_orchestrator
            from pocket.worker_daemon import ensure_daemon

            ensure_daemon()
            skill = body.get("skill") or body.get("id") or body.get("job") or ""
            r = get_orchestrator().execute(
                skill,
                prompt=body.get("prompt") or body.get("text") or "",
                params=body.get("params") or {},
            )
            return self._json(200, {"ok": r.get("ok"), "result": r, "engine": "orchestrator"})

        if path in ("/v1/orchestrator/chat", "/v1/chat/workflow", "/v1/desk/chat"):
            from pocket.orchestrator import get_orchestrator
            from pocket.worker_daemon import ensure_daemon

            ensure_daemon()
            text = body.get("prompt") or body.get("text") or body.get("message") or ""
            r = get_orchestrator().chat(text, record=bool(body.get("record")))
            return self._json(200, {"ok": r.get("ok"), "result": r, "engine": "orchestrator"})

        if path in ("/v1/orchestrator/plan", "/v1/plan/run"):
            from pocket.orchestrator import get_orchestrator

            steps = body.get("steps") or body.get("plan") or []
            r = get_orchestrator().execute_plan(steps, record=bool(body.get("record")))
            return self._json(200, {"ok": r.get("ok"), "result": r})

        if path in ("/v1/woa", "/v1/wrapped-orch", "/v1/orchestrator/woa"):
            from pocket.wrapped_orchestrator import run_wrapped

            text = body.get("prompt") or body.get("text") or body.get("goal") or body.get("message") or ""
            remote = body.get("remote")
            if remote is None:
                remote = True
            r = run_wrapped(
                text,
                remote=bool(remote),
                cwd=body.get("cwd") or "",
                job_id=body.get("job_id") or "",
            )
            return self._json(200, {"ok": r.get("ok"), "result": r, "engine": "wrapped-orch"})

        if path in ("/v1/ai-workspace/refresh", "/v1/ai_workspace/refresh"):
            from pocket.ai_workspace import get_workspace_view, refresh_index, touch_from_job

            ws = body.get("workspace") or "parallax"
            refresh_index(ws, body.get("cwd") or "")
            if body.get("job"):
                touch_from_job(body["job"])
            return self._json(
                200,
                get_workspace_view(ws, session_id=body.get("session_id") or body.get("session") or ""),
            )

        if path in ("/v1/agent-bus/send", "/v1/mesh/send"):
            from pocket.mesh_disk import send_message

            r = send_message(
                body.get("from") or body.get("from_agent") or "USER",
                body.get("to") or body.get("to_agent") or "ARCHON",
                body.get("body") or body.get("text") or body.get("message") or "",
                channel=body.get("channel") or "freq-coding",
                kind=body.get("kind") or "note",
                encrypt=body.get("encrypt", True),
            )
            return self._json(200, r)

        if path in ("/v1/offload", "/v1/offload/enqueue", "/v1/embody"):
            from pocket.offload_queue import enqueue, ensure_worker

            ensure_worker()
            goal = body.get("goal") or body.get("prompt") or body.get("text") or body.get("message") or ""
            r = enqueue(
                goal,
                steps=body.get("steps"),
                agent=body.get("agent") or body.get("from") or "USER",
                session_id=body.get("session_id") or "",
                workspace=body.get("workspace") or "parallax",
                priority=int(body.get("priority") or 5),
                kind=body.get("kind") or "embodiment",
            )
            return self._json(200, r)

        if path in ("/v1/embodiment/run", "/v1/embody/run"):
            from pocket.embodiment import run_embodiment_plan

            r = run_embodiment_plan(
                body.get("goal") or body.get("prompt") or body.get("text") or "capability snapshot",
                steps=body.get("steps"),
                agent=body.get("agent") or "USER",
                workspace=body.get("workspace") or "parallax",
            )
            return self._json(200, {"ok": r.get("ok"), "result": r})

        if path in ("/v1/task-market/post", "/v1/market/post"):
            from pocket.task_market import post_task

            r = post_task(
                body.get("title") or body.get("goal") or "untitled",
                body=body.get("body") or body.get("text") or "",
                from_agent=body.get("from") or body.get("agent") or "GROK",
                tags=body.get("tags"),
            )
            return self._json(200, r)

        if path in ("/v1/task-market/claim", "/v1/market/claim"):
            from pocket.task_market import claim

            r = claim(body.get("id") or body.get("task_id") or "", agent=body.get("agent") or "CODEX")
            return self._json(200, r)

        if path == "/v1/workers/create":
            from pocket.orchestrator import get_orchestrator

            r = get_orchestrator().create_worker(
                body.get("name") or "CUSTOM",
                body.get("skills") or ["screenshot", "scroll_read"],
                role=body.get("role") or "custom",
            )
            return self._json(200, r)

        if path in ("/v1/workers/spawn", "/v1/dynamic/spawn"):
            from pocket.dynamic_worker import spawn_worker

            r = spawn_worker(
                body.get("goal") or body.get("prompt") or body.get("text") or "explore screen",
                name=body.get("name") or "AUTON",
                max_steps=int(body.get("max_steps") or 10),
                async_=bool(body.get("async")),
            )
            return self._json(200, r)

        if path == "/v1/vision/click":
            from pocket.vision_core import click_by_name

            return self._json(200, click_by_name(body.get("name") or body.get("text") or ""))

        if path == "/v1/vision/observe":
            from pocket.vision_core import observe

            return self._json(
                200,
                observe(
                    with_ui_map=bool(body.get("ui_map", True)),
                    with_ocr=bool(body.get("ocr", True)),
                    with_understand=bool(body.get("understand", True)),
                ),
            )
        if path in ("/v1/vision/understand", "/v1/pixel/understand", "/v1/pixel/translate"):
            from pocket.pixel_translator import understand

            return self._json(
                200,
                understand(
                    want_ocr=bool(body.get("ocr", True)),
                    want_semantic=bool(body.get("semantic", True)),
                    want_visual=bool(body.get("visual", True)),
                    include_image=bool(body.get("image", False)),
                ),
            )
        if path in ("/v1/pixel/text", "/v1/vision/ocr"):
            from pocket.pixel_translator import translate_to_text_only

            return self._json(200, translate_to_text_only())
        if path in ("/v1/vision/page", "/v1/page/render", "/v1/vision/full"):
            from pocket.page_renderer import render_full_page

            return self._json(
                200,
                render_full_page(
                    max_ui=int(body.get("max_ui") or 800),
                    include_ocr=bool(body.get("ocr", True)),
                    include_visual=bool(body.get("visual", True)),
                    include_image=bool(body.get("image", False)),
                    visual_grid=int(body.get("grid") or 5),
                ),
            )
        if path == "/v1/vision/stream/start":
            from pocket.page_renderer import stream_start

            return self._json(
                200,
                stream_start(
                    interval_sec=float(body.get("interval") or 1.5),
                    max_ui=int(body.get("max_ui") or 500),
                ),
            )
        if path == "/v1/vision/stream/stop":
            from pocket.page_renderer import stream_stop

            return self._json(200, stream_stop())
        if path == "/v1/vision/find":
            from pocket.page_renderer import find_symbols, render_full_page

            q = body.get("q") or body.get("query") or body.get("name") or ""
            if body.get("refresh"):
                render_full_page(max_ui=int(body.get("max_ui") or 600))
            return self._json(200, {"ok": True, "query": q, "hits": find_symbols(q)})

        if path == "/v1/long_workers/start":
            from pocket.long_workers import start_folder_watch, start_always_on_pulse, start_daily_research

            kind = (body.get("kind") or "always_on").lower()
            if kind == "folder_watch":
                return self._json(200, start_folder_watch())
            if kind == "daily_research":
                return self._json(200, start_daily_research(body.get("topic") or "AI agents"))
            return self._json(200, start_always_on_pulse(interval_sec=int(body.get("interval") or 120)))

        if path == "/v1/purchase/scaffold":
            from pocket.purchase_playbooks import run_playbook_scaffold

            return self._json(200, run_playbook_scaffold(body.get("id") or "generic_checkout_scaffold"))

        # Real-time synchronous bridge (outer agent drives each step after observe)
        if path == "/v1/bridge/open":
            from pocket.realtime_bridge import open_bridge

            return self._json(
                200,
                open_bridge(
                    title=body.get("title") or "live",
                    record=bool(body.get("record", True)),
                ),
            )
        if path.startswith("/v1/bridge/") and path.endswith("/observe"):
            from pocket.realtime_bridge import observe_bridge

            bid = path.split("/v1/bridge/", 1)[-1].replace("/observe", "").strip("/")
            return self._json(200, observe_bridge(bid))
        if path.startswith("/v1/bridge/") and path.endswith("/act"):
            from pocket.realtime_bridge import act_bridge

            bid = path.split("/v1/bridge/", 1)[-1].replace("/act", "").strip("/")
            action = body.get("action") or body.get("act") or ""
            kw = {k: v for k, v in body.items() if k not in ("action", "act")}
            return self._json(200, act_bridge(bid, action, **kw))
        if path.startswith("/v1/bridge/") and path.endswith("/close"):
            from pocket.realtime_bridge import close_bridge

            bid = path.split("/v1/bridge/", 1)[-1].replace("/close", "").strip("/")
            return self._json(200, close_bridge(bid))

        if path in ("/v1/campaigns", "/v1/campaigns/run"):
            from pocket.campaigns import run_research_campaign, list_campaigns

            if (body.get("list") or body.get("action") == "list") and not (
                body.get("topic") or body.get("prompt")
            ):
                return self._json(200, {"campaigns": list_campaigns()})
            topic = body.get("topic") or body.get("prompt") or body.get("text") or "POCKET host co-pilot"
            repos = body.get("repos")
            r = run_research_campaign(
                topic,
                repos=repos,
                record=bool(body.get("record", True)),
                commercial_polish=bool(body.get("commercial", True)),
            )
            return self._json(200, {"ok": True, "campaign": r, "api": "campaigns"})

        if path == "/v1/studio/render":
            from pocket.video_studio import render

            r = render(
                body.get("source") or body.get("path") or "",
                preset=body.get("preset") or "rotato_phone",
                title=body.get("title") or "POCKET",
                subtitle=body.get("subtitle") or "Host co-pilot demo",
                caption=body.get("caption") or "",
                cta=body.get("cta") or "Try POCKET",
                brand=body.get("brand") or "ItsNotAI Labs",
                max_seconds=float(body.get("max_seconds") or 0),
                start_seconds=float(body.get("start_seconds") or 0),
                speed=float(body.get("speed") or 1.0),
            )
            return self._json(200 if r.get("ok") else 400, r)
        if path in ("/v1/imagine/compose", "/v1/imagine/render"):
            from pocket.imagine_studio import compose

            r = compose(
                mode=body.get("mode") or body.get("preset") or "rotato_phone",
                image=body.get("image") or body.get("path") or "",
                title=body.get("title") or "POCKET",
                subtitle=body.get("subtitle") or "Host co-pilot",
                width=int(body.get("width") or 0),
                height=int(body.get("height") or 0),
            )
            return self._json(200 if r.get("ok") else 400, r)
        if path in ("/v1/fusion/remake", "/v1/vision/remake", "/v1/imagine/remake"):
            from pocket.fusion_remake import remake

            r = remake(
                refresh_page=bool(body.get("refresh", True)),
                max_ui=int(body.get("max_ui") or 500),
                styled=bool(body.get("styled", True)),
            )
            return self._json(200 if r.get("ok") else 400, r)
        if path in ("/v1/rfe/synthesize", "/v1/rfe/run", "/v1/fusion/synthesize"):
            from pocket.rfe_kernel import materialize

            r = materialize(
                instruction_set=body.get("instruction_set")
                or body.get("instruction")
                or body.get("mode")
                or "FULL_SYNTHESIS",
                refresh=bool(body.get("refresh", True)),
                max_ui=int(body.get("max_ui") or 500),
            )
            return self._json(200 if r.get("ok") else 400, r)
        if path == "/v1/rfe/verify":
            from pocket.rfe_kernel import verify_packet

            pkt = body.get("fusion_packet") or body
            return self._json(200, {"ok": True, "valid": verify_packet({"fusion_packet": pkt} if "uuid" in pkt else body)})
        if path == "/v1/studio/batch":
            from pocket.video_studio import render_batch

            r = render_batch(
                body.get("source") or "",
                presets=body.get("presets"),
                title=body.get("title") or "POCKET",
                subtitle=body.get("subtitle") or "Host co-pilot",
                caption=body.get("caption") or "",
                cta=body.get("cta") or "ItsNotAI Labs",
            )
            return self._json(200 if r.get("ok") else 400, r)
        if path == "/v1/studio/auto":
            from pocket.video_studio import auto_viral_pack

            r = auto_viral_pack(
                body.get("source") or "",
                title=body.get("title") or "POCKET",
                subtitle=body.get("subtitle") or "Real host co-pilot",
                caption=body.get("caption") or "Recorded live · Studio polish",
                cta=body.get("cta") or "ItsNotAI Labs",
            )
            return self._json(200 if r.get("ok") else 400, r)

        # --- Virtual computer (Caster-class) ---
        if path in ("/v1/vcomp/open", "/v1/computer/open"):
            from pocket.virtual_computer import open_computer

            return self._json(200, open_computer(label=body.get("label") or "main"))
        if path in ("/v1/vcomp/close", "/v1/computer/close"):
            from pocket.virtual_computer import close_computer

            return self._json(200, close_computer())
        if path in ("/v1/vcomp/sense", "/v1/computer/sense"):
            from pocket.virtual_computer import sense_computer

            return self._json(200, sense_computer(max_ui=int(body.get("max_ui") or 500)))
        if path in ("/v1/vcomp/act", "/v1/computer/act"):
            from pocket.virtual_computer import act

            action = body.get("action") or body.get("op") or "sense"
            params = {k: v for k, v in body.items() if k not in ("action", "op")}
            return self._json(200, act(action, **params))
        if path in ("/v1/vcomp/shell", "/v1/computer/shell"):
            from pocket.virtual_computer import shell

            return self._json(
                200,
                shell(body.get("command") or body.get("cmd") or "", timeout=int(body.get("timeout") or 60)),
            )
        if path in ("/v1/vcomp/term", "/v1/computer/term"):
            from pocket.virtual_computer import open_terminal
            from pocket.terminals import send_terminal

            if body.get("command") and body.get("id"):
                return self._json(200, send_terminal(body["id"], body["command"]))
            return self._json(200, open_terminal(kind=body.get("kind") or "powershell"))

        # --- Long missions ---
        if path in ("/v1/missions/start", "/v1/mission/start"):
            from pocket.mission_loop import start_mission

            return self._json(
                200,
                start_mission(
                    body.get("goal") or body.get("prompt") or "host work",
                    queue=body.get("queue") or body.get("steps"),
                    max_hours=float(body.get("max_hours") or 3.0),
                    step_pause_sec=float(body.get("pause") or 1.0),
                    name=body.get("name") or "MISSION",
                ),
            )
        if path in ("/v1/missions/enqueue", "/v1/mission/enqueue"):
            from pocket.mission_loop import enqueue

            return self._json(
                200,
                enqueue(body.get("id") or body.get("mission_id") or "", body.get("steps") or body.get("queue") or []),
            )
        if path in ("/v1/missions/stop", "/v1/mission/stop"):
            from pocket.mission_loop import stop_mission

            return self._json(200, stop_mission(body.get("id") or body.get("mission_id") or ""))

        # --- Alpha workflows ---
        if path in ("/v1/workflows/run", "/v1/workflow/run"):
            from pocket.workflows_alpha import run_workflow, run_all

            wid = body.get("id") or body.get("workflow") or ""
            if (body.get("all") or wid in ("all", "*")):
                return self._json(200, run_all())
            return self._json(200, run_workflow(wid, **{k: v for k, v in body.items() if k not in ("id", "workflow")}))
        if path in ("/v1/workflows/real", "/v1/workflows/real/run"):
            from pocket.workflows_real import run as run_real, run_all_real, catalog as real_catalog

            if body.get("all"):
                return self._json(200, run_all_real())
            wid = body.get("id") or body.get("workflow") or "real1"
            if body.get("list"):
                return self._json(200, {"workflows": real_catalog()})
            return self._json(200, run_real(wid, **{k: v for k, v in body.items() if k not in ("id", "workflow", "all", "list")}))
        if path in ("/v1/studio/product_phone", "/v1/studio/device_phone"):
            from pocket.device_remake import product_phone_from_recording, product_phone_from_image

            src = body.get("source") or body.get("path") or ""
            if src:
                r = product_phone_from_recording(
                    src,
                    title=body.get("title") or "POCKET",
                    caption=body.get("caption") or "Host co-pilot",
                    max_seconds=float(body.get("max_seconds") or 12),
                    n_frames=int(body.get("n_frames") or 10),
                )
            else:
                r = product_phone_from_image(
                    body.get("image"),
                    title=body.get("title") or "POCKET",
                    caption=body.get("caption") or "Host co-pilot",
                )
            return self._json(200 if r.get("ok") else 400, r)
        if path in ("/v1/studio/product_web", "/v1/studio/device_web"):
            from pocket.device_remake import product_web_from_image

            r = product_web_from_image(
                body.get("image") or body.get("path"),
                title=body.get("title") or "POCKET",
                brand=body.get("brand") or "pocket.local",
            )
            return self._json(200 if r.get("ok") else 400, r)
        if path in ("/v1/video/watch", "/v1/watch"):
            from pocket.video_watch import watch

            r = watch(
                body.get("source") or body.get("url") or body.get("path") or "",
                n_frames=int(body.get("n_frames") or 8),
                max_seconds=float(body.get("max_seconds") or 45),
                want_ocr=bool(body.get("ocr", True)),
            )
            return self._json(200 if r.get("ok") else 400, r)
        if path in ("/v1/nexus/run",):
            from pocket.nexus_bridge import run_worker

            r = run_worker(
                body.get("worker") or body.get("name") or "Bridge",
                body.get("tool") or body.get("action") or "list_servers",
                body.get("params") or body.get("args") or {},
            )
            return self._json(200 if r.get("ok", True) else 400, r)

        if path in ("/v1/subagents/dispatch", "/v1/agents/dispatch"):
            from pocket.agent_hook import ensure_mesh_hook
            from pocket.subagent_dispatch import dispatch

            ensure_mesh_hook()

            msg = body.get("message") or body.get("text") or body.get("prompt") or ""
            agents = body.get("agents") or body.get("names")
            if body.get("name") and not agents:
                agents = [body.get("name")]
            return self._json(
                200,
                dispatch(
                    msg,
                    from_agent=body.get("from") or "USER",
                    agents=agents,
                    channel=body.get("channel") or "freq-0",
                ),
            )
        if path in ("/v1/mesh/send",):
            from pocket.mesh_disk import send_message

            return self._json(
                200,
                send_message(
                    body.get("from") or "USER",
                    body.get("to") or "ARCHON",
                    body.get("body") or body.get("message") or "",
                    channel=body.get("channel") or "freq-0",
                    kind=body.get("kind") or "note",
                ),
            )
        if path in ("/v1/mesh/bootstrap", "/v1/headless/start", "/v1/hooks/mesh"):
            from pocket.agent_hook import ensure_mesh_hook

            h = ensure_mesh_hook(force=True, interval_sec=float(body.get("interval") or 120))
            return self._json(200, {"ok": True, "hook": h, "protocol": "MEDINA-SUBAGENT-MESH/1.0"})
        if path == "/v1/headless/stop":
            from pocket.subagent_dispatch import stop_headless_pack

            return self._json(200, stop_headless_pack())

        return self._json(404, {"error": "not found"})


def serve(host: str = "0.0.0.0", port: int = PORT) -> None:
    global PORT
    PORT = port
    try:
        from pocket.jobs import reclaim_orphans

        n = reclaim_orphans()
        if n:
            print(f"[POCKET] reclaimed {n} orphan running jobs", flush=True)
    except Exception as e:
        print(f"[POCKET] reclaim warn: {e}", flush=True)
    # Mesh / auro arm AFTER bind — never block first HTTP (login/desk)
    def _bg_hooks():
        try:
            from pocket.agent_hook import ensure_mesh_hook

            hook = ensure_mesh_hook()
            print(
                f"[POCKET] mesh hook armed={hook.get('armed')} "
                f"errors={len(hook.get('errors') or [])}",
                flush=True,
            )
        except Exception as e:
            print(f"[POCKET] mesh hook warn: {e}", flush=True)
        try:
            from pocket.auro14b_bridge import start_silent_training, status as auro_status

            print(
                f"[POCKET] auro14b {auro_status().get('ok')} "
                f"ckpt={auro_status().get('checkpoint_exists')}",
                flush=True,
            )
            start_silent_training()
        except Exception as e:
            print(f"[POCKET] auro14b warn: {e}", flush=True)

    ensure_embedded_worker()
    httpd = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=_bg_hooks, name="pocket-bg-hooks", daemon=True).start()
    from pocket.auth import ACCESS_NOTE, expected_user

    print("=" * 62, flush=True)
    print("POCKET host online", flush=True)
    print(f"  DESK:    http://127.0.0.1:{port}/desk", flush=True)
    print(f"  LANDING: http://127.0.0.1:{port}/", flush=True)
    print(f"  AUTH:    user={expected_user()}  file={ACCESS_NOTE}", flush=True)
    print(f"  HEART:   873ms runtime worker recommended (python -m pocket runtime-worker)", flush=True)
    print("=" * 62, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("stopped", flush=True)


def main(argv: Optional[list] = None) -> None:
    p = argparse.ArgumentParser(prog="pocket")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("serve", help="HTTP multi-agent desk")
    s.add_argument("--host", default="0.0.0.0")
    s.add_argument("--port", type=int, default=PORT)
    sub.add_parser("worker", help="Job worker only")
    r = sub.add_parser("runtime", help="Full Python runtime + watchdog (leave this on)")
    r.add_argument("--once", action="store_true", help="Serve once without watchdog")
    sub.add_parser(
        "runtime-worker",
        help="Keep-alive worker: 873ms heartbeat + auto-restart serve (use with Electron)",
    )
    sub.add_parser("doctor", help="Product readiness report")
    sub.add_parser("desktop", help="POCKET Desktop app (native window + local host)")
    sub.add_parser("channels", help="Print product channels (Desktop vs API)")
    sub.add_parser(
        "desktop-pack",
        help="Copy electron-builder output into releases/desktop for web download",
    )
    args = p.parse_args(argv)
    if args.cmd == "worker":
        from pocket.worker import run_loop

        run_loop()
        return
    if args.cmd == "runtime-worker":
        from pocket.runtime_worker import run as runtime_worker_run

        runtime_worker_run()
        return
    if args.cmd == "runtime":
        from pocket.runtime import main as runtime_main

        runtime_main(["--once"] if getattr(args, "once", False) else [])
        return
    if args.cmd == "doctor":
        from pocket.product import doctor
        import json as _json

        print(_json.dumps(doctor(), indent=2, default=str))
        return
    if args.cmd == "desktop":
        from pocket.desktop_app import run_desktop

        raise SystemExit(run_desktop())
    if args.cmd == "desktop-pack":
        from pocket.desktop_pack import pack_releases
        import json as _json

        print(_json.dumps(pack_releases(), indent=2, default=str))
        return
    if args.cmd == "channels":
        from pocket.product_channels import channels
        import json as _json

        print(_json.dumps(channels(), indent=2, default=str))
        return
    if args.cmd == "serve" or args.cmd is None:
        serve(getattr(args, "host", "0.0.0.0"), getattr(args, "port", PORT))
        return
    p.print_help()


if __name__ == "__main__":
    main()




