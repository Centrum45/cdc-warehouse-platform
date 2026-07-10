from __future__ import annotations

"""
Realtime binlog → Kudu sink.

Two modes:
- Real mode: connects to Impala daemon, upserts into Kudu tables via Impala SQL.
  Requires: pip install impyla thrift-sasl
  Set KUDU_MASTERS env var or configure via configs/app.yaml.

- Simulation mode (default): maintains an in-memory key-value state persisted
  to local CSV. Used when Impala/Kudu are not available.
"""

import csv
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from streaming.common.binlog_parser import parse_topic_file
from streaming.common.checkpoint import FileCheckpoint

# ---------------------------------------------------------------------------
# Schema registry — maps (db, table) → (impala_db, impala_table, columns, pk)
# ---------------------------------------------------------------------------

TABLE_REGISTRY: dict[str, dict[str, Any]] = {
    "basiccomment.avatar_commentbatchsource": {
        "impala_db": "realtime",
        "impala_table": "avatar_commentbatchsource",
        "columns": ["id", "batchnumber", "batchtype", "ctime", "utime", "ver", "event_ts"],
        "primary_keys": ["id"],
    },
    "trade.order_info": {
        "impala_db": "realtime",
        "impala_table": "order_info",
        "columns": ["id", "user_id", "order_no", "pay_amount", "order_status",
                    "ctime", "utime", "ver", "event_ts"],
        "primary_keys": ["id"],
    },
    "user.user_info": {
        "impala_db": "realtime",
        "impala_table": "user_info",
        "columns": ["id", "user_name", "mobile", "email", "register_time",
                    "ctime", "utime", "ver", "event_ts"],
        "primary_keys": ["id"],
    },
}


def _resolve_table(topic_stem: str) -> dict[str, Any] | None:
    """Map a Kafka topic stem like 'cdc.incremental.binlog' to table metadata.

    For now, the topic name encodes the table via convention. Override by
    setting TABLE_REGISTRY entries keyed by fully-qualified (db, table).
    """
    # Try direct match first
    for key, meta in TABLE_REGISTRY.items():
        if topic_stem in key or key in topic_stem:
            return meta
    # Fallback: default comment batch source
    return TABLE_REGISTRY.get(
        "basiccomment.avatar_commentbatchsource",
        TABLE_REGISTRY["basiccomment.avatar_commentbatchsource"],
    )


# ---------------------------------------------------------------------------
# Real Kudu sink (Impala)
# ---------------------------------------------------------------------------

def _upsert_to_kudu(
    rows_to_upsert: list[dict[str, Any]],
    keys_to_delete: list[dict[str, Any]],
    meta: dict[str, Any],
) -> dict[str, Any]:
    """Upsert and delete rows in real Kudu via Impala."""
    from realtime.kudu.kudu_client import KuduClient

    client = KuduClient()
    if not client.is_available:
        return {"skipped": True, "reason": "impyla not installed"}

    db = meta["impala_db"]
    table = meta["impala_table"]

    result: dict[str, Any] = {"upserted": 0, "deleted": 0}
    try:
        if rows_to_upsert:
            res = client.upsert_rows(db, table, rows_to_upsert, meta["primary_keys"])
            result["upserted"] = res.get("upserted", 0)
        if keys_to_delete:
            res = client.delete_rows(db, table, keys_to_delete)
            result["deleted"] = res.get("deleted", 0)
        result["success"] = True
    except Exception as exc:
        result["success"] = False
        result["msg"] = str(exc)
    finally:
        client.close()
    return result


# ---------------------------------------------------------------------------
# Local CSV simulation (fallback)
# ---------------------------------------------------------------------------

def _csv_upsert(
    events: list[Any],
    meta: dict[str, Any],
    table_path: Path,
) -> int:
    """Simulate Kudu upsert with in-memory dict + CSV persistence."""
    state: dict[str, dict[str, object]] = {}

    if table_path.exists():
        with table_path.open("r", encoding="utf-8", newline="") as fp:
            for row in csv.DictReader(fp):
                state[str(row["id"])] = row

    for event in events:
        key = str(event.data.get("id"))
        if event.is_delete:
            state.pop(key, None)
            continue
        row = {col: event.data.get(col) for col in meta["columns"] if col != "event_ts"}
        row["event_ts"] = event.ts
        state[key] = row

    columns = meta["columns"]
    with table_path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        for row in sorted(state.values(), key=lambda item: str(item["id"])):
            writer.writerow(row)

    return len(events)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------


def upsert_rows(
    topic_file: Path,
    kudu_root: Path,
    checkpoint_path: Path,
    use_real_kudu: bool = False,
) -> Path:
    """Read binlog topic, upsert into Kudu (real or simulated).

    Returns the output path for CSV simulation, or a status marker for real Kudu.
    """
    topic = topic_file.stem
    checkpoint = FileCheckpoint(checkpoint_path)
    start_offset = checkpoint.load_offset(topic)
    events = parse_topic_file(topic_file)[start_offset:]

    if not events:
        return kudu_root / "realtime.avatar_commentbatchsource.csv"

    meta = _resolve_table(topic)

    # --- real Kudu path ---
    if use_real_kudu or os.environ.get("USE_REAL_KUDU", "").lower() in ("1", "true", "yes"):
        rows_to_upsert: list[dict[str, Any]] = []
        keys_to_delete: list[dict[str, Any]] = []

        for event in events:
            pk_vals = {k: event.data.get(k) for k in meta["primary_keys"] if event.data.get(k) is not None}
            if event.is_delete:
                keys_to_delete.append(pk_vals)
            else:
                row = {col: event.data.get(col) for col in meta["columns"] if col != "event_ts"}
                row["event_ts"] = event.ts
                rows_to_upsert.append(row)

        result = _upsert_to_kudu(rows_to_upsert, keys_to_delete, meta)
        if result.get("skipped"):
            print(f"[kafka_to_kudu] real Kudu skipped: {result.get('reason')}. Falling back to CSV.")
        else:
            print(f"[kafka_to_kudu] real Kudu: {result}")
            checkpoint.save_offset(topic, start_offset + len(events))
            return kudu_root / f"realtime.{meta['impala_table']}.kudu"

    # --- CSV simulation path ---
    table_path = kudu_root / f"realtime.{meta['impala_table']}.csv"
    table_path.parent.mkdir(parents=True, exist_ok=True)
    _csv_upsert(events, meta, table_path)
    checkpoint.save_offset(topic, start_offset + len(events))
    return table_path


def main() -> None:
    topic_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/kafka/cdc.incremental.binlog.jsonl")
    kudu_root = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/kudu")
    checkpoint_path = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("data/checkpoints/realtime_sink.json")
    use_real = "--real" in sys.argv
    output = upsert_rows(topic_file, kudu_root, checkpoint_path, use_real_kudu=use_real)
    print(output)


if __name__ == "__main__":
    main()
