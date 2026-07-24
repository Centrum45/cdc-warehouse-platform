from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

from monitors.field_alter_sql import build_add_columns_sql
from monitors.field_monitor_job import diff_schema
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

    def test_field_schema_diff_detects_all_change_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            platform = root / "platform.json"
            dba = root / "dba.json"
            platform.write_text(json.dumps({"columns": [{"name": "id", "type": "int"}, {"name": "old", "type": "string"}]}))
            dba.write_text(json.dumps({"columns": [{"name": "id", "type": "bigint"}, {"name": "new", "type": "string"}]}))
            changes = diff_schema(platform, dba)
            self.assertEqual([item["name"] for item in changes["added"]], ["new"])
            self.assertEqual([item["name"] for item in changes["removed"]], ["old"])
            self.assertEqual(changes["type_changed"][0]["name"], "id")


if __name__ == "__main__":
    unittest.main()
