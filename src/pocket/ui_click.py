"""Same-window interface control — click named UI, maximize, close window (not kill process).

Uses UI Automation when possible so workers act like a user on one page.
"""

from __future__ import annotations

import subprocess
import time
from typing import Any, Dict, List, Optional

from pocket.live_events import emit
from pocket.ui_maneuver import focus_window_title, send_keys, set_clipboard


def maximize_foreground() -> Dict[str, Any]:
    """Maximize the currently focused window (Win+Up)."""
    emit("ui", "Maximize foreground window", agent="PORTARIUS", role="python")
    # Win+Up
    ps = r"""
$w = New-Object -ComObject wscript.shell
Start-Sleep -Milliseconds 200
$w.SendKeys('%{ }')  # Alt+Space
Start-Sleep -Milliseconds 150
$w.SendKeys('x')     # Maximize
'ok'
"""
    try:
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, timeout=10)
        # also Win+Up via shell
        subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "$w=New-Object -ComObject wscript.shell; $w.SendKeys('^{UP}'); "
             # Win key is harder; use ShowWindow maximize on foreground
             "Add-Type @'\nusing System;using System.Runtime.InteropServices;\npublic class M{\n[DllImport(\"user32.dll\")]public static extern IntPtr GetForegroundWindow();\n[DllImport(\"user32.dll\")]public static extern bool ShowWindow(IntPtr h,int n);\n}\n'@; [M]::ShowWindow([M]::GetForegroundWindow(),3); 'max'"],
            capture_output=True,
            timeout=10,
        )
        return {"ok": True, "message": "Maximized foreground window"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def close_foreground_window() -> Dict[str, Any]:
    """Alt+F4 on focused window only — does NOT kill Edge process / other tabs."""
    emit("ui", "Close foreground window (Alt+F4)", agent="PORTARIUS", role="python")
    r = send_keys("%{F4}", settle_ms=300)
    return {"ok": r.get("ok"), "message": "Alt+F4 sent to foreground (gentle exit)"}


def scroll_page(times: int = 4, *, direction: str = "down") -> Dict[str, Any]:
    key = "{PGDN}" if direction == "down" else "{PGUP}"
    for _ in range(max(1, times)):
        send_keys(key, settle_ms=180)
        time.sleep(0.2)
    return {"ok": True, "scrolls": times, "direction": direction}


def click_named_element(name: str, *, control_type: str = "") -> Dict[str, Any]:
    """Click first UI Automation element whose Name matches (case-insensitive contains)."""
    nm = name.replace("'", "''")
    ct = control_type.replace("'", "''") if control_type else ""
    ps = rf"""
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::NameProperty, '{nm}'
)
# try exact first
$el = $root.FindFirst([System.Windows.Automation.TreeScope]::Descendants, $cond)
if (-not $el) {{
  # walk partial match (limited)
  $all = $root.FindAll([System.Windows.Automation.TreeScope]::Descendants,
    [System.Windows.Automation.Condition]::TrueCondition)
  $i = 0
  foreach ($e in $all) {{
    $i++
    if ($i -gt 4000) {{ break }}
    try {{
      $n = $e.Current.Name
      if ($n -and ($n -like '*{nm}*' -or $n -eq '{nm}')) {{ $el = $e; break }}
    }} catch {{}}
  }}
}}
if (-not $el) {{ 'miss'; exit 1 }}
try {{
  $inv = $el.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
  $inv.Invoke()
  'invoked:' + $el.Current.Name
}} catch {{
  try {{
    $rect = $el.Current.BoundingRectangle
    $x = [int]($rect.X + $rect.Width/2)
    $y = [int]($rect.Y + $rect.Height/2)
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.Cursor]::Position = New-Object System.Drawing.Point($x,$y)
    # mouse click via user32
    Add-Type @"
using System; using System.Runtime.InteropServices;
public class C {{
  [DllImport(\"user32.dll\")] public static extern void mouse_event(int f,int dx,int dy,int d,int e);
}}
"@
    [C]::mouse_event(0x02,0,0,0,0); [C]::mouse_event(0x04,0,0,0,0)
    'clicked:' + $el.Current.Name + '@' + $x + ',' + $y
  }} catch {{ 'fail:' + $_.Exception.Message; exit 2 }}
}}
"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=45,
        )
        out = (r.stdout or r.stderr or "").strip()
        emit("ui", f"Click '{name}': {out[:100]}", agent="UI", role="python")
        return {"ok": r.returncode == 0 and not out.startswith("miss") and not out.startswith("fail"), "detail": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def github_use_interface(repo_url: str) -> Dict[str, Any]:
    """Open ONE GitHub repo once, then navigate purely via UI: scroll, click tabs in same window."""
    from pocket.browser_mode import open_edge_url

    url = (repo_url or "").strip()
    if not url.startswith("http"):
        url = f"https://github.com/{url}"
    parts = url.replace("https://github.com/", "").split("/")
    if len(parts) >= 2:
        base = f"https://github.com/{parts[0]}/{parts[1]}"
    else:
        base = url

    emit("github", f"Single-page UI tour: {base}", agent="REPOSITOR", role="python")
    # ONE window — no new-window flood
    open_edge_url(base, profile="Default", new_window=True)
    time.sleep(2.2)
    focus_window_title("GitHub")
    maximize_foreground()
    time.sleep(0.5)

    actions: List[Dict[str, Any]] = []

    # Scroll like a user reading the README
    actions.append({"scroll_down": scroll_page(5, direction="down")})
    time.sleep(0.4)
    actions.append({"scroll_up": scroll_page(2, direction="up")})
    time.sleep(0.3)

    # Click in-page nav tabs (same browser window — Invoke/click, not new Edge launches)
    for tab in ("Code", "Issues", "Pull requests", "Actions", "Projects", "Security", "Insights"):
        focus_window_title("GitHub")
        r = click_named_element(tab)
        actions.append({"tab": tab, **r})
        time.sleep(1.1)
        # scroll that view
        scroll_page(2, direction="down")
        time.sleep(0.35)
        scroll_page(1, direction="up")
        time.sleep(0.25)

    # Return to Code via UI
    focus_window_title("GitHub")
    click_named_element("Code")
    time.sleep(0.8)
    scroll_page(3, direction="down")

    return {
        "ok": True,
        "mode": "same_window_interface",
        "repo": base,
        "actions": actions,
        "message": f"Used GitHub interface on one window for {base} (scroll + click tabs, no multi-window links)",
        "skill": "github_interface_tour",
    }


def github_desktop_tour() -> Dict[str, Any]:
    """Open GitHub Desktop and light UI tour (scroll/list)."""
    from pocket.desktop import open_app

    emit("github", "GitHub Desktop UI tour", agent="REPOSITOR", role="python")
    open_app("github")
    time.sleep(2.5)
    focus_window_title("GitHub Desktop")
    maximize_foreground()
    time.sleep(0.5)
    # arrow/tab around UI
    for _ in range(4):
        send_keys("{DOWN}", settle_ms=120)
        time.sleep(0.15)
    send_keys("{TAB}", settle_ms=150)
    send_keys("{TAB}", settle_ms=150)
    scroll_page(2, direction="down")
    time.sleep(0.8)
    # knowledge note for workers
    knowledge = (
        "GitHub Desktop: left = current repo; center = changes; "
        "History tab for commits; Branch menu for branches; "
        "Fetch origin / Pull / Push in top bar; "
        "Clone via File > Clone repository. Prefer HTTPS remotes with gh auth."
    )
    from pathlib import Path
    import json

    brain = Path.home() / ".pocket" / "worker_brains" / "REPOSITOR_github_desktop.json"
    brain.parent.mkdir(parents=True, exist_ok=True)
    brain.write_text(
        json.dumps({"learned_at": time.time(), "knowledge": knowledge, "source": "github_desktop_tour"}, indent=2),
        encoding="utf-8",
    )
    return {
        "ok": True,
        "message": "GitHub Desktop opened, maximized, navigated; knowledge saved to worker brain",
        "brain": str(brain),
        "knowledge": knowledge,
    }


def app_open_max_scroll_exit(app_focus_title: str, open_fn, *, hold_sec: float = 2.0, scrolls: int = 3) -> Dict[str, Any]:
    """Open app → maximize → scroll/wait → gentle Alt+F4 exit. Never kills Edge process."""
    open_fn()
    time.sleep(1.5)
    focus_window_title(app_focus_title)
    maximize_foreground()
    time.sleep(0.4)
    scroll_page(scrolls, direction="down")
    time.sleep(hold_sec)
    close_foreground_window()
    time.sleep(0.4)
    return {"ok": True, "app": app_focus_title, "message": f"{app_focus_title}: open→max→scroll→exit"}
