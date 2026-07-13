from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from monitors.special_value_sql_builder import build_not_null_sql, build_special_value_sql
from replay.replay_plan import ReplayPlan
from replay.replay_runner import run_replay
from streaming.common.binlog_parser import parse_maxwell_event
from streaming.common.checkpoint import FileCheckpoint


EVENTS = [
    {
        "database": "basiccomment",
        "table": "avatar_commentbatchsource",
        "type": "insert",
        "ts": 100,
        "xid": 1,
        "data": {
            "id": 1,
            "batchnumber": "B1",
            "batchtype": "normal",
            "ctime": "2026-07-06 10:00:00",
            "utime": "2026-07-06 10:00:00",
            "ver": 1
        }
    },
    {
        "database": "basiccomment",
        "table": "avatar_commentbatchsource",
        "type": "delete",
        "ts": 101,
        "xid": 2,
        "data": {
            "id": 1,
            "batchnumber": "B1",
            "batchtype": "normal",
            "ctime": "2026-07-06 10:00:00",
            "utime": "2026-07-06 11:00:00",
            "ver": 2
        }
    }
]


def write_topic(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fp:
        for event in EVENTS:
            fp.write(json.dumps(event))
            fp.write("\n")


class StreamingReplayTest(unittest.TestCase):
    def test_parser(self) -> None:
        event = parse_maxwell_event(EVENTS[0])
        self.assertEqual(event.qualified_table, "basiccomment.avatar_commentbatchsource")
        self.assertEqual(event.business_dt, "2026-07-06")

    def test_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint = FileCheckpoint(Path(tmp) / "offset.json")
            checkpoint.save_offset("topic", 3)
            self.assertEqual(checkpoint.load_offset("topic"), 3)

    def test_replay_runner(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source.jsonl"
            target = Path(tmp) / "target.jsonl"
            write_topic(source)
            plan = ReplayPlan("basiccomment", "avatar_commentbatchsource", "2026-07-06 00:00:00", "2026-07-07 00:00:00", "replay")
            self.assertEqual(run_replay(source, target, plan), 2)

    def test_special_value_sql(self) -> None:
        sql = build_not_null_sql("dwd.table", ["id"], "2026-07-06")
        self.assertIn("id is null", sql)
        self.assertIn("batchtype in ('unknown')", build_special_value_sql("dwd.table", {"batchtype": ["unknown"]}, "2026-07-06")[0])


if __name__ == "__main__":
    unittest.main()
