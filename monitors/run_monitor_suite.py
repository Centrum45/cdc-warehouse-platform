from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from monitors.field_monitor_job import diff_columns
from monitors.notifier import Notifier
from monitors.null_rate_monitor import null_rate_check
from monitors.partition_monitor import check_partitions
from monitors.result_store import MonitorResultStore
from monitors.row_count_monitor import load_rules, row_count_ratio
from warehouse.jobs.delay_gate import can_merge


def run_suite(biz_dt: str = "2026-07-06") -> None:
    store = MonitorResultStore()
    notifier = Notifier()
    rules = load_rules()

    # ---- delay gate ----
    allowed, reason = can_merge("data/progress", "basiccomment", "avatar_commentbatchsource", 999999999)
    store.append("delay", "basiccomment", "avatar_commentbatchsource", "OK" if allowed else "FAIL", reason)
    if not allowed:
        notifier.send("dingtalk", "dba", "CDC delay alert", reason)

    # ---- field drift ----
    missing = diff_columns(
        Path("metadata/tables/basiccomment.avatar_commentbatchsource.json"),
        Path("metadata/dba/basiccomment.avatar_commentbatchsource.json")
    )
    status = "OK" if not missing else "WARN"
    message = "metadata aligned" if not missing else f"missing columns: {[column['name'] for column in missing]}"
    store.append("field", "basiccomment", "avatar_commentbatchsource", status, message, len(missing))
    if missing:
        notifier.send("email", "dba@example.com", "CDC field drift", message)

    # ---- row count (ODS -> DWD) ----
    rc_rules = rules.get("row_count", {})
    ods_path = Path(f"data/lake/ods/db=basiccomment/table=avatar_commentbatchsource/dt={biz_dt}/part-00000.csv")
    dwd_path = Path(f"data/lake/dwd/dwd_comment_batch_detail_di/dt={biz_dt}/part-00000.parquet")
    if ods_path.exists():
        rc_result = row_count_ratio(
            ods_path, dwd_path,
            min_ratio=rc_rules.get("min_ratio", 0.99),
            max_ratio=rc_rules.get("max_ratio", 1.01),
        )
        store.append(
            "row_count", "basiccomment", "avatar_commentbatchsource",
            "OK" if rc_result["passed"] else "FAIL",
            rc_result["message"],
        )
        if not rc_result["passed"]:
            notifier.send("email", "dba@example.com", "CDC row count drift", rc_result["message"])

    # ---- null rate ----
    nr_rules = rules.get("null_rate", {})
    nr_result = null_rate_check(
        ods_path,
        max_null_rate=nr_rules.get("max_null_rate", 0.05),
        skip_columns=nr_rules.get("skip_columns", []),
    )
    store.append(
        "null_rate", "basiccomment", "avatar_commentbatchsource",
        "OK" if nr_result["passed"] else "FAIL",
        nr_result["message"],
    )
    if not nr_result["passed"]:
        notifier.send("email", "dba@example.com", "CDC null rate alert", nr_result["message"])

    # ---- partition completeness ----
    pq_rules = rules.get("partition", {})
    if pq_rules.get("enabled", True):
        pq_result = check_partitions("data/lake", biz_dt)
        store.append(
            "partition", "*", "*",
            "OK" if pq_result["passed"] else "FAIL",
            pq_result["message"],
        )
        if not pq_result["passed"]:
            notifier.send("email", "dba@example.com", "CDC partition missing", pq_result["message"])

    print(store.path)


if __name__ == "__main__":
    run_suite()
