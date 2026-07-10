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
from pathlib import Path
from typing import Any


class KuduClient:
    """Write path: upsert / delete rows in Kudu tables via Impala."""

    def __init__(
        self,
        impala_host: str | None = None,
        impala_port: int = 21050,
        kudu_masters: str | None = None,
        user: str | None = None,
        password: str | None = None,
        auth_mechanism: str | None = None,
        use_ssl: bool | None = None,
    ) -> None:
        self.impala_host = impala_host or os.environ.get("IMPALA_HOST", "localhost")
        self.impala_port = impala_port or int(os.environ.get("IMPALA_PORT", "21050"))
        self.kudu_masters = kudu_masters or os.environ.get("KUDU_MASTERS", "")
        self.user = user or os.environ.get("IMPALA_USER")
        self.password = password or os.environ.get("IMPALA_PASSWORD")
        self.auth_mechanism = auth_mechanism or os.environ.get("IMPALA_AUTH_MECHANISM")
        self.use_ssl = use_ssl if use_ssl is not None else os.environ.get("IMPALA_USE_SSL", "").lower() in ("1", "true", "yes")
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
        kwargs: dict[str, Any] = {"host": self.impala_host, "port": self.impala_port}
        if self.user:
            kwargs["user"] = self.user
        if self.password:
            kwargs["password"] = self.password
        if self.auth_mechanism:
            kwargs["auth_mechanism"] = self.auth_mechanism
        if self.use_ssl:
            kwargs["use_ssl"] = True
        self._conn = impala.dbapi.connect(**kwargs)
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
        return self.execute(ddl)

    def execute(self, sql: str) -> dict[str, Any]:
        """Execute DDL/DML against Impala."""
        if not self.is_available:
            return {"success": False, "msg": "impyla not installed"}
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            return {"success": True, "sql": sql[:120]}
        except Exception as exc:
            return {"success": False, "msg": str(exc)}
        finally:
            cursor.close()

    def create_database(self, db: str) -> dict[str, Any]:
        return self.execute(f"CREATE DATABASE IF NOT EXISTS {db}")

    def execute_file(self, path: Path) -> list[dict[str, Any]]:
        statements = [stmt.strip() for stmt in path.read_text(encoding="utf-8").split(";") if stmt.strip()]
        return [self.execute(stmt) for stmt in statements]

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
        columns = list(rows[0].keys())
        for row in rows:
            missing = [col for col in columns if col not in row]
            if missing:
                return {"success": False, "upserted": 0, "msg": f"missing columns: {missing}"}
        if not self.is_available:
            return {"success": False, "msg": "impyla not installed"}
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
