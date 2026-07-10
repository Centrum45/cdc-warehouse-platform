from __future__ import annotations

"""
Null rate monitor — checks per-column null ratio against thresholds.
Flags columns exceeding the configured max_null_rate.
"""

import csv
from pathlib import Path
from typing import Any


def null_rate_check(
    csv_path: Path,
    max_null_rate: float = 0.05,
    skip_columns: list[str] | None = None,
) -> dict[str, Any]:
    """Compute null rate for each column in a CSV partition.

    Returns dict with per-column null rates and overall pass/fail.
    """
    skip = set(skip_columns) if skip_columns else set()

    if not csv_path.exists():
        return {"passed": False, "message": f"file not found: {csv_path}", "columns": {}}

    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        rows = list(reader)

    if not rows or not reader.fieldnames:
        return {"passed": True, "message": "empty file", "columns": {}}

    total = len(rows)
    column_rates: dict[str, dict[str, Any]] = {}
    failed_columns: list[str] = []

    for col in reader.fieldnames:
        if col in skip:
            continue
        null_count = sum(1 for row in rows if row.get(col) in (None, "", "null", "NULL", "None"))
        rate = null_count / total
        column_rates[col] = {"null_count": null_count, "total": total, "rate": round(rate, 4)}
        if rate > max_null_rate:
            failed_columns.append(col)

    passed = len(failed_columns) == 0
    message = "all columns within threshold" if passed else f"columns over {max_null_rate:.0%}: {failed_columns}"

    return {"passed": passed, "message": message, "columns": column_rates}
