from __future__ import annotations


def build_not_null_sql(table: str, columns: list[str], dt: str) -> str:
    checks = " or ".join(f"{column} is null" for column in columns)
    return f"select '{table}' as table_name, count(1) as bad_count from {table} where dt = '{dt}' and ({checks});"


def build_special_value_sql(table: str, rules: dict[str, list[object]], dt: str) -> list[str]:
    statements = []
    for column, values in rules.items():
        formatted = ", ".join(f"'{value}'" for value in values)
        statements.append(
            f"select '{table}' as table_name, '{column}' as column_name, count(1) as bad_count "
            f"from {table} where dt = '{dt}' and {column} in ({formatted});"
        )
    return statements


def build_increasing_sql(table: str, key_column: str, value_column: str, dt: str) -> str:
    return (
        f"select '{table}' as table_name, count(1) as bad_count "
        f"from {table} today join {table} yesterday on today.{key_column} = yesterday.{key_column} "
        f"where today.dt = '{dt}' and yesterday.dt = date_sub('{dt}', 1) "
        f"and today.{value_column} < yesterday.{value_column};"
    )
