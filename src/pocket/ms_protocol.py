"""Microsoft system protocol — compatibility shim.

Canonical implementation: `pocket.protocols.microsoft_protocol`.
"""

from __future__ import annotations

from pocket.protocols.microsoft_protocol import (  # noqa: F401
    click_ui,
    close_foreground,
    find_symbols,
    guarded_shell,
    invoke,
    list_host_apps,
    maximize_window,
    open_host_app,
    open_surface,
    page_symbols,
    render_page,
    run,
    safe_shell_echo,
    scroll_ui,
    sense_ui,
    status,
)

__all__ = [
    "status",
    "open_surface",
    "open_host_app",
    "sense_ui",
    "page_symbols",
    "render_page",
    "guarded_shell",
    "click_ui",
    "run",
    "invoke",
]
