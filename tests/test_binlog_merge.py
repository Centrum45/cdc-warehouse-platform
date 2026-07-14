from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path

from scripts.spark_sql_ods_merge_daily import binlog_partitions, run_daily_merge
from warehouse.storage.binlog_parquet import event_to_binlog_row, write_local_parquet as write_binlog_parquet
from warehouse.storage.parquet_table import read_local_parquet
from warehouse.jobs.merge_ods_snapshot import merge_rows


METADATA = {
    "primary_keys": ["id"],
    "version_column": "ver",
    "columns": [
        {"name": "id", "type": "bigint"},
        {"name": "batchnumber", "type": "string"},
        {"name": "batchtype", "type": "string"},
        {"name": "ctime", "type": "string"},
        {"name": "utime", "type": "string"},
        {"name": "ver", "type": "int"}
    ]
}


class BinlogMergeTest(unittest.TestCase):
    def test_update_wins_over_old_snapshot(self) -> None:
        old_rows = [
            {"id": "1", "batchnumber": "B1", "batchtype": "normal", "ctime": "2026-07-06 09:00:00", "utime": "2026-07-06 09:00:00", "ver": "1", "dt": "2026-07-06"}
        ]
        binlog_rows = [
            {"binlog_type": 2, "id": "1", "batchnumber": "B1", "batchtype": "priority", "ctime": "2026-07-06 09:00:00", "utime": "2026-07-06 10:00:00", "ver": 2, "dt": "2026-07-06"}
        ]
        result = merge_rows(binlog_rows, old_rows, METADATA)
        self.assertEqual(result[0]["batchtype"], "priority")

    def test_delete_removes_latest_row(self) -> None:
        old_rows = [
            {"id": "1", "batchnumber": "B1", "batchtype": "normal", "ctime": "2026-07-06 09:00:00", "utime": "2026-07-06 09:00:00", "ver": "1", "dt": "2026-07-06"}
        ]
        binlog_rows = [
            {"binlog_type": 3, "id": "1", "batchnumber": "B1", "batchtype": "normal", "ctime": "2026-07-06 09:00:00", "utime": "2026-07-06 11:00:00", "ver": 2, "dt": "2026-07-06"}
        ]
        self.assertEqual(merge_rows(binlog_rows, old_rows, METADATA), [])

    def test_daily_merge_runs_local_fallback_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_root = root / "metadata"
            metadata_root.mkdir()
            metadata_path = metadata_root / "basiccomment.avatar_commentbatchsource.json"
            metadata = dict(METADATA)
            metadata.update({
                "source_database": "basiccomment",
                "source_table": "avatar_commentbatchsource",
                "partition_column": "ctime",
            })
            metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

            binlog_dir = root / "lake/ods_binlog/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-06"
            binlog_file = binlog_dir / "part-00000.parquet"
            write_binlog_parquet(binlog_file, [event_to_binlog_row({
                "database": "basiccomment",
                "table": "avatar_commentbatchsource",
                "type": "insert",
                "ts": 100,
                "xid": 1,
                "data": {
                    "id": 1,
                    "batchnumber": "B1",
                    "batchtype": "normal",
                    "ctime": "2026-07-06 09:00:00",
                    "utime": "2026-07-06 09:00:00",
                    "ver": 1
                }
            })])

            partitions = binlog_partitions(metadata_path, root / "lake")
            self.assertEqual(partitions[0], "2026-07-06")

            progress_dir = root / "progress"
            progress_dir.mkdir()
            (progress_dir / "basiccomment.avatar_commentbatchsource.json").write_text(json.dumps({
                "database": "basiccomment",
                "table": "avatar_commentbatchsource",
                "latest_event_ts": 100,
                "partition_dt": "2026-07-06",
                "updated_at": 100
            }), encoding="utf-8")

            daily_messages = run_daily_merge(metadata_root, root / "lake", "2026-07-06", "local", root / "progress", 9999999999)
            self.assertEqual(len(daily_messages), 1)
            self.assertIn("dt=2026-07-06", daily_messages[0])
            output = root / "lake/ods/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-06/part-00000.parquet"
            self.assertEqual(read_local_parquet(output)[0]["batchnumber"], "B1")


if __name__ == "__main__":
    unittest.main()
