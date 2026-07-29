"""TABELLARIUS — Outlook draft (display only, never Send)."""

from __future__ import annotations

import os
import shutil
import subprocess
import time
import urllib.parse
from pathlib import Path
from typing import Any, Dict

from pocket.live_events import emit

DRAFT_DIR = Path.home() / ".pocket" / "drafts"
DRAFT_DIR.mkdir(parents=True, exist_ok=True)


def create_draft(*, subject: str = "POCKET test", body: str = "Test body", to: str = "") -> Dict[str, Any]:
    """Open a draft email with subject/body. Never calls Send."""
    emit("outlook", "TABELLARIUS creating draft…", agent="TABELLARIUS", role="python")
    subject = (subject or "POCKET test subject")[:200]
    body = body or "POCKET TABELLARIUS draft — not sent."
    to = (to or "").strip()

    # 1) Classic Outlook COM
    try:
        import win32com.client  # type: ignore

        for prog in ("Outlook.Application", "Outlook.Application.16", "Outlook.Application.15"):
            try:
                outlook = win32com.client.Dispatch(prog)
                mail = outlook.CreateItem(0)
                mail.Subject = subject
                mail.Body = body
                if to:
                    mail.To = to
                mail.Display(True)
                emit("outlook", f"COM draft via {prog}", agent="TABELLARIUS", role="python")
                return {
                    "ok": True,
                    "kind": "outlook_draft",
                    "method": "com",
                    "prog": prog,
                    "subject": subject,
                    "to": to or "(none)",
                    "sent": False,
                    "message": "Outlook draft open (COM) — not sent",
                    "agent": "TABELLARIUS",
                    "at": time.time(),
                }
            except Exception:
                continue
    except Exception as e:
        com_err = str(e)
    else:
        com_err = "no progid"

    # 2) outlook.exe /c ipm.note — then paste body via clipboard + sendkeys
    outlook_exe = (
        shutil.which("outlook")
        or shutil.which("OUTLOOK.EXE")
        or r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE"
    )
    if outlook_exe and os.path.isfile(outlook_exe):
        try:
            subprocess.Popen([outlook_exe, "/c", "ipm.note"], shell=False)
            time.sleep(2.0)
            # clipboard body; user sees new mail — try set subject/body via SendKeys limited
            try:
                import win32clipboard  # type: ignore

                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_UNICODETEXT, body)
                win32clipboard.CloseClipboard()
            except Exception:
                pass
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "Start-Sleep -Milliseconds 800; "
                # Alt+S is send — DO NOT use. Tab to body and paste only.
                "[System.Windows.Forms.SendKeys]::SendWait('%u'); "  # sometimes focus
                "Start-Sleep -Milliseconds 200; "
                f"[System.Windows.Forms.SendKeys]::SendWait('{_escape_sendkeys(subject)}'); "
                "[System.Windows.Forms.SendKeys]::SendWait('{{TAB}}'); "
                "[System.Windows.Forms.SendKeys]::SendWait('^v'); "
            )
            # Safer: only paste body into focused compose
            ps = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "Start-Sleep -Milliseconds 1500; "
                "[System.Windows.Forms.SendKeys]::SendWait('^v'); "
            )
            subprocess.Popen(["powershell", "-NoProfile", "-Command", ps], shell=False)
            emit("outlook", "outlook.exe /c ipm.note + paste body", agent="TABELLARIUS", role="python")
            return {
                "ok": True,
                "kind": "outlook_draft",
                "method": "outlook_exe",
                "subject": subject,
                "body_preview": body[:200],
                "sent": False,
                "message": "New Outlook message opened; body pasted — set subject if needed; NOT sent",
                "agent": "TABELLARIUS",
                "com_error": com_err,
            }
        except Exception as e2:
            exe_err = str(e2)
    else:
        exe_err = "outlook.exe not found"

    # 3) mailto: opens default mail client with subject/body (draft, user sends)
    try:
        q = urllib.parse.urlencode({"subject": subject, "body": body[:1500]})
        mailto = f"mailto:{to}?{q}" if to else f"mailto:?{q}"
        os.startfile(mailto)  # type: ignore[attr-defined]
        emit("outlook", "mailto: draft opened", agent="TABELLARIUS", role="python")
        return {
            "ok": True,
            "kind": "outlook_draft",
            "method": "mailto",
            "subject": subject,
            "sent": False,
            "message": "Default mail client opened with subject/body (mailto) — not sent",
            "agent": "TABELLARIUS",
            "com_error": com_err,
            "exe_error": exe_err,
        }
    except Exception as e3:
        pass

    # 4) Write .eml and open
    try:
        eml = DRAFT_DIR / f"draft-{int(time.time())}.eml"
        content = (
            f"To: {to}\r\n"
            f"Subject: {subject}\r\n"
            f"X-Unsent: 1\r\n"
            f"Content-Type: text/plain; charset=utf-8\r\n"
            f"\r\n"
            f"{body}\r\n"
        )
        eml.write_text(content, encoding="utf-8")
        os.startfile(str(eml))  # type: ignore[attr-defined]
        emit("outlook", f"Opened .eml {eml.name}", agent="TABELLARIUS", role="python")
        return {
            "ok": True,
            "kind": "outlook_draft",
            "method": "eml",
            "path": str(eml),
            "subject": subject,
            "sent": False,
            "message": f"Draft .eml opened: {eml} — not sent",
            "agent": "TABELLARIUS",
        }
    except Exception as e4:
        return {
            "ok": False,
            "error": f"COM:{com_err}; exe:{exe_err}; eml:{e4}",
            "message": "Could not create draft",
            "agent": "TABELLARIUS",
        }


def _escape_sendkeys(s: str) -> str:
    # minimal escape for SendKeys specials
    out = []
    for ch in s[:120]:
        if ch in "+^%~(){}[]":
            out.append("{" + ch + "}")
        else:
            out.append(ch)
    return "".join(out)
