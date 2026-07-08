from __future__ import annotations

import json
from pathlib import Path


class FileCheckpoint:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load_offset(self, topic: str) -> int:
        if not self.path.exists():
            return 0
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return int(payload.get(topic, 0))

    def save_offset(self, topic: str, offset: int) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {}
        if self.path.exists():
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        payload[topic] = int(offset)
        self.path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
