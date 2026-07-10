from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from streaming.common.maxwell_event import MaxwellEvent

# Dead-letter queue root. Bad events land here grouped by topic.
DLQ_ROOT = Path(os.environ.get("DLQ_ROOT", "data/dead_letter"))


def _write_dlq(topic: str, raw_line: str, error: str) -> None:
    """Write an unparseable event to the dead-letter queue."""
    dlq_path = DLQ_ROOT / topic
    dlq_path.mkdir(parents=True, exist_ok=True)
    record = {
        "received_at": datetime.now().isoformat(),
        "error": error,
        "raw_payload": raw_line.strip(),
    }
    # Append to daily DLQ file
    day = datetime.now().strftime("%Y-%m-%d")
    dlq_file = dlq_path / f"dlq-{day}.jsonl"
    with open(dlq_file, "a", encoding="utf-8") as fp:
        fp.write(json.dumps(record, ensure_ascii=False))
        fp.write("\n")


def parse_maxwell_event(payload: str | dict[str, Any]) -> MaxwellEvent:
    """Parse a single Maxwell binlog event.

    Raises KeyError / TypeError / json.JSONDecodeError on malformed input.
    Callers should catch these and route to the dead-letter queue.
    """
    raw = json.loads(payload) if isinstance(payload, str) else payload
    return MaxwellEvent(
        database=raw["database"],
        table=raw["table"],
        event_type=raw["type"],
        ts=int(raw["ts"]),
        xid=raw.get("xid"),
        data=dict(raw.get("data", {})),
        old=dict(raw.get("old", {})),
    )


def parse_maxwell_event_safe(
    payload: str | dict[str, Any],
    topic: str = "unknown",
) -> MaxwellEvent | None:
    """Parse a Maxwell event, routing failures to the dead-letter queue.

    Returns None if the event cannot be parsed (already written to DLQ).
    """
    try:
        return parse_maxwell_event(payload)
    except (KeyError, TypeError, json.JSONDecodeError, ValueError) as exc:
        raw_line = payload if isinstance(payload, str) else json.dumps(payload)
        _write_dlq(topic, raw_line, f"{type(exc).__name__}: {exc}")
        return None


def parse_topic_file(path, skip_bad: bool = True) -> list[MaxwellEvent]:
    """Parse a JSONL topic file. Bad events go to DLQ when skip_bad=True."""
    topic = Path(path).stem
    events: list[MaxwellEvent] = []
    with open(path, "r", encoding="utf-8") as fp:
        for line in fp:
            if not line.strip():
                continue
            if skip_bad:
                event = parse_maxwell_event_safe(line, topic)
                if event is not None:
                    events.append(event)
            else:
                events.append(parse_maxwell_event(line))
    return events
