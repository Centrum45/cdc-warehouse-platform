from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path


class FileCheckpoint:
    """File-based offset checkpoint with advisory locking.

    Uses fcntl.flock to prevent concurrent write corruption.
    Atomic write via temp-then-rename.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_offset(self, topic: str) -> int:
        if not self.path.exists():
            return 0
        payload = self._read_locked()
        return int(payload.get(topic, 0))

    def save_offset(self, topic: str, offset: int) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, int] = {}
        if self.path.exists():
            payload = self._read_locked()
        payload[topic] = int(offset)

        # Atomic write with file lock
        tmp_path = self.path.with_suffix(self.path.suffix + ".tmp")
        with open(tmp_path, "w", encoding="utf-8") as fp:
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(payload, fp, sort_keys=True)
                fp.flush()
                os.fsync(fp.fileno())
            finally:
                fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
        os.replace(tmp_path, self.path)

    def _read_locked(self) -> dict[str, int]:
        """Read checkpoint with shared lock."""
        with open(self.path, "r", encoding="utf-8") as fp:
            fcntl.flock(fp.fileno(), fcntl.LOCK_SH)
            try:
                return json.loads(fp.read() or "{}")
            finally:
                fcntl.flock(fp.fileno(), fcntl.LOCK_UN)
