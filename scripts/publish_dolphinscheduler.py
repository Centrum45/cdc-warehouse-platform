"""
Publish the CDC warehouse daily process to DolphinScheduler.

Modes:
  --audit       Publish to DS audit files (offline review)
  --live        Publish to a live DS instance (requires DS config)
  --dry-run     Print the process definition JSON without publishing
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from warehouse.scheduler.dolphinscheduler.ds_api_client import DolphinSchedulerClient


def _load_config() -> dict[str, Any]:
    try:
        from configs.loader import load_config
        return load_config()
    except Exception:
        return {}


def build_process_definition(process: dict) -> dict[str, Any]:
    """Convert high-level process JSON to DS OpenAPI process definition format.

    Returns a dict with 'projectName' and 'processDefinition' keys.
    """
    tasks = process["tasks"]
    dependencies = process["dependencies"]

    # Build task code mapping
    task_codes: dict[str, int] = {}
    for i, t in enumerate(tasks):
        task_codes[t["name"]] = i + 1

    # Build DS task definitions
    task_defs = []
    for t in tasks:
        code = task_codes[t["name"]]
        task_defs.append({
            "code": code,
            "name": t["name"],
            "description": t.get("description", ""),
            "taskType": t["type"],
            "taskParams": {
                "localParams": [],
                "rawScript": t["command"],
                "resourceList": [],
            },
            "flag": "YES",
            "taskPriority": "MEDIUM",
            "workerGroup": "default",
            "failRetryTimes": 2,
            "failRetryInterval": 5,
            "delayTime": 0,
            "timeoutFlag": "CLOSE",
            "timeout": 0,
        })

    # Build task relations
    task_relations = []
    for dep in dependencies:
        upstream_name, downstream_name = dep[0], dep[1]
        task_relations.append({
            "name": f"{upstream_name} -> {downstream_name}",
            "preTaskCode": task_codes[upstream_name],
            "preTaskVersion": 1,
            "postTaskCode": task_codes[downstream_name],
            "postTaskVersion": 1,
            "conditionType": "NONE",
            "conditionParams": {},
        })

    return {
        "projectName": process["projectName"],
        "processDefinition": {
            "name": process["processDefinitionName"],
            "description": process.get("description", ""),
            "globalParams": [
                {"prop": "biz_dt", "value": "${system.biz.curdate}",
                 "type": "VARCHAR", "direct": "IN"},
            ],
            "locations": "",
            "timeout": 0,
            "executionType": "PARALLEL",
            "taskDefinitionJson": task_defs,
            "taskRelationJson": task_relations,
        },
    }


def main() -> None:
    args = set(sys.argv[1:])
    process_path = ROOT / "warehouse/scheduler/dolphinscheduler/warehouse_daily_process.json"
    process = json.loads(process_path.read_text(encoding="utf-8"))

    if "--dry-run" in args or "-d" in args:
        ds_def = build_process_definition(process)
        print(json.dumps(ds_def, ensure_ascii=False, indent=2))
        return

    cfg = _load_config()
    ds_cfg = cfg.get("dolphinscheduler", {})
    audit_mode = "--audit" in args or ds_cfg.get("audit_mode", True)

    client = DolphinSchedulerClient(
        endpoint=ds_cfg.get("endpoint", "http://localhost:12345/dolphinscheduler"),
        token=ds_cfg.get("token", ""),
        audit_mode=audit_mode,
        audit_dir=ds_cfg.get("audit_dir", "data/dolphinscheduler/audit"),
    )

    # Auto-login for live mode
    if not audit_mode:
        username = ds_cfg.get("username", "admin")
        password = ds_cfg.get("password", "dolphinscheduler123")
        login_resp = client.login(username, password)
        if login_resp.get("success"):
            print(f"  Logged in as {username}")
        else:
            print(f"  Login failed: {login_resp.get('msg', 'unknown error')}")

    project_name = process["projectName"]
    process_name = process["processDefinitionName"]
    cron_expr = process["schedule"]

    mode_label = "AUDIT" if audit_mode else "LIVE"
    print(f"\nPublishing to DolphinScheduler [{mode_label}]")
    print(f"  Project : {project_name}")
    print(f"  Process : {process_name}")
    print(f"  Schedule: {cron_expr}")
    print(f"  Tasks   : {len(process['tasks'])} tasks, {len(process['dependencies'])} dependencies\n")

    # Step 1: create project
    r1 = client.create_project(project_name, "CDC warehouse demo project")
    print(f"[1/4] create project  : {_fmt_result(r1)}")

    # Step 2: create/update process with full DS definition
    ds_def = build_process_definition(process)
    r2 = client.create_or_update_process(project_name, ds_def["processDefinition"])
    print(f"[2/4] upsert process  : {_fmt_result(r2)}")

    # Step 3: online
    r3 = client.online_process(project_name, process_name)
    print(f"[3/4] online process  : {_fmt_result(r3)}")

    # Step 4: set schedule
    r4 = client.set_schedule(project_name, process_name, cron_expr)
    print(f"[4/4] set schedule    : {_fmt_result(r4)}")

    if audit_mode:
        audit_dir = ds_cfg.get("audit_dir", "data/dolphinscheduler/audit")
        print(f"\nAudit files written to: {audit_dir}/")
        print("Review them, then publish with: --live")


def _fmt_result(r: dict) -> str:
    """Format a DS API result for display."""
    if isinstance(r, dict):
        if r.get("success") is False:
            return f"FAILED - {r.get('msg', str(r))[:80]}"
        if r.get("status") == "OK":
            return f"OK (audit: {r.get('audit_file', '')})"
        code = r.get("code", -1)
        return f"OK (code={code})" if code == 0 or code == 200 else f"code={code} - {r.get('msg', str(r))[:80]}"
    return str(r)


if __name__ == "__main__":
    main()
