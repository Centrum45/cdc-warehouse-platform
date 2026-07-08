from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


class Notifier:
    def __init__(self, outbox: str | Path = "data/alerts/outbox.jsonl") -> None:
        self.outbox = Path(outbox)

    def send(self, channel: str, target: str, title: str, body: str) -> Path:
        self.outbox.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "channel": channel,
            "target": target,
            "title": title,
            "body": body
        }
        with self.outbox.open("a", encoding="utf-8") as fp:
            fp.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
            fp.write("\n")
        return self.outbox
