from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class DolphinSchedulerClient:
    """Small DS client facade.

    In demo mode it writes request payloads to local files. In production, replace
    `_request` with HTTP calls to DolphinScheduler OpenAPI.
    """

    def __init__(self, endpoint: str, token: str | None = None, audit_dir: str | Path = "data/dolphinscheduler/audit") -> None:
        self.endpoint = endpoint.rstrip("/")
        self.token = token
        self.audit_dir = Path(audit_dir)

    def _request(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        path = self.audit_dir / f"{action}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
        return {"status": "OK", "action": action, "audit_file": str(path)}

    def create_project(self, project_name: str, description: str = "") -> dict[str, Any]:
        return self._request("create_project", {"projectName": project_name, "description": description})

    def create_or_update_process(self, project_name: str, process_definition: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "create_or_update_process",
            {"projectName": project_name, "processDefinition": process_definition}
        )

    def online_process(self, project_name: str, process_name: str) -> dict[str, Any]:
        return self._request("online_process", {"projectName": project_name, "processName": process_name})

    def set_schedule(self, project_name: str, process_name: str, cron: str) -> dict[str, Any]:
        return self._request(
            "set_schedule",
            {"projectName": project_name, "processName": process_name, "cron": cron}
        )

    def query_instance_state(self, project_name: str, process_name: str) -> dict[str, Any]:
        return self._request("query_instance_state", {"projectName": project_name, "processName": process_name})
