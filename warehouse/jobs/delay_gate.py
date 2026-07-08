from __future__ import annotations

import json
import time
from pathlib import Path


def progress_path(progress_root: str | Path, database: str, table: str) -> Path:
    return Path(progress_root) / f"{database}.{table}.json"


def write_progress(progress_root: str | Path, database: str, table: str, latest_event_ts: int, partition_dt: str) -> Path:
    path = progress_path(progress_root, database, table)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "database": database,
        "table": table,
        "latest_event_ts": latest_event_ts,
        "partition_dt": partition_dt,
        "updated_at": int(time.time())
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return path


def can_merge(progress_root: str | Path, database: str, table: str, max_delay_seconds: int, now_ts: int | None = None) -> tuple[bool, str]:
    path = progress_path(progress_root, database, table)
    if not path.exists():
        return False, f"missing progress: {path}"
    payload = json.loads(path.read_text(encoding="utf-8"))
    current_ts = int(now_ts if now_ts is not None else time.time())
    delay = current_ts - int(payload["latest_event_ts"])
    if delay > max_delay_seconds:
        return False, f"delay {delay}s > threshold {max_delay_seconds}s"
    return True, f"delay {delay}s <= threshold {max_delay_seconds}s"
