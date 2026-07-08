from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class MaxwellEvent:
    database: str
    table: str
    event_type: str
    ts: int
    xid: int | None
    data: dict[str, Any]
    old: dict[str, Any]

    @property
    def qualified_table(self) -> str:
        return f"{self.database}.{self.table}"

    @property
    def business_dt(self) -> str:
        ctime = self.data.get("ctime")
        if ctime is None:
            return "unknown"
        return str(ctime)[:10]

    @property
    def is_delete(self) -> bool:
        return self.event_type == "delete"
