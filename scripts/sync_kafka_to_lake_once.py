from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from streaming.offline_sink.kafka_to_local_lake import sink_events
from warehouse.jobs.delay_gate import progress_path


def latest_synced_ts(progress_root: Path, database: str, table: str) -> int:
    path = progress_path(progress_root, database, table)
    if not path.exists():
        return -1
    payload = json.loads(path.read_text(encoding="utf-8"))
    return int(payload.get("latest_event_ts", -1))


def filter_new_events(topic_file: Path, progress_root: Path, output_file: Path) -> int:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    kept = 0
    with topic_file.open("r", encoding="utf-8") as src, output_file.open("w", encoding="utf-8") as dst:
        for line in src:
            if not line.strip():
                continue
            event = json.loads(line)
            database = event["database"]
            table = event["table"]
            event_ts = int(event["ts"])
            if event_ts <= latest_synced_ts(progress_root, database, table):
                continue
            dst.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
            kept += 1
    return kept


def main() -> None:
    parser = argparse.ArgumentParser(description="Sink only new Kafka CDC events into local lake once.")
    parser.add_argument("--topic-file", default="data/kafka/cdc.incremental.binlog.jsonl")
    parser.add_argument("--lake-root", default="data/lake")
    parser.add_argument("--rules", default="metadata/rules/sensitive_columns.json")
    parser.add_argument("--progress-root", default="data/progress")
    parser.add_argument("--filtered-file", default="data/kafka/cdc.incremental.binlog.new.jsonl")
    args = parser.parse_args()

    topic_file = Path(args.topic_file)
    progress_root = Path(args.progress_root)
    filtered_file = Path(args.filtered_file)
    kept = filter_new_events(topic_file, progress_root, filtered_file)
    if kept == 0:
        print("no new events")
        return

    written = sink_events(filtered_file, Path(args.lake_root), Path(args.rules), progress_root)
    print(f"new events: {kept}")
    for path in written:
        print(path)


if __name__ == "__main__":
    main()
