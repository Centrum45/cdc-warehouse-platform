from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from admin_platform.onboarding.table_onboarding import build_table_metadata, onboard_table


DBA_METADATA = {
    "source_database": "sales",
    "source_table": "order_info",
    "columns": [
        {"name": "id", "type": "bigint"},
        {"name": "amount", "type": "double"},
        {"name": "ctime", "type": "string"},
        {"name": "utime", "type": "string"},
        {"name": "ver", "type": "int"}
    ]
}


class TableOnboardingTest(unittest.TestCase):
    def test_build_metadata(self) -> None:
        metadata = build_table_metadata(DBA_METADATA, ["id"], "ver", "ctime")
        self.assertEqual(metadata["ods_table"], "ods_sales_order_info_dic")
        self.assertEqual(metadata["ods_binlog_table"], "ods_binlog_sales_order_info_di")

    def test_onboard_table_outputs_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dba_path = root / "dba.json"
            dba_path.write_text(json.dumps(DBA_METADATA), encoding="utf-8")
            outputs = onboard_table(dba_path, root, ["id"], "ver", "ctime")
            for path in outputs.values():
                self.assertTrue(path.exists(), path)
            self.assertIn("create external table", outputs["ods_ddl"].read_text(encoding="utf-8"))
            self.assertIn("row_number()", outputs["merge_sql"].read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
