"""Host backend — local now, virtual machine / remote later. Same skill API.

Orchestrator and workers call HostBackend; swap LocalHost for RemoteHost(VM).
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional

HOST_CFG = Path.home() / ".pocket" / "host.json"


class HostBackend(ABC):
    @abstractmethod
    def kind(self) -> str: ...

    @abstractmethod
    def execute_skill(self, skill: str, *, prompt: str = "", params: Optional[Dict] = None) -> Dict[str, Any]: ...

    @abstractmethod
    def observe(self) -> Dict[str, Any]: ...


class LocalHost(HostBackend):
    def kind(self) -> str:
        return "local"

    def execute_skill(self, skill: str, *, prompt: str = "", params: Optional[Dict] = None) -> Dict[str, Any]:
        from pocket.orchestrator import get_orchestrator

        return get_orchestrator().execute(skill, prompt=prompt, params=params or {})

    def observe(self) -> Dict[str, Any]:
        from pocket.vision_core import observe

        return observe(with_ui_map=True)


class RemoteHost(HostBackend):
    """Scaffold: same interface, posts to remote POCKET on a VM.

    Configure ~/.pocket/host.json:
      {"backend":"remote","base_url":"http://vm:8787","token":"..."}
    """

    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def kind(self) -> str:
        return "remote_vm"

    def execute_skill(self, skill: str, *, prompt: str = "", params: Optional[Dict] = None) -> Dict[str, Any]:
        import urllib.request

        body = json.dumps({"skill": skill, "prompt": prompt, "params": params or {}}).encode()
        req = urllib.request.Request(
            f"{self.base_url}/v1/skills/run",
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.token}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            return {"ok": False, "error": str(e), "backend": "remote_vm", "scaffold": True}

    def observe(self) -> Dict[str, Any]:
        import urllib.request

        try:
            req = urllib.request.Request(f"{self.base_url}/v1/vision/observe", method="GET")
            if self.token:
                req.add_header("Authorization", f"Bearer {self.token}")
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as e:
            return {"ok": False, "error": str(e), "scaffold": True, "note": "Start POCKET on VM with same API"}


def get_host() -> HostBackend:
    if HOST_CFG.exists():
        try:
            cfg = json.loads(HOST_CFG.read_text(encoding="utf-8"))
            if cfg.get("backend") == "remote" and cfg.get("base_url"):
                return RemoteHost(cfg["base_url"], cfg.get("token") or "")
        except Exception:
            pass
    return LocalHost()
