from __future__ import annotations

import json
from pathlib import Path

from replay.replay_plan import ReplayPlan


def load_events(source_topic_file: Path, plan: ReplayPlan) -> list[dict]:
    events = []
    with source_topic_file.open("r", encoding="utf-8") as fp:
        for line in fp:
            if not line.strip():
                continue
            event = json.loads(line)
            event_time = event.get("data", {}).get("utime") or event.get("data", {}).get("ctime", "")
            if event["database"] == plan.database and event["table"] == plan.table and plan.start_time <= event_time < plan.end_time:
                events.append(event)
    return events


def run_replay(source_topic_file: Path, target_topic_file: Path, plan: ReplayPlan) -> int:
    events = load_events(source_topic_file, plan)
    target_topic_file.parent.mkdir(parents=True, exist_ok=True)
    with target_topic_file.open("a", encoding="utf-8") as fp:
        for event in events:
            event["_replay"] = True
            fp.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
            fp.write("\n")
    return len(events)
