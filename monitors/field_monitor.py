from __future__ import annotations


def missing_columns(expected: list[str], actual: list[str]) -> list[str]:
    actual_set = set(actual)
    return [column for column in expected if column not in actual_set]


def extra_columns(expected: list[str], actual: list[str]) -> list[str]:
    expected_set = set(expected)
    return [column for column in actual if column not in expected_set]

