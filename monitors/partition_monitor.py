from __future__ import annotations

"""
Partition completeness monitor — verifies expected partitions exist
for all layers of the warehouse.

Checks that for a given biz_dt, every layer has its partition written.
"""

from pathlib import Path
from typing import Any

# Expected table → layer mapping for completeness check
LAYER_TABLE_MAP: dict[str, list[str]] = {
    "ods": [
        "ods_basiccomment_avatar_commentbatchsource_dic",
        "ods_trade_order_info_dic",
        "ods_user_user_info_dic",
    ],
    "dim": [
        "dim_comment_batch_type",
        "dim_user_info",
    ],
    "dwd": [
        "dwd_comment_batch_detail_di",
        "dwd_trade_order_detail_di",
    ],
    "dws": [
        "dws_comment_batch_1d",
        "dws_trade_user_1d",
    ],
    "dwt": [
        "dwt_comment_batch_topic_td",
        "dwt_trade_user_td",
    ],
    "ads": [
        "ads_comment_dashboard_1d",
        "ads_trade_dashboard_1d",
    ],
}


def check_partitions(
    lake_root: str | Path,
    biz_dt: str,
    table_map: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Check that all expected table partitions exist for biz_dt.

    Scans data/lake/{layer}/{table}/dt={biz_dt}/ for each table.
    """
    root = Path(lake_root)
    table_map = table_map or LAYER_TABLE_MAP

    results: dict[str, dict[str, bool]] = {}
    missing: list[str] = []

    for layer, tables in table_map.items():
        results[layer] = {}
        for table in tables:
            partition_path = root / layer / table / f"dt={biz_dt}"
            exists = partition_path.exists() and any(partition_path.iterdir())
            results[layer][table] = exists
            if not exists:
                missing.append(f"{layer}.{table}")

    passed = len(missing) == 0
    message = "all partitions present" if passed else f"missing: {missing}"

    return {
        "passed": passed,
        "message": message,
        "biz_dt": biz_dt,
        "total_expected": sum(len(t) for t in table_map.values()),
        "missing_count": len(missing),
        "missing": missing,
        "layers": results,
    }
