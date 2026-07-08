from __future__ import annotations


def build_add_columns_sql(database: str, table: str, missing_columns: list[dict[str, str]]) -> list[str]:
    statements = []
    for column in missing_columns:
        statements.append(f"alter table {database}.{table} add columns ({column['name']} {column['type']});")
    return statements
