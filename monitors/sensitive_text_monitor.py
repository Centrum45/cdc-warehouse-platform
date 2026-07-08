from __future__ import annotations

import re

PATTERNS = {
    "phone": re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    "id_card": re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
}


def detect_sensitive_text(value: str) -> list[str]:
    return [name for name, pattern in PATTERNS.items() if pattern.search(value or "")]


def scan_row(row: dict[str, object]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for column, value in row.items():
        hits = detect_sensitive_text(str(value))
        if hits:
            result[column] = hits
    return result

