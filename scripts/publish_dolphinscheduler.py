from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from configs.loader import load_config
from warehouse.scheduler.dolphinscheduler.ds_api_client import DolphinSchedulerClient


def main() -> None:
    cfg = load_config()
    ds_cfg = cfg.get("dolphinscheduler", {})

    process_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else ROOT / "warehouse/scheduler/dolphinscheduler/warehouse_daily_process.json"
    )

    process = json.loads(process_path.read_text(encoding="utf-8"))
    project_name = process["projectName"]
    process_name = process["processDefinitionName"]
    cron_expr = process["schedule"]

    client = DolphinSchedulerClient(
        endpoint=ds_cfg.get("endpoint", "http://localhost:12345/dolphinscheduler"),
        token=ds_cfg.get("token", ""),
        audit_mode=ds_cfg.get("audit_mode", False),
        audit_dir=ds_cfg.get("audit_dir", "data/dolphinscheduler/audit"),
    )

    print("[1/4] create project  :", client.create_project(project_name, "CDC warehouse demo project"))
    print("[2/4] upsert process  :", client.create_or_update_process(project_name, process))
    print("[3/4] online process  :", client.online_process(project_name, process_name))
    print("[4/4] set schedule    :", client.set_schedule(project_name, process_name, cron_expr))


if __name__ == "__main__":
    main()
