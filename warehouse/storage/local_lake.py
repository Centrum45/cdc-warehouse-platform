from __future__ import annotations

import os
from pathlib import Path
from typing import Any


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
