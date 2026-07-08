from __future__ import annotations

import csv
from pathlib import Path


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as fp:
        return list(csv.DictReader(fp))


def write_metric(path: Path, metrics: list[dict[str, object]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=["metric_name", "metric_value", "dt"])
        writer.writeheader()
        for metric in metrics:
            writer.writerow(metric)
    return path


def compute_trade_ads(lake_root: Path, dt: str) -> Path:
    order_path = lake_root / "ods/db=trade/table=order_info" / f"dt={dt}" / "part-00000.csv"
    orders = read_csv(order_path)
    paid_orders = [row for row in orders if row.get("order_status") == "PAID"]
    gmv = sum(float(row.get("pay_amount") or 0) for row in paid_orders)
    pay_users = len({row.get("user_id") for row in paid_orders if row.get("user_id")})
    output = lake_root / "ads/trade_dashboard_1d" / f"dt={dt}" / "part-00000.csv"
    return write_metric(output, [
        {"metric_name": "gmv", "metric_value": gmv, "dt": dt},
        {"metric_name": "pay_user_cnt", "metric_value": pay_users, "dt": dt}
    ])


def main() -> None:
    print(compute_trade_ads(Path("data/lake"), "2026-07-06"))


if __name__ == "__main__":
    main()
