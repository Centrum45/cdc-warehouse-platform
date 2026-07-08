from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from monitors.table_update_monitor import is_stale


def max_update_time(csv_path: Path, column: str = "utime") -> str | None:
    if not csv_path.exists():
        return None
    with csv_path.open("r", encoding="utf-8", newline="") as fp:
        rows = list(csv.DictReader(fp))
    values = [row[column] for row in rows if row.get(column)]
    return max(values) if values else None


def main() -> None:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/lake/ods/db=basiccomment/table=avatar_commentbatchsource/dt=2026-07-06/part-00000.csv")
    now = sys.argv[2] if len(sys.argv) > 2 else "2026-07-07 00:00:00"
    threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 1440
    latest = max_update_time(csv_path)
    if latest is None:
        print("missing table data")
        raise SystemExit(1)
    stale = is_stale(latest, now, threshold)
    print(f"latest={latest} stale={stale}")
    if stale:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
