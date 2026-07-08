from __future__ import annotations

import time


def event_delay_seconds(event_ts: int, now_ts: int | None = None) -> int:
    current = int(now_ts if now_ts is not None else time.time())
    return max(0, current - int(event_ts))


def is_delayed(event_ts: int, threshold_seconds: int, now_ts: int | None = None) -> bool:
    return event_delay_seconds(event_ts, now_ts) > threshold_seconds

