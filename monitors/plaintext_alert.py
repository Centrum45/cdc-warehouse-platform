from __future__ import annotations

import json
from pathlib import Path


def append_alert(alert_path: str | Path, database: str, table: str, columns: list[str], ts: int) -> None:
    path = Path(alert_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "database": database,
        "table": table,
        "columns": columns,
        "ts": ts,
        "notify_target": "DBA"
    }
    with path.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        fp.write("\n")
