from __future__ import annotations

"""
Row count monitor — compares row counts between ODS and downstream layers.
Detects data loss or duplication in ETL pipeline.
"""

import csv
import json
from pathlib import Path
from typing import Any


def row_count_ratio(
    upstream_csv: Path,
    downstream_csv: Path,
    min_ratio: float = 0.99,
    max_ratio: float = 1.01,
) -> dict[str, Any]:
    """Compare row counts of two CSV partitions.

    Returns dict with:
        upstream_count, downstream_count, ratio, passed, message
    """
    upstream_count = _count_rows(upstream_csv)
    downstream_count = _count_rows(downstream_csv)

    if upstream_count == 0 and downstream_count == 0:
        return {
            "upstream_count": 0, "downstream_count": 0, "ratio": 1.0,
            "passed": True, "message": "both empty — no data to compare",
        }

    if upstream_count == 0:
        return {
            "upstream_count": 0, "downstream_count": downstream_count, "ratio": float("inf"),
            "passed": False, "message": f"upstream empty but downstream has {downstream_count} rows",
        }

    ratio = downstream_count / upstream_count
    passed = min_ratio <= ratio <= max_ratio

    direction = "loss" if ratio < 1 else "gain" if ratio > 1 else "match"
    message = (
        f"upstream={upstream_count} downstream={downstream_count} "
        f"ratio={ratio:.4f} ({direction})"
    )

    return {
        "upstream_count": upstream_count,
        "downstream_count": downstream_count,
        "ratio": ratio,
        "passed": passed,
        "message": message,
    }


def _count_rows(csv_path: Path) -> int:
    if not csv_path.exists():
        return 0
    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        reader = csv.DictReader(fp)
        return sum(1 for _ in reader)


def load_rules(rules_path: str | Path = "metadata/rules/data_quality_rules.json") -> dict[str, Any]:
    path = Path(rules_path)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
