from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from realtime.impala.bootstrap import bootstrap_realtime, load_statements, split_sql
from realtime.kudu.kudu_client import KuduClient
from streaming.realtime_sink.kafka_to_kudu import upsert_rows


class FakeKuduClient:
    is_available = True

    def __init__(self, fail_on: str | None = None) -> None:
        self.fail_on = fail_on
        self.statements: list[str] = []

    def execute(self, sql: str) -> dict[str, object]:
        self.statements.append(sql)
        if self.fail_on and self.fail_on in sql:
            return {"success": False, "msg": "planned failure"}
        return {"success": True, "sql": sql[:120]}


def write_topic(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    event = {
        "database": "basiccomment",
        "table": "avatar_commentbatchsource",
        "type": "insert",
        "ts": 100,
        "data": {
            "id": 1,
            "batchnumber": "B1",
            "batchtype": "normal",
            "ctime": "2026-07-06 10:00:00",
            "utime": "2026-07-06 10:00:00",
            "ver": 1,
        },
    }
    path.write_text(json.dumps(event) + "\n", encoding="utf-8")


class RealtimeKuduImpalaTest(unittest.TestCase):
    def test_split_sql(self) -> None:
        self.assertEqual(split_sql("-- c\ncreate database x;\n\nselect 1;"), ["create database x", "select 1"])

    def test_load_statements_has_kudu_tables_and_views(self) -> None:
        sql = "\n".join(statement for _, statement in load_statements())
        self.assertIn("stored as kudu", sql.lower())
        self.assertIn("v_realtime_comment_analysis", sql)

    def test_bootstrap_realtime_dry_run(self) -> None:
        result = bootstrap_realtime(client=FakeKuduClient(), dry_run=True)
        sql = "\n".join(item["sql"] for item in result)
        self.assertIn("CREATE DATABASE IF NOT EXISTS realtime", sql)
        self.assertIn("realtime.avatar_commentbatchsource", sql)

    def test_bootstrap_realtime_stops_on_failure(self) -> None:
        client = FakeKuduClient(fail_on="avatar_commentbatchsource")
        result = bootstrap_realtime(client=client)
        self.assertFalse(result[-1]["success"])

    def test_kudu_client_missing_columns(self) -> None:
        client = KuduClient()
        result = client.upsert_rows("realtime", "t", [{"id": 1}, {"name": "bad"}])
        self.assertFalse(result["success"])
        self.assertIn("missing columns", result["msg"])

    def test_real_kudu_failure_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            topic = Path(tmp) / "topic.jsonl"
            write_topic(topic)
            with patch("realtime.kudu.kudu_client.KuduClient.upsert_rows", return_value={"success": False, "msg": "boom"}):
                with patch("realtime.kudu.kudu_client.KuduClient.is_available", new_callable=lambda: property(lambda self: True)):
                    with self.assertRaises(RuntimeError):
                        upsert_rows(topic, Path(tmp) / "kudu", Path(tmp) / "ckpt.json", use_real_kudu=True)


if __name__ == "__main__":
    unittest.main()
