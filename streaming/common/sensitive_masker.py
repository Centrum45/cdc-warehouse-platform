from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def md5_text(value: object) -> str:
    return hashlib.md5(str(value).encode("utf-8")).hexdigest()


def load_rules(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as fp:
        return json.load(fp)


def mask_event(event: dict[str, Any], rules: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    columns = rules.get("columns", {})
    data = dict(event.get("data", {}))
    hits: list[str] = []

    for column, rule in columns.items():
        if column not in data or data[column] in (None, ""):
            continue
        hits.append(column)
        action = rule.get("action", rules.get("default_action", "md5"))
        if action == "md5":
            data[column] = md5_text(data[column])
        elif action == "default":
            data[column] = rule.get("default_value", "")

    masked = dict(event)
    masked["data"] = data
    if hits:
        masked["_sensitive_hits"] = hits
    return masked, hits
