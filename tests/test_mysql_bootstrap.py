from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ingestion.bootstrap.mysql_bootstrap import build_bootstrap_events, build_select_sql, rows_from_tsv, write_events
from scripts.bootstrap_mysql_table import append_ods_binlog
from storage.binlog_parquet import read_local_parquet, row_to_event


METADATA = {
    "source_database": "basiccomment",
    "source_table": "avatar_commentbatchsource",
    "primary_keys": ["id"],
    "partition_column": "ctime",
    "version_column": "ver",
    "columns": [
        {"name": "id", "type": "bigint"},
        {"name": "batchnumber", "type": "string"},
        {"name": "batchtype", "type": "string"},
        {"name": "ctime", "type": "string"},
        {"name": "utime", "type": "string"},
        {"name": "ver", "type": "int"},
        {"name": "source_channel", "type": "string"},
    ],
}


class MysqlBootstrapTest(unittest.TestCase):
    def test_build_select_sql(self) -> None:
        sql = build_select_sql(METADATA)
        self.assertIn("from `basiccomment`.`avatar_commentbatchsource`", sql)
        self.assertIn("order by `id`", sql)

    def test_rows_from_tsv_coerces_types(self) -> None:
        rows = rows_from_tsv("9001\tB1\tdocker\t2026-07-06 12:00:00\t2026-07-07 15:18:37\t1\tdocker\n", METADATA)
        self.assertEqual(rows[0]["id"], 9001)
        self.assertEqual(rows[0]["ver"], 1)
        self.assertEqual(rows[0]["source_channel"], "docker")

    def test_bootstrap_events_append_to_ods_binlog(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            metadata_path = root / "metadata.json"
            metadata_path.write_text(json.dumps(METADATA), encoding="utf-8")
            first_event = build_bootstrap_events(
                [
                    {
                        "id": 1,
                        "batchnumber": "B1",
                        "batchtype": "seed",
                        "ctime": "2026-07-06 09:00:00",
                        "utime": "2026-07-06 09:00:00",
                        "ver": 1,
                        "source_channel": "seed",
                    }
                ],
                METADATA,
                100,
            )
            second_event = build_bootstrap_events(
                [
                    {
                        "id": 2,
                        "batchnumber": "B2",
                        "batchtype": "seed",
                        "ctime": "2026-07-06 10:00:00",
                        "utime": "2026-07-06 10:00:00",
                        "ver": 1,
                        "source_channel": "seed",
                    }
                ],
                METADATA,
                101,
            )
            first_file = write_events(first_event, root / "first.jsonl")
            second_file = write_events(second_event, root / "second.jsonl")
            append_ods_binlog(metadata_path=metadata_path, lake_root=root / "lake", event_file=first_file, progress_root=None)
            written = append_ods_binlog(metadata_path=metadata_path, lake_root=root / "lake", event_file=second_file, progress_root=None)

            records = [row_to_event(row) for row in read_local_parquet(written[0])]
            self.assertEqual(len(records), 2)
            self.assertEqual(records[0]["type"], "bootstrap-insert")


if __name__ == "__main__":
    unittest.main()
