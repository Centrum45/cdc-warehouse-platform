from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterable


class LocalLake:
    """Local filesystem adapter that keeps Hive-style partition paths."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def binlog_partition(self, database: str, table: str, dt: str) -> Path:
        return self.root / "ods_binlog" / f"db={database}" / f"table={table}" / f"dt={dt}"

    def ods_partition(self, database: str, table: str, dt: str) -> Path:
        return self.root / "ods" / f"db={database}" / f"table={table}" / f"dt={dt}"

    def write_jsonl(self, path: Path, rows: Iterable[dict[str, Any]]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fp:
            for row in rows:
                fp.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                fp.write("\n")

    def read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as fp:
            return [json.loads(line) for line in fp if line.strip()]

    def write_csv(self, path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column, "") for column in columns})

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as fp:
            return list(csv.DictReader(fp))

