from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from streaming.common.binlog_parser import parse_topic_file
from streaming.common.checkpoint import FileCheckpoint


def upsert_rows(topic_file: Path, kudu_root: Path, checkpoint_path: Path) -> Path:
    topic = topic_file.stem
    checkpoint = FileCheckpoint(checkpoint_path)
    start_offset = checkpoint.load_offset(topic)
    events = parse_topic_file(topic_file)[start_offset:]
    table_path = kudu_root / "realtime.avatar_commentbatchsource.csv"
    table_path.parent.mkdir(parents=True, exist_ok=True)

    state: dict[str, dict[str, object]] = {}
    if table_path.exists():
        with table_path.open("r", encoding="utf-8", newline="") as fp:
            for row in csv.DictReader(fp):
                state[str(row["id"])] = row

    for event in events:
        key = str(event.data.get("id"))
        if event.is_delete:
            state.pop(key, None)
            continue
        state[key] = {
            "id": event.data.get("id"),
            "batchnumber": event.data.get("batchnumber"),
            "batchtype": event.data.get("batchtype"),
            "ctime": event.data.get("ctime"),
            "utime": event.data.get("utime"),
            "ver": event.data.get("ver"),
            "event_ts": event.ts
        }

    columns = ["id", "batchnumber", "batchtype", "ctime", "utime", "ver", "event_ts"]
    with table_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        for row in sorted(state.values(), key=lambda item: str(item["id"])):
            writer.writerow(row)

    checkpoint.save_offset(topic, start_offset + len(events))
    return table_path


def main() -> None:
    topic_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/kafka/cdc.incremental.binlog.jsonl")
    kudu_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/kudu")
    checkpoint_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("data/checkpoints/realtime_sink.json")
    print(upsert_rows(topic_file, kudu_root, checkpoint_path))


if __name__ == "__main__":
    main()
