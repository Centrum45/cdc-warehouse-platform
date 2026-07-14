from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayPlan:
    database: str
    table: str
    start_time: str
    end_time: str
    target_topic: str

    def describe(self) -> str:
        return f"{self.database}.{self.table} {self.start_time} -> {self.end_time} => {self.target_topic}"

