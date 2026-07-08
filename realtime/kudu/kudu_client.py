from __future__ import annotations

"""
Real Kudu client via Impala.

Uses impyla to connect to the Impala daemon, which manages Kudu tables.
Kudu DML (INSERT / UPSERT / DELETE) and DDL (CREATE TABLE ... STORED AS KUDU)
are executed through Impala SQL.

Installation:
    pip install impyla thrift-sasl

Environment / config:
    IMPALA_HOST  — default localhost
    IMPALA_PORT  — default 21050
    KUDU_MASTERS — comma-separated Kudu master addresses (for DDL only)
"""

import os
from typing import Any


class KuduClient:
    """Write path: upsert / delete rows in Kudu tables via Impala."""

    def __init__(
        self,
        impala_host: str | None = None,
        impala_port: int = 21050,
        kudu_masters: str | None = None,
    ) -> None:
        self.impala_host = impala_host or os.environ.get("IMPALA_HOST", "localhost")
        self.impala_port = impala_port or int(os.environ.get("IMPALA_PORT", "21050"))
        self.kudu_masters = kudu_masters or os.environ.get("KUDU_MASTERS", "")
        self._conn = None

    @property
    def is_available(self) -> bool:
        try:
            import impala.dbapi  # noqa: F401
            return True
        except ModuleNotFoundError:
            return False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def _connect(self):
        if self._conn is not None:
            return self._conn
        try:
            import impala.dbapi
        except ModuleNotFoundError:
            raise RuntimeError(
                "impyla not installed. Run: pip install impyla thrift-sasl"
            )
        self._conn = impala.dbapi.connect(
            host=self.impala_host,
            port=self.impala_port,
        )
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # ------------------------------------------------------------------
    # DDL
    # ------------------------------------------------------------------

    def create_table(self, ddl: str) -> dict[str, Any]:
        """Execute a CREATE TABLE ... STORED AS KUDU statement."""
        if not self.is_available:
            return {"success": False, "msg": "impyla not installed"}
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(ddl)
            return {"success": True, "ddl": ddl}
        except Exception as exc:
            return {"success": False, "msg": str(exc)}
        finally:
            cursor.close()

    def table_exists(self, db: str, table: str) -> bool:
        if not self.is_available:
            return False
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(f"SHOW TABLES IN {db} LIKE '{table}'")
            rows = cursor.fetchall()
            return len(rows) > 0
        except Exception:
            return False
        finally:
            cursor.close()

    # ------------------------------------------------------------------
    # DML — upsert / delete
    # ------------------------------------------------------------------

    def upsert_rows(
        self,
        db: str,
        table: str,
        rows: list[dict[str, Any]],
        primary_keys: list[str] | None = None,
    ) -> dict[str, Any]:
        """Upsert rows into a Kudu table via Impala.

        Uses INSERT ... VALUES with per-row statements. For bulk operations,
        batch INSERT is used when available (Impala 3.0+).
        """
        if not rows:
            return {"success": True, "upserted": 0}
        if not self.is_available:
            return {"success": False, "msg": "impyla not installed"}

        columns = list(rows[0].keys())
        col_list = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))
        sql = f"UPSERT INTO {db}.{table} ({col_list}) VALUES ({placeholders})"

        conn = self._connect()
        cursor = conn.cursor()
        success_count = 0
        try:
            for row in rows:
                values = [row[col] for col in columns]
                cursor.execute(sql, values)
                success_count += 1
            return {"success": True, "upserted": success_count}
        except Exception as exc:
            return {"success": False, "upserted": success_count, "msg": str(exc)}
        finally:
            cursor.close()

    def delete_rows(
        self,
        db: str,
        table: str,
        key_values: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Delete rows by primary key from a Kudu table."""
        if not key_values:
            return {"success": True, "deleted": 0}
        if not self.is_available:
            return {"success": False, "msg": "impyla not installed"}

        conn = self._connect()
        cursor = conn.cursor()
        deleted = 0
        try:
            for kv in key_values:
                where = " AND ".join(f"{k} = %s" for k in kv)
                sql = f"DELETE FROM {db}.{table} WHERE {where}"
                cursor.execute(sql, list(kv.values()))
                deleted += 1
            return {"success": True, "deleted": deleted}
        except Exception as exc:
            return {"success": False, "deleted": deleted, "msg": str(exc)}
        finally:
            cursor.close()
