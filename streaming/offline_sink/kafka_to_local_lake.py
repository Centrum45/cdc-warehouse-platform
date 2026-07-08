from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from storage.local_lake import LocalLake
from streaming.common.sensitive_masker import load_rules, mask_event
from warehouse.jobs.delay_gate import write_progress


def event_dt(event: dict) -> str:
    return str(event["data"]["ctime"])[:10]


def sink_events(
    topic_file: Path,
    lake_root: Path,
    rules_path: Path | None = None,
    progress_root: Path | None = None
) -> list[Path]:
    lake = LocalLake(lake_root)
    rules = load_rules(rules_path) if rules_path else None
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    with topic_file.open("r", encoding="utf-8") as fp:
        for line in fp:
            if not line.strip():
                continue
            event = json.loads(line)
            if rules:
                event, hits = mask_event(event, rules)
                if hits:
                    print(f"sensitive columns masked: {event['database']}.{event['table']} {hits}")
            dt = event_dt(event)
            grouped[(event["database"], event["table"], dt)].append({"content": event})
            if progress_root:
                write_progress(progress_root, event["database"], event["table"], int(event["ts"]), dt)

    written: list[Path] = []
    for (database, table, dt), rows in grouped.items():
        path = lake.binlog_partition(database, table, dt) / "part-00000.jsonl"
        lake.write_jsonl(path, lake.read_jsonl(path) + rows)
        written.append(path)
    return written


def main() -> None:
    topic_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/kafka/cdc.incremental.binlog.jsonl")
    lake_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/lake")
    rules_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    progress_root = Path(sys.argv[4]) if len(sys.argv) > 4 else None
    for path in sink_events(topic_file, lake_root, rules_path, progress_root):
        print(path)


if __name__ == "__main__":
    main()
