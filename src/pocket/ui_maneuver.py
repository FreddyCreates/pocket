"""UI maneuver layer — click, type, focus (interface, not only URL open).

Uses Win32 + SendKeys. Skills call this so workers act inside apps.
"""

from __future__ import annotations

import subprocess
import time
from typing import Any, Dict, List, Optional

from pocket.live_events import emit


def send_keys(sequence: str, *, settle_ms: int = 300) -> Dict[str, Any]:
    """SendKeys sequence (PowerShell System.Windows.Forms)."""
    # Escape for PowerShell single-quoted string carefully
    seq = sequence.replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        f"Start-Sleep -Milliseconds {int(settle_ms)}; "
        f"[System.Windows.Forms.SendKeys]::SendWait('{seq}'); "
        "'ok'"
    )
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=30,
        )
        emit("ui", f"SendKeys {sequence[:40]}", agent="UI", role="python")
        return {"ok": r.returncode == 0, "out": (r.stdout or "")[:80]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def set_clipboard(text: str) -> bool:
    try:
        import win32clipboard  # type: ignore

        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, text)
        win32clipboard.CloseClipboard()
        return True
    except Exception:
        try:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", f"Set-Clipboard -Value @'\n{text}\n'@"],
                capture_output=True,
                timeout=10,
            )
            return True
        except Exception:
            return False


def focus_window_title(pattern: str) -> Dict[str, Any]:
    ps = rf"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class F {{
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int n);
}}
"@
$p = Get-Process | Where-Object {{ $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle -like '*{pattern}*' }} | Select-Object -First 1
if ($p) {{
  [F]::ShowWindow($p.MainWindowHandle, 9) | Out-Null
  [F]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
  'focused:' + $p.MainWindowTitle
}} else {{ 'miss' }}
"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=15,
        )
        out = (r.stdout or "").strip()
        emit("ui", f"Focus {pattern}: {out[:80]}", agent="UI", role="python")
        return {"ok": out.startswith("focused"), "detail": out}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def paste_and_enter(*, settle_ms: int = 500) -> Dict[str, Any]:
    return send_keys("^v", settle_ms=settle_ms) and send_keys("{ENTER}", settle_ms=400)


def type_text(text: str, *, use_clipboard: bool = True) -> Dict[str, Any]:
    if use_clipboard:
        set_clipboard(text)
        return send_keys("^v", settle_ms=400)
    # slow type via SendKeys escaped
    esc = []
    for ch in text[:200]:
        if ch in "+^%~(){}[]":
            esc.append("{" + ch + "}")
        elif ch == "\n":
            esc.append("{ENTER}")
        else:
            esc.append(ch)
    return send_keys("".join(esc), settle_ms=200)


def shell_start_appuser(app_user_model_id: str) -> Dict[str, Any]:
    """Launch Store/packaged app by AUMID."""
    try:
        subprocess.Popen(
            ["explorer.exe", f"shell:AppsFolder\\{app_user_model_id}"],
            shell=False,
        )
        emit("ui", f"Start packaged {app_user_model_id[:50]}", agent="PORTARIUS", role="python")
        return {"ok": True, "aumid": app_user_model_id}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def close_edge_only() -> Dict[str, Any]:
    """Close Microsoft Edge processes only (not whole PC)."""
    emit("ui", "Closing Edge windows only…", agent="PORTARIUS", role="python")
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command",
             "Get-Process msedge -ErrorAction SilentlyContinue | Stop-Process -Force; 'closed'"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        return {"ok": True, "message": "Edge processes closed", "out": (r.stdout or "").strip()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
