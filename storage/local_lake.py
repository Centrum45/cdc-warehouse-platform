from __future__ import annotations

import csv
import json
import os
from pathlib import Path
from typing import Any, Iterable


class LocalLake:
    """Local filesystem adapter with Hive-style partition paths.

    All writes use temp-then-rename for atomicity.
    """

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    # ------------------------------------------------------------------
    # Partition paths
    # ------------------------------------------------------------------

    def binlog_partition(self, database: str, table: str, dt: str) -> Path:
        return self.root / "ods_binlog" / f"db={database}" / f"table={table}" / f"dt={dt}"

    def ods_partition(self, database: str, table: str, dt: str) -> Path:
        return self.root / "ods" / f"db={database}" / f"table={table}" / f"dt={dt}"

    # ------------------------------------------------------------------
    # Atomic write helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _atomic_write(path: Path, write_fn) -> None:
        """Write to a .tmp file, then atomically rename to target path.

        On crash/interrupt, the .tmp file is left behind (harmless).
        On success, the rename is atomic on the same filesystem.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        write_fn(tmp_path)
        os.replace(tmp_path, path)

    # ------------------------------------------------------------------
    # JSONL read / write
    # ------------------------------------------------------------------

    def write_jsonl(self, path: Path, rows: Iterable[dict[str, Any]]) -> None:
        def _write(target: Path) -> None:
            with target.open("w", encoding="utf-8") as fp:
                for row in rows:
                    fp.write(json.dumps(row, ensure_ascii=False, sort_keys=True))
                    fp.write("\n")
        self._atomic_write(path, _write)

    def read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8") as fp:
            return [json.loads(line) for line in fp if line.strip()]

    # ------------------------------------------------------------------
    # CSV read / write
    # ------------------------------------------------------------------

    def write_csv(self, path: Path, rows: list[dict[str, Any]], columns: list[str]) -> None:
        def _write(target: Path) -> None:
            with target.open("w", encoding="utf-8", newline="") as fp:
                writer = csv.DictWriter(fp, fieldnames=columns)
                writer.writeheader()
                for row in rows:
                    writer.writerow({column: row.get(column, "") for column in columns})
        self._atomic_write(path, _write)

    def read_csv(self, path: Path) -> list[dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", encoding="utf-8", newline="") as fp:
            return list(csv.DictReader(fp))
