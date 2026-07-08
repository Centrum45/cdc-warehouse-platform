from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class MetadataService:
    def __init__(self, metadata_root: str | Path) -> None:
        self.metadata_root = Path(metadata_root)

    def list_tables(self) -> list[str]:
        return sorted(path.stem for path in self.metadata_root.glob("*.json"))

    def get_table(self, qualified_name: str) -> dict[str, Any]:
        path = self.metadata_root / f"{qualified_name}.json"
        with path.open("r", encoding="utf-8") as fp:
            return json.load(fp)

    def find_by_source(self, database: str, table: str) -> dict[str, Any] | None:
        for path in self.metadata_root.glob("*.json"):
            with path.open("r", encoding="utf-8") as fp:
                metadata = json.load(fp)
            if metadata["source_database"] == database and metadata["source_table"] == table:
                return metadata
        return None

