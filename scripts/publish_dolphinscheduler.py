from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from warehouse.scheduler.dolphinscheduler.ds_api_client import DolphinSchedulerClient


def main() -> None:
    process_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("warehouse/scheduler/dolphinscheduler/warehouse_daily_process.json")
    process = json.loads(process_path.read_text(encoding="utf-8"))
    client = DolphinSchedulerClient("http://localhost:12345/dolphinscheduler")
    project = process["projectName"]
    process_name = process["processDefinitionName"]
    print(client.create_project(project, "CDC warehouse demo project"))
    print(client.create_or_update_process(project, process))
    print(client.online_process(project, process_name))
    print(client.set_schedule(project, process_name, process["schedule"]))


if __name__ == "__main__":
    main()
