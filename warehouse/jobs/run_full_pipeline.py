"""
Full warehouse pipeline: ODS → DIM → DWD → DWS → DWT → ADS
Local CSV-based execution — no Hive/Spark required.
"""
from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

BIZ_DT = os.environ.get("BIZ_DT", "2026-07-06")
LAKE_ROOT = ROOT / "data" / "lake"


# ── helpers ──────────────────────────────────────────────────────────

def read_csv(path: Path) -> list[dict[str, str]]:
    """Read CSV, return list of dicts keyed by header."""
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [row for row in reader]


def write_csv(path: Path, rows: list[dict[str, Any]], columns: list[str]) -> Path:
    """Write CSV with given column order."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in columns})
    return path


def ods_partition(database: str, table: str, dt: str) -> Path:
    return LAKE_ROOT / "ods" / f"db={database}" / f"table={table}" / f"dt={dt}"


def layer_partition(layer: str, table: str, dt: str) -> Path:
    return LAKE_ROOT / layer / table / f"dt={dt}"


# ── layer steps ──────────────────────────────────────────────────────

def step_dim_comment_batch_type(dt: str) -> list[dict]:
    """dim.dim_comment_batch_type — static seed."""
    return [
        {"batchtype": "normal", "batchtype_name": "普通批次", "is_priority": "0"},
        {"batchtype": "priority", "batchtype_name": "优先批次", "is_priority": "1"},
    ]


def step_dim_user_info(dt: str) -> list[dict]:
    """dim.dim_user_info — latest snapshot from ods_user_user_info_dic."""
    # user ODS data is at dt=2026-07-01
    user_dt = "2026-07-01"
    rows = read_csv(ods_partition("user", "user_info", user_dt) / "part-00000.csv")
    result = []
    for r in rows:
        result.append({
            "user_id": r.get("id", ""),
            "user_name": r.get("user_name", ""),
            "mobile": r.get("mobile", ""),
            "email": r.get("email", ""),
            "register_time": r.get("register_time", ""),
        })
    return result


def step_dwd_comment_batch_detail(dt: str) -> list[dict]:
    """dwd.dwd_comment_batch_detail_di — join ods + dim_comment_batch_type."""
    ods_rows = read_csv(ods_partition("basiccomment", "avatar_commentbatchsource", dt) / "part-00000.csv")
    dim_types = {r["batchtype"]: r for r in step_dim_comment_batch_type(dt)}

    result = []
    for r in ods_rows:
        bt = r.get("batchtype", "")
        dim_row = dim_types.get(bt, {"batchtype_name": "", "is_priority": "0"})
        result.append({
            "id": r.get("id", ""),
            "batchnumber": r.get("batchnumber", ""),
            "batchtype": bt,
            "batchtype_name": dim_row["batchtype_name"],
            "ctime": r.get("ctime", ""),
            "utime": r.get("utime", ""),
            "ver": r.get("ver", ""),
        })
    return result


def step_dwd_trade_order_detail(dt: str) -> list[dict]:
    """dwd.dwd_trade_order_detail_di — join ods_order_info + ods_user_info."""
    orders = read_csv(ods_partition("trade", "order_info", dt) / "part-00000.csv")
    user_dt = "2026-07-01"
    users_list = read_csv(ods_partition("user", "user_info", user_dt) / "part-00000.csv")
    users = {r.get("id", ""): r for r in users_list}

    result = []
    for r in orders:
        uid = r.get("user_id", "")
        u = users.get(uid, {})
        result.append({
            "order_id": r.get("id", ""),
            "user_id": uid,
            "order_no": r.get("order_no", ""),
            "pay_amount": r.get("pay_amount", ""),
            "order_status": r.get("order_status", ""),
            "user_name": u.get("user_name", ""),
            "ctime": r.get("ctime", ""),
            "utime": r.get("utime", ""),
        })
    return result


def step_dws_comment_batch_1d(dt: str) -> list[dict]:
    """dws.dws_comment_batch_1d — group by batchtype."""
    dwd_rows = step_dwd_comment_batch_detail(dt)
    agg: dict[str, dict] = {}
    for r in dwd_rows:
        bt = r["batchtype"]
        if bt not in agg:
            agg[bt] = {"batchtype": bt, "batch_cnt": 0, "priority_batch_cnt": 0}
        agg[bt]["batch_cnt"] += 1
        if bt == "priority":
            agg[bt]["priority_batch_cnt"] += 1
    return list(agg.values())


def step_dws_trade_user_1d(dt: str) -> list[dict]:
    """dws.dws_trade_user_1d — group by user_id."""
    dwd_rows = step_dwd_trade_order_detail(dt)
    agg: dict[str, dict] = {}
    for r in dwd_rows:
        uid = r["user_id"]
        if uid not in agg:
            agg[uid] = {"user_id": uid, "order_cnt": 0, "pay_amount": 0.0}
        agg[uid]["order_cnt"] += 1
        agg[uid]["pay_amount"] += float(r.get("pay_amount", 0))
    return [
        {"user_id": v["user_id"], "order_cnt": str(v["order_cnt"]),
         "pay_amount": str(v["pay_amount"])}
        for v in agg.values()
    ]


def step_dwt_comment_batch_topic_td(dt: str) -> list[dict]:
    """dwt.dwt_comment_batch_topic_td — cumulative: full outer join today + yesterday."""
    today = {r["batchtype"]: r for r in step_dws_comment_batch_1d(dt)}

    from datetime import datetime, timedelta
    prev_dt = (datetime.strptime(dt, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_path = layer_partition("dwt", "dwt_comment_batch_topic_td", prev_dt) / "part-00000.csv"
    yesterday_rows = read_csv(yesterday_path)
    yesterday = {r["batchtype"]: r for r in yesterday_rows}

    all_bts = set(today.keys()) | set(yesterday.keys())
    result = []
    for bt in all_bts:
        t = today.get(bt, {"batch_cnt": "0", "priority_batch_cnt": "0"})
        y = yesterday.get(bt, {"total_batch_cnt": "0", "priority_batch_cnt": "0"})
        result.append({
            "batchtype": bt,
            "total_batch_cnt": str(int(y["total_batch_cnt"]) + int(t["batch_cnt"])),
            "priority_batch_cnt": str(int(y["priority_batch_cnt"]) + int(t["priority_batch_cnt"])),
            "latest_batch_time": dt,
        })
    return result


def step_dwt_trade_user_td(dt: str) -> list[dict]:
    """dwt.dwt_trade_user_td — cumulative per user."""
    today = {r["user_id"]: r for r in step_dws_trade_user_1d(dt)}

    from datetime import datetime, timedelta
    prev_dt = (datetime.strptime(dt, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    yesterday_path = layer_partition("dwt", "dwt_trade_user_td", prev_dt) / "part-00000.csv"
    yesterday_rows = read_csv(yesterday_path)
    yesterday = {r["user_id"]: r for r in yesterday_rows}

    all_uids = set(today.keys()) | set(yesterday.keys())
    result = []
    for uid in all_uids:
        t = today.get(uid, {"order_cnt": "0", "pay_amount": "0"})
        y = yesterday.get(uid, {
            "total_order_cnt": "0", "total_pay_amount": "0",
            "first_order_date": dt, "last_order_date": dt
        })
        result.append({
            "user_id": uid,
            "total_order_cnt": str(int(y["total_order_cnt"]) + int(t["order_cnt"])),
            "total_pay_amount": str(float(y["total_pay_amount"]) + float(t["pay_amount"])),
            "first_order_date": y.get("first_order_date", dt),
            "last_order_date": dt,
        })
    return result


def step_ads_comment_dashboard_1d(dt: str) -> list[dict]:
    """ads.ads_comment_dashboard_1d — metrics from DWT."""
    dwt_rows = step_dwt_comment_batch_topic_td(dt)
    total_batch = sum(int(r["total_batch_cnt"]) for r in dwt_rows)
    priority_batch = sum(int(r["priority_batch_cnt"]) for r in dwt_rows)
    return [
        {"metric_name": "comment_batch_total", "metric_value": str(total_batch)},
        {"metric_name": "comment_batch_priority_total", "metric_value": str(priority_batch)},
    ]


def step_ads_trade_dashboard_1d(dt: str) -> list[dict]:
    """ads.ads_trade_dashboard_1d — GMV, user counts from DWS + DWT."""
    dws_rows = step_dws_trade_user_1d(dt)
    dwt_rows = step_dwt_trade_user_td(dt)

    gmv = sum(float(r["pay_amount"]) for r in dws_rows)
    pay_user_cnt = len({r["user_id"] for r in dws_rows})
    total_gmv = sum(float(r["total_pay_amount"]) for r in dwt_rows)
    total_user_cnt = len({r["user_id"] for r in dwt_rows})
    total_orders = sum(int(r["total_order_cnt"]) for r in dwt_rows)
    avg_order = total_orders / total_user_cnt if total_user_cnt > 0 else 0.0

    return [
        {"metric_name": "gmv", "metric_value": str(gmv)},
        {"metric_name": "pay_user_cnt", "metric_value": str(pay_user_cnt)},
        {"metric_name": "total_gmv", "metric_value": str(total_gmv)},
        {"metric_name": "total_user_cnt", "metric_value": str(total_user_cnt)},
        {"metric_name": "avg_order_per_user", "metric_value": str(round(avg_order, 2))},
    ]


# ── pipeline orchestrator ────────────────────────────────────────────

PIPELINE = [
    # (layer, table, step_fn, columns)
    ("dim", "dim_comment_batch_type", step_dim_comment_batch_type,
     ["batchtype", "batchtype_name", "is_priority"]),
    ("dim", "dim_user_info", step_dim_user_info,
     ["user_id", "user_name", "mobile", "email", "register_time"]),
    ("dwd", "dwd_comment_batch_detail_di", step_dwd_comment_batch_detail,
     ["id", "batchnumber", "batchtype", "batchtype_name", "ctime", "utime", "ver"]),
    ("dwd", "dwd_trade_order_detail_di", step_dwd_trade_order_detail,
     ["order_id", "user_id", "order_no", "pay_amount", "order_status",
      "user_name", "ctime", "utime"]),
    ("dws", "dws_comment_batch_1d", step_dws_comment_batch_1d,
     ["batchtype", "batch_cnt", "priority_batch_cnt"]),
    ("dws", "dws_trade_user_1d", step_dws_trade_user_1d,
     ["user_id", "order_cnt", "pay_amount"]),
    ("dwt", "dwt_comment_batch_topic_td", step_dwt_comment_batch_topic_td,
     ["batchtype", "total_batch_cnt", "priority_batch_cnt", "latest_batch_time"]),
    ("dwt", "dwt_trade_user_td", step_dwt_trade_user_td,
     ["user_id", "total_order_cnt", "total_pay_amount", "first_order_date",
      "last_order_date"]),
    ("ads", "ads_comment_dashboard_1d", step_ads_comment_dashboard_1d,
     ["metric_name", "metric_value"]),
    ("ads", "ads_trade_dashboard_1d", step_ads_trade_dashboard_1d,
     ["metric_name", "metric_value"]),
]


def run(dt: str = BIZ_DT, dry: bool = False) -> None:
    print(f"{'[DRY RUN] ' if dry else ''}Pipeline for dt={dt}")
    print(f"Lake root: {LAKE_ROOT}")
    print("-" * 60)

    for layer, table, step_fn, columns in PIPELINE:
        out_dir = layer_partition(layer, table, dt)
        out_file = out_dir / "part-00000.csv"

        rows = step_fn(dt)
        print(f"  {layer:>4s}.{table:<35s} → {len(rows):>4d} rows", end="")

        if dry:
            print("  (dry — skipped write)")
        else:
            write_csv(out_file, rows, columns)
            print(f"  ✓ {out_file}")

    print("-" * 60)
    print("Done.")


if __name__ == "__main__":
    dry_run = "--dry" in sys.argv
    run(dry=dry_run)
