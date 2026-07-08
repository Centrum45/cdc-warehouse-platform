from __future__ import annotations

import json
from typing import Any

from streaming.common.maxwell_event import MaxwellEvent


def parse_maxwell_event(payload: str | dict[str, Any]) -> MaxwellEvent:
    raw = json.loads(payload) if isinstance(payload, str) else payload
    return MaxwellEvent(
        database=raw["database"],
        table=raw["table"],
        event_type=raw["type"],
        ts=int(raw["ts"]),
        xid=raw.get("xid"),
        data=dict(raw.get("data", {})),
        old=dict(raw.get("old", {}))
    )


def parse_topic_file(path) -> list[MaxwellEvent]:
    events: list[MaxwellEvent] = []
    with open(path, "r", encoding="utf-8") as fp:
        for line in fp:
            if line.strip():
                events.append(parse_maxwell_event(line))
    return events
