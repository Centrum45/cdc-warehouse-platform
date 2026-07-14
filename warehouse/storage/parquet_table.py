from __future__ import annotations

import io
from pathlib import Path
from typing import Any, Iterable


def _pyarrow():
    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
    except Exception as exc:
        raise RuntimeError("pyarrow is required for parquet read/write") from exc
    return pa, pq


def parquet_bytes(rows: Iterable[dict[str, Any]], columns: list[str]) -> bytes:
    pa, pq = _pyarrow()
    materialized = [{column: row.get(column) for column in columns} for row in rows]
    table = pa.Table.from_pydict({
        column: [row.get(column) for row in materialized]
        for column in columns
    })
    output = io.BytesIO()
    pq.write_table(table, output, compression="snappy")
    return output.getvalue()


def read_parquet_bytes(payload: bytes) -> list[dict[str, Any]]:
    if not payload:
        return []
    _, pq = _pyarrow()
    return pq.read_table(io.BytesIO(payload)).to_pylist()


def write_local_parquet(path: Path, rows: Iterable[dict[str, Any]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_bytes(parquet_bytes(rows, columns))
    tmp_path.replace(path)


def read_local_parquet(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return read_parquet_bytes(path.read_bytes())
