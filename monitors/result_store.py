from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any


RESULT_COLUMNS = ["created_at", "monitor_type", "database", "table", "status", "message", "metric_value"]


class MonitorResultStore:
    def __init__(self, path: str | Path = "data/monitor/monitor_result.csv") -> None:
        self.path = Path(path)

    def append(self, monitor_type: str, database: str, table: str, status: str, message: str, metric_value: Any = "") -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        exists = self.path.exists()
        with self.path.open("a", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=RESULT_COLUMNS)
            if not exists:
                writer.writeheader()
            writer.writerow({
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "monitor_type": monitor_type,
                "database": database,
                "table": table,
                "status": status,
                "message": message,
                "metric_value": metric_value
            })

    def read_all(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8", newline="") as fp:
            return list(csv.DictReader(fp))
