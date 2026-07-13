from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from monitors.notifier import Notifier
from monitors.result_store import MonitorResultStore
from warehouse.scheduler.dolphinscheduler.ds_api_client import DolphinSchedulerClient


class SchedulerMonitorStoreTest(unittest.TestCase):
    def test_dolphinscheduler_client_audit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            client = DolphinSchedulerClient("http://localhost", audit_mode=True, audit_dir=tmp)
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

    def test_notifier_default_channels_and_missing_webhook(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            outbox_path = Path(tmp) / "outbox.jsonl"
            with patch.dict("os.environ", {"ALERT_CHANNELS": "stdout,dingtalk", "ALERT_TARGET": "ops"}, clear=False):
                outbox = Notifier(outbox_path).send_default("title", "body")
            text = outbox.read_text(encoding="utf-8")
            self.assertIn('"channel": "file"', text)
            self.assertIn('"channel": "stdout"', text)
            self.assertIn('"channel": "dingtalk"', text)
            self.assertIn("no webhook url configured", text)


if __name__ == "__main__":
    unittest.main()
