"""CLI inventory — tools Python agents and LLMs can invoke on the host.

Production apps + CLIs people actually have when they build with AI.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List

# Known CLI tool catalog (id → discovery)
CLI_CATALOG: List[Dict[str, str]] = [
    {"id": "git", "bin": "git", "label": "Git", "group": "scm"},
    {"id": "gh", "bin": "gh", "label": "GitHub CLI", "group": "scm"},
    {"id": "codex", "bin": "codex", "label": "OpenAI Codex CLI", "group": "ai"},
    {"id": "claude", "bin": "claude", "label": "Claude Code CLI", "group": "ai"},
    {"id": "grok", "bin": "grok", "label": "Grok CLI", "group": "ai"},
    {"id": "antigravity", "bin": "antigravity", "label": "Antigravity", "group": "ai"},
    {"id": "cursor", "bin": "cursor", "label": "Cursor CLI", "group": "ai"},
    {"id": "code", "bin": "code", "label": "VS Code CLI", "group": "editor"},
    {"id": "node", "bin": "node", "label": "Node.js", "group": "runtime"},
    {"id": "npm", "bin": "npm", "label": "npm", "group": "runtime"},
    {"id": "python", "bin": "python", "label": "Python", "group": "runtime"},
    {"id": "pip", "bin": "pip", "label": "pip", "group": "runtime"},
    {"id": "docker", "bin": "docker", "label": "Docker CLI", "group": "ops"},
    {"id": "kubectl", "bin": "kubectl", "label": "kubectl", "group": "ops"},
    {"id": "wrangler", "bin": "wrangler", "label": "Cloudflare Wrangler", "group": "ops"},
    {"id": "cloudflared", "bin": "cloudflared", "label": "cloudflared", "group": "ops"},
    {"id": "terraform", "bin": "terraform", "label": "Terraform", "group": "ops"},
    {"id": "cargo", "bin": "cargo", "label": "Rust cargo", "group": "runtime"},
    {"id": "go", "bin": "go", "label": "Go", "group": "runtime"},
    {"id": "powershell", "bin": "powershell", "label": "PowerShell", "group": "shell"},
    {"id": "wsl", "bin": "wsl", "label": "WSL", "group": "shell"},
    {"id": "winget", "bin": "winget", "label": "winget", "group": "shell"},
]


def which_tool(bin_name: str) -> str:
    p = shutil.which(bin_name) or ""
    if p:
        return p
    # grok special
    if bin_name == "grok":
        cand = Path.home() / ".grok" / "bin" / "grok.exe"
        if cand.exists():
            return str(cand)
    if bin_name == "antigravity":
        for c in (
            Path.home() / "AppData" / "Local" / "Programs" / "Antigravity" / "Antigravity.exe",
            Path.home() / "AppData" / "Local" / "Programs" / "antigravity" / "antigravity.exe",
            Path.home() / "AppData" / "Local" / "antigravity" / "antigravity.exe",
        ):
            if c.exists():
                return str(c)
        # also try npx-style
        w = shutil.which("antigravity.cmd") or shutil.which("agy")
        if w:
            return w
    return ""


def inventory() -> Dict[str, Any]:
    tools = []
    for t in CLI_CATALOG:
        path = which_tool(t["bin"])
        tools.append({**t, "available": bool(path), "path": path or None})
    # version samples for available AI tools
    for t in tools:
        if t["available"] and t["id"] in ("git", "gh", "node", "python", "codex", "docker"):
            try:
                r = subprocess.run(
                    [t["path"] or t["bin"], "--version"],
                    capture_output=True,
                    text=True,
                    timeout=8,
                )
                t["version"] = ((r.stdout or r.stderr or "")[:120]).strip()
            except Exception:
                t["version"] = ""
    return {
        "ok": True,
        "count": len(tools),
        "available": sum(1 for x in tools if x["available"]),
        "tools": tools,
        "note": "CLIs on PATH the platform can open or shell into. Auth stays on host (gh login, etc.).",
    }


def open_cli_app(tool_id: str) -> Dict[str, Any]:
    """Open associated desktop app for a CLI when possible."""
    from pocket.desktop import open_app
    from pocket.live_events import emit

    tid = (tool_id or "").lower().strip()
    emit("cli", f"Open tool/app {tid}", agent="cli", role="python")
    mapping = {
        "antigravity": "antigravity",
        "cursor": "cursor",
        "code": "code",
        "vscode": "code",
        "github": "github",
        "gh": "github",
        "docker": "docker",
        "wt": "wt",
        "terminal": "wt",
    }
    app = mapping.get(tid, tid)
    return open_app(app)
