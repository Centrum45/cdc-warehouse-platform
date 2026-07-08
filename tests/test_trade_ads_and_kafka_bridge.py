from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from warehouse.jobs.local_trade_ads import compute_trade_ads


class TradeAdsTest(unittest.TestCase):
    def test_compute_trade_ads(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            lake = Path(tmp)
            order_dir = lake / "ods/db=trade/table=order_info/dt=2026-07-06"
            order_dir.mkdir(parents=True)
            with (order_dir / "part-00000.csv").open("w", encoding="utf-8", newline="") as fp:
                writer = csv.DictWriter(fp, fieldnames=["id", "user_id", "pay_amount", "order_status"])
                writer.writeheader()
                writer.writerow({"id": 1, "user_id": 501, "pay_amount": 128.5, "order_status": "PAID"})
                writer.writerow({"id": 2, "user_id": 502, "pay_amount": 9.9, "order_status": "CANCEL"})
            output = compute_trade_ads(lake, "2026-07-06")
            text = output.read_text(encoding="utf-8")
            self.assertIn("gmv,128.5", text)
            self.assertIn("pay_user_cnt,1", text)


if __name__ == "__main__":
    unittest.main()
