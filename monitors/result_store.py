from __future__ import annotations

import csv
import os
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
        self._append_mysql(monitor_type, database, table, status, message, metric_value)

    def read_all(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        with self.path.open("r", encoding="utf-8", newline="") as fp:
            return list(csv.DictReader(fp))

    def _append_mysql(
        self,
        monitor_type: str,
        database: str,
        table: str,
        status: str,
        message: str,
        metric_value: Any,
    ) -> None:
        host = os.environ.get("MONITOR_DB_HOST") or os.environ.get("DB_HOST")
        if not host:
            return
        try:
            import pymysql

            connection = pymysql.connect(
                host=host,
                port=int(os.environ.get("MONITOR_DB_PORT", os.environ.get("DB_PORT", "3306"))),
                user=os.environ.get("MONITOR_DB_USER", os.environ.get("DB_USER", "root")),
                password=os.environ.get("MONITOR_DB_PASSWORD", os.environ.get("DB_PASSWORD", "")),
                database=os.environ.get("MONITOR_DB_NAME", os.environ.get("DB_NAME", "cdc_warehouse_admin")),
                charset="utf8mb4",
                connect_timeout=5,
            )
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "insert into monitor_result "
                        "(monitor_type, source_database, source_table, status, message, metric_value) "
                        "values (%s, %s, %s, %s, %s, %s)",
                        (monitor_type, database, table, status, message, str(metric_value)),
                    )
                connection.commit()
            finally:
                connection.close()
        except Exception as exc:
            print(f"[monitor] MySQL result write failed: {exc}")
