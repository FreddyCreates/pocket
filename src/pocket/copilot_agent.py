"""Windows Copilot intro agent — Python opens app + clipboard intro for the user/LLM persona.

Cannot inject text into Copilot's private UI reliably; production path:
  1. Build intro blurb (Python + optional LLM)
  2. Put on clipboard
  3. Open Windows Copilot app
  4. User Ctrl+V once (or we try SendKeys best-effort)
"""

from __future__ import annotations

import subprocess
import time
from typing import Any, Dict, Optional, Tuple

from pocket.live_events import emit


DEFAULT_INTRO = (
    "Hello Copilot — I'm working with POCKET (ItsNotAI Labs / Medina Tech Labs) on this Windows PC. "
    "POCKET is a multi-agent desk: Browser mode, GUPPY Python workers, Codex/Grok coding engines, "
    "and desktop control. The operator is signed in on this machine. "
    "Please treat me as their co-pilot for host tasks; they may paste research or tweet drafts next."
)


def _set_clipboard_text(text: str) -> bool:
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


def _try_paste_sendkeys() -> bool:
    """Best-effort paste into focused window after Copilot opens."""
    try:
        ps = (
            "Start-Sleep -Milliseconds 1200; "
            "Add-Type -AssemblyName System.Windows.Forms; "
            "[System.Windows.Forms.SendKeys]::SendWait('^v')"
        )
        subprocess.Popen(["powershell", "-NoProfile", "-Command", ps], shell=False)
        return True
    except Exception:
        return False


def _focus_copilot_window() -> bool:
    """Try to bring Copilot / Windows Copilot window to foreground."""
    ps = r"""
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr hWnd);
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
}
"@
$names = @('*Copilot*','*Windows Copilot*','*Microsoft Copilot*','*ChatGPT*')
$p = Get-Process | Where-Object { $_.MainWindowHandle -ne 0 } | Where-Object {
  $t = $_.MainWindowTitle; $names | ForEach-Object { if ($t -like $_) { return $true } }; $false
} | Select-Object -First 1
if (-not $p) {
  $p = Get-Process | Where-Object { $_.ProcessName -match 'Copilot|ApplicationFrameHost' -and $_.MainWindowHandle -ne 0 } | Select-Object -First 1
}
if ($p) {
  [W]::ShowWindow($p.MainWindowHandle, 9) | Out-Null
  [W]::SetForegroundWindow($p.MainWindowHandle) | Out-Null
  'focused:' + $p.ProcessName + ':' + $p.MainWindowTitle
} else { 'nofocus' }
"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=15,
        )
        out = (r.stdout or "").strip()
        emit("copilot", f"Focus: {out[:120]}", agent="CONSILIARIUS", role="python")
        return out.startswith("focused")
    except Exception as e:
        emit("copilot", f"Focus fail: {e}", agent="CONSILIARIUS", role="python", level="error")
        return False


def paste_and_send_copilot(text: str, *, already_open: bool = False) -> Dict[str, Any]:
    """Open Windows Copilot (if needed), paste text, press Enter to send.

    Reply fetch is deferred — operator reads reply in Copilot for now.
    """
    body = (text or "").strip()
    if not body:
        return {"ok": False, "error": "empty text"}
    emit("copilot", "CONSILIARIUS paste+send…", agent="CONSILIARIUS", role="python")
    clip = _set_clipboard_text(body)
    if not already_open:
        from pocket.browser_mode import open_windows_copilot

        open_windows_copilot()
        time.sleep(1.8)
    else:
        time.sleep(0.6)

    focused = _focus_copilot_window()
    time.sleep(0.4)

    # Synchronous SendKeys: click/focus, Ctrl+V, short wait, Enter
    ps = r"""
Add-Type -AssemblyName System.Windows.Forms
Start-Sleep -Milliseconds 400
# Try focus again via Alt-Tab-ish: Win+C sometimes opens Copilot sidebar on Win11
try { [System.Windows.Forms.SendKeys]::SendWait('^{ESC}'); Start-Sleep -Milliseconds 200 } catch {}
[System.Windows.Forms.SendKeys]::SendWait('^v')
Start-Sleep -Milliseconds 500
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
'pasted_sent'
"""
    try:
        r = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=20,
        )
        out = (r.stdout or r.stderr or "").strip()
        # Second attempt with longer settle if first was too fast
        time.sleep(0.3)
        _focus_copilot_window()
        ps2 = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "Start-Sleep -Milliseconds 600; "
            "[System.Windows.Forms.SendKeys]::SendWait('^v'); "
            "Start-Sleep -Milliseconds 400; "
            "[System.Windows.Forms.SendKeys]::SendWait('{ENTER}'); "
            "'ok'"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps2], capture_output=True, timeout=15)
        emit("copilot", "Paste+Enter dispatched to Copilot", agent="CONSILIARIUS", role="python")
        return {
            "ok": True,
            "kind": "copilot_paste_send",
            "clipboard": clip,
            "focused": focused,
            "text_chars": len(body),
            "text_preview": body[:200],
            "sendkeys": out,
            "message": (
                "CONSILIARIUS: text pasted and Enter sent to Windows Copilot. "
                "Reply fetch not yet automated — read the reply in the Copilot window."
            ),
            "agent": "CONSILIARIUS",
            "note": "If paste landed elsewhere, click Copilot input once and re-run introduce.",
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "clipboard": clip, "focused": focused}


def introduce_to_copilot(
    prompt: str = "",
    *,
    persona: str = "POCKET",
    use_llm: bool = False,
    cwd: str = "",
    job: Optional[dict] = None,
) -> Dict[str, Any]:
    emit("copilot", "Building Copilot introduction…", agent="copilot_intro", role="python")
    user_bit = (prompt or "").strip()
    if user_bit.lower().startswith("introduce"):
        user_bit = user_bit.split(None, 1)[1] if " " in user_bit else ""

    intro = DEFAULT_INTRO
    if persona and persona.upper() != "POCKET":
        intro = intro.replace("I'm working with POCKET", f"I'm {persona}, working with POCKET")
    if user_bit:
        intro = intro + " Operator note: " + user_bit[:400]

    engine_used = "python"
    if use_llm and user_bit:
        try:
            from pocket.browser_mode import _compose_with_engine

            out, err, eng = _compose_with_engine(
                "Write a short friendly introduction (under 400 chars) to Microsoft Copilot "
                f"as agent {persona} on POCKET desk. Include: multi-agent host, no passwords, signed-in browser. "
                f"Extra: {user_bit}\nOutput only the intro text.",
                cwd,
                job,
                "auto",
            )
            if out and len(out.strip()) > 40:
                # strip tags
                import re

                clean = re.sub(r"\[\[POCKET[^\]]*\]\]", "", out)
                clean = re.sub(r"^#+\s.*$", "", clean, flags=re.M).strip()
                if clean:
                    intro = clean[:500]
                    engine_used = eng
        except Exception:
            pass

    clip = _set_clipboard_text(intro)
    emit("copilot", "Opening Windows Copilot app…", agent="CONSILIARIUS", role="python")
    from pocket.browser_mode import open_windows_copilot

    opened = open_windows_copilot()
    send = paste_and_send_copilot(intro, already_open=True) if clip else {"ok": False}

    return {
        "ok": bool(opened.get("ok")),
        "kind": "copilot_intro",
        "intro": intro,
        "clipboard": clip,
        "paste_attempted": True,
        "sent": bool(send.get("ok")),
        "send_detail": send,
        "engine": engine_used,
        "opened": opened,
        "message": (
            "CONSILIARIUS: Windows Copilot opened; intro pasted and Enter sent. "
            "Read the reply in Copilot (auto-fetch next)."
        ),
        "note": "POCKET never stores your Microsoft password — app uses your signed-in Windows session.",
        "agent": "CONSILIARIUS",
    }


def run_copilot_job(prompt: str, *, cwd: str = "", job: Optional[dict] = None) -> Tuple[str, str, str]:
    low = (prompt or "").strip().lower()
    if low in ("help", ""):
        return (
            "## Copilot agent\n\n"
            "- `introduce` — open Windows Copilot + clipboard intro as POCKET\n"
            "- `introduce as Grok: …` — persona line\n"
            "- `open` — just open Windows Copilot\n"
            "- `open web` — web Copilot in Edge\n",
            "",
            "copilot",
        )
    if low in ("open", "open copilot"):
        from pocket.browser_mode import open_windows_copilot

        r = open_windows_copilot()
        return f"## Copilot\n\n{r.get('message')}\n", "" if r.get("ok") else "open failed", "copilot"
    if low.startswith("open web"):
        from pocket.browser_mode import open_web_copilot

        q = prompt[8:].strip() if len(prompt) > 8 else ""
        r = open_web_copilot(q)
        return f"## Web Copilot\n\n```json\n{r}\n```\n", "" if r.get("ok") else "fail", "copilot"
    # introduce…
    persona = "POCKET"
    body = prompt
    if low.startswith("introduce as "):
        rest = prompt[13:].strip()
        if ":" in rest:
            persona, body = rest.split(":", 1)
            persona, body = persona.strip(), body.strip()
        else:
            persona, body = rest, ""
    elif low.startswith("introduce"):
        body = prompt.split(None, 1)[1] if " " in prompt else ""
    r = introduce_to_copilot(body, persona=persona, use_llm=True, cwd=cwd, job=job)
    md = (
        f"## Copilot introduction ({r.get('engine')})\n\n"
        f"**{r.get('message')}**\n\n"
        f"> {r.get('intro')}\n\n"
        f"clipboard={r.get('clipboard')} · paste_attempted={r.get('paste_attempted')}\n"
    )
    return md, "" if r.get("ok") else "copilot open failed", "copilot"
