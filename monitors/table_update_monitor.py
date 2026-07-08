from __future__ import annotations

from datetime import datetime


def stale_minutes(latest_update_time: str, now: str) -> float:
    latest = datetime.strptime(latest_update_time, "%Y-%m-%d %H:%M:%S")
    current = datetime.strptime(now, "%Y-%m-%d %H:%M:%S")
    return (current - latest).total_seconds() / 60


def is_stale(latest_update_time: str, now: str, threshold_minutes: int) -> bool:
    return stale_minutes(latest_update_time, now) > threshold_minutes

