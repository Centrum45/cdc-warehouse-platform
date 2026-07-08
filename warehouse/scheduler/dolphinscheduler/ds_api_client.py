from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class DolphinSchedulerClient:
    """DolphinScheduler OpenAPI client.

    Supports two modes:
    - Live mode (default): real HTTP calls to DolphinScheduler OpenAPI.
    - Audit mode: writes request payloads to local files for offline review.

    Requires DS >= 3.0 for the v2 OpenAPI endpoints.
    """

    def __init__(
        self,
        endpoint: str,
        token: str | None = None,
        audit_mode: bool = False,
        audit_dir: str | Path = "data/dolphinscheduler/audit",
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.token = token or ""
        self.audit_mode = audit_mode
        self.audit_dir = Path(audit_dir)

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _build_url(self, path: str) -> str:
        return f"{self.endpoint}{path}"

    def _headers(self, with_content_type: bool = True) -> dict[str, str]:
        headers = {}
        if with_content_type:
            headers["Content-Type"] = "application/json"
        if self.token:
            # DS 3.x standalone uses cookie-based auth with sessionId
            headers["Cookie"] = f"sessionId={self.token}"
        return headers

    def _http(self, method: str, path: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send an HTTP request to the DS OpenAPI, parse JSON response."""
        url = self._build_url(path)
        has_body = body is not None
        data = json.dumps(body).encode("utf-8") if has_body else None
        req = urllib.request.Request(url, data=data, headers=self._headers(with_content_type=has_body), method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            error_body = exc.read().decode("utf-8", errors="replace")
            return {"code": exc.code, "msg": error_body, "success": False}
        except urllib.error.URLError as exc:
            return {"code": -1, "msg": str(exc.reason), "success": False}

    def _audit(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Write payload to a local audit file (demo / offline mode)."""
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        path = self.audit_dir / f"{action}.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return {"status": "OK", "action": action, "audit_file": str(path)}

    def _request(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch based on mode."""
        if self.audit_mode:
            return self._audit(action, payload)
        return self._do_request(action, payload)

    # ------------------------------------------------------------------
    # OpenAPI operations
    # ------------------------------------------------------------------

    def _do_request(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Map logical action names to DS OpenAPI calls."""
        if action == "create_project":
            return self._http("POST", "/v2/projects", payload)
        if action == "update_project":
            code = payload.get("projectCode")
            return self._http("PUT", f"/v2/projects/{code}", payload)
        if action == "query_project":
            name = payload.get("projectName", "")
            return self._http("GET", f"/v2/projects?pageNo=1&pageSize=50&searchVal={name}")
        if action == "create_or_update_process":
            return self._create_or_update_process_impl(payload)
        if action == "online_process":
            return self._release_process(payload, release_state="ONLINE")
        if action == "offline_process":
            return self._release_process(payload, release_state="OFFLINE")
        if action == "set_schedule":
            return self._set_schedule(payload)
        if action == "query_instance_state":
            return self._query_instance_state(payload)
        return {"code": -1, "msg": f"Unknown action: {action}", "success": False}

    # ------------------------------------------------------------------
    # Composite operations
    # ------------------------------------------------------------------

    def _create_or_update_process_impl(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create or update a process definition.

        1. Look up the project code by name.
        2. Try to find an existing process definition by name.
        3. Create or update.
        """
        project_name: str = payload["projectName"]
        process_def: dict[str, Any] = payload["processDefinition"]
        process_name: str = process_def.get("name", "")

        # 1) Resolve project code
        proj = self._resolve_project_code(project_name)
        if proj is None:
            return {"code": -1, "msg": f"Project not found: {project_name}", "success": False}
        project_code = proj["code"]

        # 2) Look for existing process definition
        existing = self._find_process_by_name(project_code, process_name)

        if existing is None:
            # Create
            create_body = {
                "projectCode": project_code,
                "name": process_name,
                "description": process_def.get("description", ""),
                "globalParams": process_def.get("globalParams", []),
                "locations": process_def.get("locations", ""),
                "timeout": process_def.get("timeout", 0),
                "taskDefinitionJson": json.dumps(process_def.get("taskDefinitionJson", [])),
                "taskRelationJson": json.dumps(process_def.get("taskRelationJson", [])),
                "executionType": process_def.get("executionType", "PARALLEL"),
            }
            return self._http(
                "POST",
                f"/projects/{project_code}/process-definition",
                create_body,
            )
        else:
            # Update
            code = existing["code"]
            update_body = {
                "name": process_name,
                "description": process_def.get("description", ""),
                "globalParams": process_def.get("globalParams", []),
                "locations": process_def.get("locations", ""),
                "timeout": process_def.get("timeout", 0),
                "taskDefinitionJson": json.dumps(process_def.get("taskDefinitionJson", [])),
                "taskRelationJson": json.dumps(process_def.get("taskRelationJson", [])),
                "executionType": process_def.get("executionType", "PARALLEL"),
            }
            return self._http(
                "PUT",
                f"/projects/{project_code}/process-definition/{code}",
                update_body,
            )

    def _release_process(self, payload: dict[str, Any], release_state: str) -> dict[str, Any]:
        """Online or offline a process definition."""
        project_name: str = payload["projectName"]
        process_name: str = payload["processName"]

        proj = self._resolve_project_code(project_name)
        if proj is None:
            return {"code": -1, "msg": f"Project not found: {project_name}", "success": False}

        proc = self._find_process_by_name(proj["code"], process_name)
        if proc is None:
            return {"code": -1, "msg": f"Process not found: {process_name}", "success": False}

        release_body = {
            "name": process_name,
            "releaseState": release_state,
            "processDefinitionCode": proc["code"],
        }
        return self._http(
            "POST",
            f"/projects/{proj['code']}/process-definition/{proc['code']}/release",
            release_body,
        )

    def _set_schedule(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create or update a schedule for a process definition."""
        project_name: str = payload["projectName"]
        process_name: str = payload["processName"]
        cron: str = payload["cron"]

        proj = self._resolve_project_code(project_name)
        if proj is None:
            return {"code": -1, "msg": f"Project not found: {project_name}", "success": False}

        proc = self._find_process_by_name(proj["code"], process_name)
        if proc is None:
            return {"code": -1, "msg": f"Process not found: {process_name}", "success": False}

        # Check for existing schedule
        existing_sched = self._find_schedule(proj["code"], proc["code"])

        schedule_body = {
            "schedule": json.dumps({
                "startTime": "2026-01-01 00:00:00",
                "endTime": "2099-12-31 23:59:59",
                "crontab": cron,
                "timezoneId": "Asia/Shanghai",
            }),
            "failureStrategy": "CONTINUE",
            "warningType": "NONE",
            "processInstancePriority": "MEDIUM",
            "workerGroup": "default",
        }

        if existing_sched is None:
            schedule_body["processDefinitionCode"] = proc["code"]
            return self._http(
                "POST",
                f"/projects/{proj['code']}/schedules",
                schedule_body,
            )
        else:
            return self._http(
                "PUT",
                f"/projects/{proj['code']}/schedules/{existing_sched['id']}",
                schedule_body,
            )

    def _query_instance_state(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Query the state of the latest process instance."""
        project_name: str = payload["projectName"]
        process_name: str = payload["processName"]

        proj = self._resolve_project_code(project_name)
        if proj is None:
            return {"code": -1, "msg": f"Project not found: {project_name}", "success": False}

        proc = self._find_process_by_name(proj["code"], process_name)
        if proc is None:
            return {"code": -1, "msg": f"Process not found: {process_name}", "success": False}

        return self._http(
            "GET",
            f"/projects/{proj['code']}/process-instances"
            f"?processDefineCode={proc['code']}"
            f"&pageNo=1&pageSize=1",
        )

    # ------------------------------------------------------------------
    # Lookup helpers
    # ------------------------------------------------------------------

    def _resolve_project_code(self, project_name: str) -> dict[str, Any] | None:
        """Find a project by name and return its {code, name} dict, or None."""
        resp = self._http("GET", "/projects/list?pageNo=1&pageSize=200")
        if not isinstance(resp, dict):
            return None
        data = resp.get("data") or []
        # data might be a list (DS 3.x) or dict with totalList
        if isinstance(data, dict):
            data = data.get("totalList", [])
        for p in data:
            if isinstance(p, dict) and p.get("name") == project_name:
                return {"code": p["code"], "name": p["name"]}
        return None

    def _find_process_by_name(self, project_code: int, process_name: str) -> dict[str, Any] | None:
        """Find a process definition by name within a project."""
        resp = self._http(
            "GET",
            f"/projects/{project_code}/process-definition/list"
            f"?searchVal={process_name}&pageNo=1&pageSize=50",
        )
        if not isinstance(resp, dict):
            return None
        data = resp.get("data") or []
        if isinstance(data, dict):
            data = data.get("totalList", [])
        for p in data:
            if isinstance(p, dict) and p.get("name") == process_name:
                return p
        return None

    def _find_schedule(self, project_code: int, process_code: int) -> dict[str, Any] | None:
        """Find an existing schedule for a process definition."""
        resp = self._http(
            "GET",
            f"/projects/{project_code}/schedules"
            f"?processDefinitionCode={process_code}&pageNo=1&pageSize=10",
        )
        if not isinstance(resp, dict):
            return None
        data = resp.get("data") or []
        if isinstance(data, dict):
            data = data.get("totalList", [])
        return data[0] if data else None

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    def login(self, username: str, password: str) -> dict[str, Any]:
        """Login to DS and store the session token.

        DS 3.x expects userName/userPassword as query parameters, not JSON body.
        """
        resp = self._http(
            "POST",
            f"/login?userName={username}&userPassword={password}",
        )
        if isinstance(resp, dict) and resp.get("success") and resp.get("data"):
            data = resp["data"]
            # DS 3.x returns sessionId
            self.token = data.get("sessionId", "")
        return resp

    @property
    def is_authenticated(self) -> bool:
        """Check if the current token is valid."""
        if not self.token:
            return False
        resp = self._http("GET", "/users/get-user-info")
        return isinstance(resp, dict) and resp.get("success", False)

    # ------------------------------------------------------------------
    # Public API (backward-compatible)
    # ------------------------------------------------------------------

    def create_project(self, project_name: str, description: str = "") -> dict[str, Any]:
        return self._request(
            "create_project",
            {"projectName": project_name, "description": description},
        )

    def create_or_update_process(
        self, project_name: str, process_definition: dict[str, Any]
    ) -> dict[str, Any]:
        return self._request(
            "create_or_update_process",
            {"projectName": project_name, "processDefinition": process_definition},
        )

    def online_process(self, project_name: str, process_name: str) -> dict[str, Any]:
        return self._request(
            "online_process",
            {"projectName": project_name, "processName": process_name},
        )

    def offline_process(self, project_name: str, process_name: str) -> dict[str, Any]:
        """Offline (unpublish) a process definition. New in real-client mode."""
        return self._request(
            "offline_process",
            {"projectName": project_name, "processName": process_name},
        )

    def set_schedule(self, project_name: str, process_name: str, cron: str) -> dict[str, Any]:
        return self._request(
            "set_schedule",
            {"projectName": project_name, "processName": process_name, "cron": cron},
        )

    def query_instance_state(self, project_name: str, process_name: str) -> dict[str, Any]:
        return self._request(
            "query_instance_state",
            {"projectName": project_name, "processName": process_name},
        )
