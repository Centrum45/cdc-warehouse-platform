from __future__ import annotations


def find_special_values(row: dict[str, object], rules: dict[str, list[object]]) -> dict[str, object]:
    hits: dict[str, object] = {}
    for column, bad_values in rules.items():
        if row.get(column) in bad_values:
            hits[column] = row.get(column)
    return hits

