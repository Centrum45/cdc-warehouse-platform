from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from storage.local_lake import LocalLake
from storage.hdfs_web import WebHdfsLake, is_hdfs_root
from streaming.common.binlog_parser import parse_maxwell_event
from streaming.common.checkpoint import FileCheckpoint
from streaming.common.sensitive_masker import load_rules, mask_event
from warehouse.jobs.delay_gate import write_progress


def run_micro_batch(
    topic_file: Path,
    lake_root: str | Path,
    checkpoint_path: Path,
    rules_path: Path | None,
    progress_root: Path
) -> list[object]:
    topic = topic_file.stem
    checkpoint = FileCheckpoint(checkpoint_path)
    start_offset = checkpoint.load_offset(topic)
    lines = topic_file.read_text(encoding="utf-8").splitlines()
    batch_lines = lines[start_offset:]
    rules = load_rules(rules_path) if rules_path else None
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)

    for line in batch_lines:
        event = parse_maxwell_event(line)
        raw = {
            "database": event.database,
            "table": event.table,
            "type": event.event_type,
            "ts": event.ts,
            "xid": event.xid,
            "data": event.data,
            "old": event.old
        }
        if rules:
            raw, _ = mask_event(raw, rules)
            event = parse_maxwell_event(raw)
        grouped[(event.database, event.table, event.business_dt)].append({"content": raw})
        write_progress(progress_root, event.database, event.table, event.ts, event.business_dt)

    lake = WebHdfsLake(str(lake_root)) if is_hdfs_root(lake_root) else LocalLake(lake_root)
    written: list[object] = []
    for (database, table, dt), rows in grouped.items():
        output = lake.binlog_partition(database, table, dt) / "part-00000.jsonl"
        existing = lake.read_jsonl(output)
        lake.write_jsonl(output, existing + rows)
        written.append(output)

    checkpoint.save_offset(topic, len(lines))
    return written


def main() -> None:
    topic_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/kafka/cdc.incremental.binlog.jsonl")
    lake_root = sys.argv[2] if len(sys.argv) > 2 else "data/lake"
    checkpoint_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("data/checkpoints/offline_sink.json")
    rules_path = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("metadata/rules/sensitive_columns.json")
    progress_root = Path(sys.argv[5]) if len(sys.argv) > 5 else Path("data/progress")
    for path in run_micro_batch(topic_file, lake_root, checkpoint_path, rules_path, progress_root):
        print(path)


if __name__ == "__main__":
    main()
