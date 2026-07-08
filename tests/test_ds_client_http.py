from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from warehouse.scheduler.dolphinscheduler.ds_api_client import DolphinSchedulerClient


class DolphinSchedulerClientHTTPTest(unittest.TestCase):
    """Test DS API client HTTP path with mocked urllib."""

    def setUp(self):
        self.client = DolphinSchedulerClient(
            "http://ds:12345/dolphinscheduler",
            token="test-token",
            audit_mode=False,
        )

    def _mock_response(self, data: dict, code: int = 200):
        resp = MagicMock()
        resp.read.return_value = json.dumps(data).encode("utf-8")
        resp.__enter__.return_value = resp
        resp.status = code
        return resp

    @patch("urllib.request.urlopen")
    @patch("urllib.request.Request")
    def test_create_project_live(self, mock_req, mock_urlopen):
        mock_urlopen.return_value = self._mock_response({"code": 0, "msg": "success", "data": {"code": 1}})
        mock_req.return_value = MagicMock()

        result = self.client.create_project("test_project", "desc")
        self.assertEqual(result["code"], 0)

    @patch("urllib.request.urlopen")
    def test_create_project_with_fields(self, mock_urlopen):
        mock_urlopen.return_value = self._mock_response({"code": 0, "msg": "success", "data": {"code": 123}})
        result = self.client.create_project("cdc_warehouse", "CDC demo")
        self.assertEqual(result["code"], 0)
        self.assertEqual(result["data"]["code"], 123)

    def test_audit_mode(self):
        with tempfile.TemporaryDirectory() as tmp:
            client = DolphinSchedulerClient("http://localhost", audit_mode=True, audit_dir=tmp)
            result = client.create_project("test")
            self.assertEqual(result["status"], "OK")
            self.assertTrue((Path(tmp) / "create_project.json").exists())

    @patch("urllib.request.urlopen")
    def test_online_process(self, mock_urlopen):
        # Mock project list
        mock_responses = [
            self._mock_response({"code": 0, "data": {"totalList": [{"code": 1, "name": "cdc_warehouse"}]}}),
            self._mock_response({"code": 0, "data": {"totalList": [{"code": 10, "name": "test_process"}]}}),
            self._mock_response({"code": 0, "msg": "success"}),
        ]
        mock_urlopen.side_effect = mock_responses

        result = self.client.online_process("cdc_warehouse", "test_process")
        self.assertEqual(result["code"], 0)


class LineageGraphTest(unittest.TestCase):
    """Test data lineage graph queries."""

    def setUp(self):
        from metadata.lineage.field_lineage import LineageGraph
        self.graph = LineageGraph()

    def test_upstream_of(self):
        sources = self.graph.upstream_of("dwd", "order_id", domain="trade")
        self.assertTrue(any("ods_order" in s for s in sources))

    def test_downstream_of(self):
        impacted = self.graph.downstream_of("ods", "id")
        self.assertGreater(len(impacted), 0)

    def test_validate_no_broken_refs(self):
        warnings = self.graph.validate()
        self.assertEqual(warnings, [])

    def test_full_lineage(self):
        graph = self.graph.full_lineage(domain="comment")
        self.assertIn("domains", graph)
        self.assertEqual(len(graph["domains"]), 1)

    def test_impact_analysis(self):
        result = self.graph.impact_analysis("pay_amount")
        self.assertGreater(result["impacted_count"], 0)

    def test_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.graph.export(Path(tmp) / "lineage.json", domain="trade")
            self.assertTrue(path.exists())
            data = json.loads(path.read_text())
            self.assertIn("domains", data)


class RowCountMonitorTest(unittest.TestCase):
    """Test row count monitor."""

    def setUp(self):
        import csv
        self.tmp = tempfile.TemporaryDirectory()
        self.upstream = Path(self.tmp.name) / "up.csv"
        self.downstream = Path(self.tmp.name) / "down.csv"
        # Write test CSVs
        for path, rows in [
            (self.upstream, [{"id": "1"}, {"id": "2"}, {"id": "3"}]),
            (self.downstream, [{"id": "1"}, {"id": "2"}, {"id": "3"}]),
        ]:
            with path.open("w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=["id"])
                w.writeheader()
                w.writerows(rows)

    def tearDown(self):
        self.tmp.cleanup()

    def test_perfect_match(self):
        from monitors.row_count_monitor import row_count_ratio
        result = row_count_ratio(self.upstream, self.downstream)
        self.assertTrue(result["passed"])
        self.assertEqual(result["ratio"], 1.0)

    def test_row_loss(self):
        import csv
        downstream2 = Path(self.tmp.name) / "down2.csv"
        with downstream2.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id"])
            w.writeheader()
            w.writerows([{"id": "1"}])
        from monitors.row_count_monitor import row_count_ratio
        result = row_count_ratio(self.upstream, downstream2)
        self.assertFalse(result["passed"])
        self.assertLess(result["ratio"], 1.0)


class NullRateMonitorTest(unittest.TestCase):
    """Test null rate monitor."""

    def setUp(self):
        import csv
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "test.csv"
        with self.path.open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["id", "name", "email"])
            w.writeheader()
            w.writerows([
                {"id": "1", "name": "alice", "email": "a@b.com"},
                {"id": "2", "name": "", "email": ""},
                {"id": "3", "name": "bob", "email": ""},
            ])

    def tearDown(self):
        self.tmp.cleanup()

    def test_null_rate_detection(self):
        from monitors.null_rate_monitor import null_rate_check
        result = null_rate_check(self.path, max_null_rate=0.3)
        self.assertFalse(result["passed"])
        self.assertIn("email", str(result["message"]))


class PartitionMonitorTest(unittest.TestCase):
    """Test partition completeness monitor."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        # Create a few partitions
        for table in ["ods_basiccomment_avatar_commentbatchsource_dic", "dim_comment_batch_type"]:
            p = self.root / "ods" / table / "dt=2026-07-06"
            p.mkdir(parents=True)
            (p / "part-00000.csv").write_text("id\n1\n")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmp.name, ignore_errors=True)

    def test_missing_partitions(self):
        from monitors.partition_monitor import check_partitions
        result = check_partitions(self.root, "2026-07-06")
        self.assertFalse(result["passed"])
        self.assertGreater(result["missing_count"], 0)


if __name__ == "__main__":
    unittest.main()
