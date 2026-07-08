from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from monitors.field_alter_sql import build_add_columns_sql
from streaming.common.sensitive_masker import mask_event
from warehouse.jobs.delay_gate import can_merge, write_progress


class IngestionControlTest(unittest.TestCase):
    def test_sensitive_masker_md5(self) -> None:
        event = {"data": {"email": "user@example.com", "name": "alice"}}
        rules = {"default_action": "md5", "columns": {"email": {"action": "md5"}}}
        masked, hits = mask_event(event, rules)
        self.assertEqual(hits, ["email"])
        self.assertNotEqual(masked["data"]["email"], "user@example.com")

    def test_delay_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            write_progress(tmp, "db", "tbl", int(time.time()), "2026-07-06")
            allowed, reason = can_merge(Path(tmp), "db", "tbl", 60)
            self.assertTrue(allowed, reason)

    def test_field_alter_sql(self) -> None:
        sql = build_add_columns_sql("ods", "ods_order_dic", [{"name": "source_channel", "type": "string"}])
        self.assertEqual(sql, ["alter table ods.ods_order_dic add columns (source_channel string);"])


if __name__ == "__main__":
    unittest.main()
