from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_KEYS = {
    "source_database",
    "source_table",
    "primary_keys",
    "version_column",
    "partition_column",
    "columns",
}


def load_table_metadata(path: str | Path) -> dict[str, Any]:
    metadata_path = Path(path)
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    missing = sorted(REQUIRED_KEYS - set(metadata))
    if missing:
        raise ValueError(f"invalid table metadata {metadata_path}: missing {missing}")
    if not metadata["primary_keys"]:
        raise ValueError(f"invalid table metadata {metadata_path}: primary_keys is empty")
    if not metadata["columns"]:
        raise ValueError(f"invalid table metadata {metadata_path}: columns is empty")
    return metadata


def data_columns(metadata: dict[str, Any]) -> list[str]:
    return [column["name"] for column in metadata["columns"]]
