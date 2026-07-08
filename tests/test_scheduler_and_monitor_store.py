from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from monitors.notifier import Notifier
from monitors.result_store import MonitorResultStore
from warehouse.scheduler.dolphinscheduler.ds_api_client import DolphinSchedulerClient


class SchedulerMonitorStoreTest(unittest.TestCase):
    def test_dolphinscheduler_client_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = DolphinSchedulerClient("http://localhost", audit_dir=tmp)
            result = client.create_project("cdc_warehouse")
            self.assertEqual(result["status"], "OK")
            self.assertTrue((Path(tmp) / "create_project.json").exists())

    def test_monitor_result_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = MonitorResultStore(Path(tmp) / "result.csv")
            store.append("delay", "db", "tbl", "OK", "fresh", 1)
            rows = store.read_all()
            self.assertEqual(rows[0]["monitor_type"], "delay")

    def test_notifier(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox = Notifier(Path(tmp) / "outbox.jsonl").send("email", "dba@example.com", "title", "body")
            self.assertIn("dba@example.com", outbox.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
