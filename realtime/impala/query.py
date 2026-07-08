from __future__ import annotations

"""
Impala query client for realtime analytics.

Uses impyla to execute SQL queries against the Impala daemon.

Installation:
    pip install impyla thrift-sasl
"""

import os
from typing import Any


class ImpalaQuery:
    """Read path: run analytical queries against Impala / Kudu tables."""

    def __init__(
        self,
        host: str | None = None,
        port: int = 21050,
    ) -> None:
        self.host = host or os.environ.get("IMPALA_HOST", "localhost")
        self.port = port or int(os.environ.get("IMPALA_PORT", "21050"))
        self._conn = None

    @property
    def is_available(self) -> bool:
        try:
            import impala.dbapi  # noqa: F401
            return True
        except ModuleNotFoundError:
            return False

    def _connect(self):
        if self._conn is not None:
            return self._conn
        try:
            import impala.dbapi
        except ModuleNotFoundError:
            raise RuntimeError(
                "impyla not installed. Run: pip install impyla thrift-sasl"
            )
        self._conn = impala.dbapi.connect(host=self.host, port=self.port)
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except Exception:
                pass
            self._conn = None

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, sql: str) -> list[dict[str, Any]]:
        """Execute a SELECT query and return rows as dicts."""
        if not self.is_available:
            raise RuntimeError("impyla not installed")
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()

    def execute(self, sql: str) -> dict[str, Any]:
        """Execute a DDL / DML statement (CREATE VIEW, REFRESH, etc.)."""
        if not self.is_available:
            return {"success": False, "msg": "impyla not installed"}
        conn = self._connect()
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            return {"success": True, "sql": sql[:80]}
        except Exception as exc:
            return {"success": False, "msg": str(exc)}
        finally:
            cursor.close()

    # ------------------------------------------------------------------
    # View management
    # ------------------------------------------------------------------

    def create_view(self, view_sql: str) -> dict[str, Any]:
        """Create (or replace) an Impala view."""
        return self.execute(view_sql)

    def refresh(self, db: str, table: str) -> dict[str, Any]:
        """Refresh Impala metadata for a Kudu table."""
        return self.execute(f"INVALIDATE METADATA {db}.{table}")

    def compute_invalidations(self, db: str, table: str) -> dict[str, Any]:
        """Update Impala metadata for a Kudu table (lighter than INVALIDATE)."""
        return self.execute(f"REFRESH {db}.{table}")

    # ------------------------------------------------------------------
    # Higher-level analytics
    # ------------------------------------------------------------------

    def run_view(self, db: str, view: str) -> list[dict[str, Any]]:
        """Run a pre-defined view and return results."""
        return self.query(f"SELECT * FROM {db}.{view}")
