"""Microsoft host protocol — thin safe hooks into desktop / UIA / page render.

No free-form PowerShell execution. All actions route through existing pocket
modules (desktop, page_renderer, ui_click) which already constrain surface area.

Canonical package path; `pocket.ms_protocol` remains a compatibility shim.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def status() -> Dict[str, Any]:
    try:
        from pocket.mesh_disk import PROTOCOLS

        path = str(PROTOCOLS / "microsoft")
    except Exception:
        path = ""
    return {
        "ok": True,
        "protocol": "microsoft",
        "path": path,
        "hooks": [
            "open_host_app",
            "list_host_apps",
            "click_ui",
            "maximize_window",
            "close_foreground",
            "scroll_ui",
            "render_page",
            "find_symbols",
            "sense_ui",
        ],
        "capabilities": [
            "uia_page_render",
            "desktop_open_app",
            "guarded_shell",
            "screenshot",
            "ui_click",
        ],
        "note": "UIA/Win32/PowerShell only via pocket.desktop / ui_click / page_renderer",
    }


def open_host_app(app_id: str, *, args: str = "", path: str = "") -> Dict[str, Any]:
    """Open an allow-listed host app (desktop.open_app)."""
    from pocket.desktop import open_app

    return open_app(app_id, args=args, path=path)


def list_host_apps() -> Dict[str, Any]:
    """List allow-listed apps with resolved paths."""
    from pocket.desktop import list_apps

    apps = list_apps()
    return {"ok": True, "apps": apps, "count": len(apps)}


def click_ui(name: str, *, control_type: str = "") -> Dict[str, Any]:
    """Click a named UIA element (ui_click.click_named_element)."""
    from pocket.ui_click import click_named_element

    return click_named_element(name, control_type=control_type)


def maximize_window() -> Dict[str, Any]:
    """Maximize the foreground window."""
    from pocket.ui_click import maximize_foreground

    return maximize_foreground()


def close_foreground() -> Dict[str, Any]:
    """Alt+F4 foreground window only (not process kill)."""
    from pocket.ui_click import close_foreground_window

    return close_foreground_window()


def scroll_ui(times: int = 4, *, direction: str = "down") -> Dict[str, Any]:
    """Page scroll via key events."""
    from pocket.ui_click import scroll_page

    return scroll_page(times, direction=direction)


def render_page(
    *,
    max_ui: int = 400,
    include_image: bool = False,
) -> Dict[str, Any]:
    """Deep UI map / page render via page_renderer."""
    from pocket.page_renderer import render_full_page

    return render_full_page(max_ui=max_ui, include_image=include_image)


def find_symbols(query: str, page: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Find UI symbols matching query on current or provided page map."""
    from pocket.page_renderer import find_symbols as _find

    hits = _find(query, page=page)
    return {"ok": True, "query": query, "hits": hits, "count": len(hits)}


def sense_ui(*, max_ui: int = 400) -> Dict[str, Any]:
    """Perception sense (UIA + brief) — used by OCULUS-style callers."""
    from pocket.perception import sense

    return sense(force=True, max_ui=max_ui)


def safe_shell_echo(text: str = "microsoft_protocol ok") -> Dict[str, Any]:
    """Sanity probe only — routes through sanity.guard_shell, not raw PS."""
    from pocket.sanity import guard_shell

    # guard_shell validates; does not execute arbitrary PowerShell
    safe = (text or "ok").replace('"', "")[:80]
    return guard_shell(f'echo "{safe}"')


def invoke(
    action: str,
    *,
    app_id: str = "",
    name: str = "",
    query: str = "",
    times: int = 4,
    direction: str = "down",
    args: str = "",
    path: str = "",
    prompt: str = "",
) -> Dict[str, Any]:
    """Dispatch a named microsoft protocol action."""
    a = (action or "").strip().lower()
    if a in ("open", "open_app", "open_host_app", "open_surface"):
        return open_host_app(app_id or "notepad", args=args, path=path)
    if a in ("list", "list_apps", "list_host_apps"):
        return list_host_apps()
    if a in ("click", "click_ui"):
        return click_ui(name or query)
    if a in ("maximize", "maximize_window"):
        return maximize_window()
    if a in ("close", "close_foreground"):
        return close_foreground()
    if a in ("scroll", "scroll_ui"):
        return scroll_ui(times, direction=direction)
    if a in ("render", "render_page", "page", "symbols", "page_render"):
        return render_page()
    if a in ("find", "find_symbols"):
        return find_symbols(query or name or prompt)
    if a in ("sense", "uia", "ui", "sense_ui"):
        return sense_ui()
    if a in ("shell", "ps", "guard"):
        return safe_shell_echo(prompt or "microsoft_protocol ok")
    if a == "screenshot":
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute("screenshot", prompt=prompt)
    if a in ("status", "probe", "help"):
        return status()
    return {"ok": False, "error": f"unknown microsoft action: {action}"}


# Compatibility names used by pocket.ms_protocol
def open_surface(app: str = "explorer") -> Dict[str, Any]:
    return open_host_app(app)


def page_symbols(prompt: str = "") -> Dict[str, Any]:
    return render_page()


def guarded_shell(cmd: str) -> Dict[str, Any]:
    return safe_shell_echo(cmd or "ok")


def run(action: str, *, prompt: str = "", app: str = "explorer", cmd: str = "") -> Dict[str, Any]:
    """ms_protocol-compatible entrypoint."""
    return invoke(action, app_id=app, prompt=prompt or cmd, query=prompt)
