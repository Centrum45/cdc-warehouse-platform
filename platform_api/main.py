"""
CDC Warehouse Platform — REST API server.
Serves metadata, tasks, monitors, replay, dashboard, and data lake queries.
"""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

METADATA_TABLES = ROOT / "metadata" / "tables"
METADATA_DBA = ROOT / "metadata" / "dba"
METADATA_RULES = ROOT / "metadata" / "rules"
DATA_PLATFORM = ROOT / "data" / "platform"
LAKE_ROOT = ROOT / "data" / "lake"
MONITOR_CSV = ROOT / "data" / "monitor" / "monitor_result.csv"


def _load_json(path: Path) -> dict | list:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _load_json_safe(path: Path) -> dict | list:
    """Load JSON, return empty dict/list if file missing."""
    if not path.exists():
        return [] if path.name.endswith("s.json") or "items" in path.name else {}
    return _load_json(path)


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _find_lake_dir(path: Path) -> list[str]:
    """List subdirectories stripping partition prefix, e.g. dt=2026-07-06 -> 2026-07-06."""
    if not path.exists():
        return []
    result = []
    for p in sorted(path.iterdir()):
        if p.is_dir():
            name = p.name
            result.append(name.split("=", 1)[1] if "=" in name else name)
    return result


# ── Handler ──────────────────────────────────────────────────────────

class APIHandler(BaseHTTPRequestHandler):
    """REST handler with routing."""

    def log_message(self, format, *args):
        """Quieter logging."""
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}")

    # ── helpers ──────────────────────────────────────────────────

    def _json(self, payload, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> dict:
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def _path_parts(self) -> list[str]:
        path = urlparse(self.path).path
        return [p for p in path.split("/") if p]

    def _query(self) -> dict[str, list[str]]:
        return parse_qs(urlparse(self.path).query)

    # ── CORS ─────────────────────────────────────────────────────

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    # ── routing ──────────────────────────────────────────────────

    def do_GET(self):
        parts = self._path_parts()

        # health
        if parts == ["health"] or parts == []:
            return self._json({"status": "ok", "service": "cdc-warehouse-platform",
                               "version": "1.0.0", "dt": os.environ.get("BIZ_DT", "2026-07-06")})

        # /api/...
        if len(parts) >= 2 and parts[0] == "api":
            return self._route_get(parts[1:])

        self._json({"error": "not found"}, 404)

    def do_POST(self):
        parts = self._path_parts()
        if len(parts) >= 2 and parts[0] == "api":
            return self._route_post(parts[1:])
        self._json({"error": "not found"}, 404)

    # ── GET routes ───────────────────────────────────────────────

    def _route_get(self, parts: list[str]):
        resource = parts[0]

        # /api/metadata/...
        if resource == "metadata":
            return self._get_metadata(parts[1:])

        # /api/tasks
        if resource == "tasks":
            return self._get_tasks(parts[1:])

        # /api/monitors
        if resource == "monitors":
            return self._get_monitors(parts[1:])

        # /api/replay
        if resource == "replay":
            return self._get_replay(parts[1:])

        # /api/dashboard
        if resource == "dashboard":
            return self._get_dashboard()

        # /api/data/...
        if resource == "data":
            return self._get_data(parts[1:])

        # /api/pipeline/status
        if resource == "pipeline":
            return self._get_pipeline_status()

        # /api/layers - list all data layers with partition info
        if resource == "layers":
            return self._get_layers()

        self._json({"error": f"unknown resource: {resource}"}, 404)

    def _route_post(self, parts: list[str]):
        resource = parts[0]

        if resource == "monitors" and len(parts) >= 2 and parts[1] == "run":
            return self._post_monitor_run()

        if resource == "replay" and len(parts) >= 2 and parts[1] == "run":
            return self._post_replay_run()

        if resource == "pipeline" and len(parts) >= 2 and parts[1] == "run":
            return self._post_pipeline_run()

        if resource == "tasks":
            return self._post_task()

        self._json({"error": "not found"}, 404)

    # ── Metadata ─────────────────────────────────────────────────

    def _get_metadata(self, parts: list[str]):
        if not parts or parts == [""]:
            # list all table metadata
            tables = []
            for path in sorted(METADATA_TABLES.glob("*.json")):
                meta = _load_json(path)
                tables.append({
                    "qualified_name": path.stem,
                    "source_database": meta.get("source_database", ""),
                    "source_table": meta.get("source_table", ""),
                    "primary_keys": meta.get("primary_keys", []),
                    "columns": len(meta.get("columns", [])),
                    "ods_table": meta.get("ods_table", ""),
                })
            return self._json({"tables": tables, "count": len(tables)})

        if parts[0] == "dba":
            dba_tables = []
            for path in sorted(METADATA_DBA.glob("*.json")):
                meta = _load_json(path)
                dba_tables.append({
                    "qualified_name": path.stem,
                    "source_database": meta.get("source_database", ""),
                    "source_table": meta.get("source_table", ""),
                    "columns": len(meta.get("columns", [])),
                })
            return self._json({"dba_tables": dba_tables, "count": len(dba_tables)})

        if parts[0] == "rules":
            rules = {}
            for path in sorted(METADATA_RULES.glob("*.json")):
                key = path.stem
                rules[key] = _load_json(path)
            return self._json({"rules": rules})

        # specific table
        table_name = parts[0]
        table_path = METADATA_TABLES / f"{table_name}.json"
        if not table_path.exists():
            return self._json({"error": f"table not found: {table_name}"}, 404)

        meta = _load_json(table_path)

        # also load DBA metadata for comparison
        dba_path = METADATA_DBA / f"{table_name}.json"
        dba_meta = _load_json(dba_path) if dba_path.exists() else None

        # enrich with platform metadata
        platform_meta = _load_json_safe(DATA_PLATFORM / "table_metadata.json")
        platform_info = None
        if isinstance(platform_meta, list):
            for pm in platform_meta:
                if (pm.get("databaseName") == meta.get("source_database") and
                        pm.get("tableName") == meta.get("source_table")):
                    platform_info = pm
                    break

        return self._json({
            "metadata": meta,
            "dba_metadata": dba_meta,
            "platform_config": platform_info,
            "column_diff": _compute_column_diff(meta, dba_meta) if dba_meta else None,
        })

    # ── Tasks ────────────────────────────────────────────────────

    def _get_tasks(self, parts: list[str]):
        tasks = _load_json_safe(DATA_PLATFORM / "task_configs.json")
        if isinstance(tasks, dict):
            tasks = [tasks]

        if parts and parts[0]:
            task_id = int(parts[0])
            for t in tasks:
                if t.get("id") == task_id:
                    return self._json(t)
            return self._json({"error": f"task not found: {task_id}"}, 404)

        return self._json({"tasks": tasks, "count": len(tasks)})

    def _post_task(self):
        body = self._read_body()
        tasks = _load_json_safe(DATA_PLATFORM / "task_configs.json")
        if isinstance(tasks, dict):
            tasks = [tasks]
        if not isinstance(tasks, list):
            tasks = []

        new_id = max((t.get("id", 0) for t in tasks), default=0) + 1
        body["id"] = new_id
        tasks.append(body)

        DATA_PLATFORM.mkdir(parents=True, exist_ok=True)
        with (DATA_PLATFORM / "task_configs.json").open("w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

        return self._json(body, 201)

    # ── Monitors ─────────────────────────────────────────────────

    def _get_monitors(self, parts: list[str]):
        if parts and parts[0] == "results":
            rows = _read_csv(MONITOR_CSV)
            return self._json({"results": rows, "count": len(rows)})

        monitors_data = _load_json_safe(DATA_PLATFORM / "monitor_items.json")
        monitors = monitors_data.get("monitors", []) if isinstance(monitors_data, dict) else monitors_data

        if parts and parts[0]:
            mon_id = int(parts[0])
            for m in monitors:
                if m.get("id") == mon_id:
                    return self._json(m)
            return self._json({"error": f"monitor not found: {mon_id}"}, 404)

        return self._json({"monitors": monitors, "count": len(monitors)})

    def _post_monitor_run(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "monitors" / "run_monitor_suite.py")],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30
        )
        return self._json({
            "success": result.returncode == 0,
            "stdout": result.stdout.strip().split("\n")[-10:],
            "stderr": result.stderr.strip(),
        })

    # ── Replay ───────────────────────────────────────────────────

    def _get_replay(self, parts: list[str]):
        platform_meta = _load_json_safe(DATA_PLATFORM / "table_metadata.json")
        if isinstance(platform_meta, list):
            replayable = [
                {"databaseName": pm["databaseName"], "tableName": pm["tableName"],
                 "primaryKeys": pm.get("primaryKeys", ""),
                 "enabled": pm.get("enabled", False)}
                for pm in platform_meta
            ]
        else:
            replayable = []
        return self._json({"replayable_tables": replayable, "count": len(replayable)})

    def _post_replay_run(self):
        body = self._read_body()
        database = body.get("database", "basiccomment")
        table = body.get("table", "avatar_commentbatchsource")
        result = subprocess.run(
            [sys.executable, str(ROOT / "replay" / "replay_runner.py"),
             database, table],
            capture_output=True, text=True, cwd=str(ROOT), timeout=30
        )
        return self._json({
            "success": result.returncode == 0,
            "database": database,
            "table": table,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        })

    # ── Dashboard ────────────────────────────────────────────────

    def _get_dashboard(self):
        """Aggregate dashboard from all ADS outputs."""
        dt = os.environ.get("BIZ_DT", "2026-07-06")
        metrics = {}

        # Comment dashboard
        comment_path = LAKE_ROOT / "ads" / "ads_comment_dashboard_1d" / f"dt={dt}" / "part-00000.csv"
        for row in _read_csv(comment_path):
            metrics[row.get("metric_name", "")] = row.get("metric_value", "")

        # Trade dashboard
        trade_path = LAKE_ROOT / "ads" / "ads_trade_dashboard_1d" / f"dt={dt}" / "part-00000.csv"
        for row in _read_csv(trade_path):
            metrics[row.get("metric_name", "")] = row.get("metric_value", "")

        # Layer status
        layers_status = {}
        for layer in ["ods", "dim", "dwd", "dws", "dwt", "ads"]:
            layer_dir = LAKE_ROOT / layer
            if layer_dir.exists():
                tables = [d.name for d in layer_dir.iterdir() if d.is_dir()]
                layers_status[layer] = {
                    "table_count": len(tables),
                    "has_data": len(tables) > 0,
                }
            else:
                layers_status[layer] = {"table_count": 0, "has_data": False}

        return self._json({
            "biz_dt": dt,
            "metrics": metrics,
            "layers": layers_status,
        })

    # ── Data lake ────────────────────────────────────────────────

    def _get_data(self, parts: list[str]):
        """Browse data lake: /api/data/{layer}[/{table}][?dt=2026-07-06]"""
        query = self._query()
        dt = query.get("dt", [os.environ.get("BIZ_DT", "2026-07-06")])[0]

        if not parts or not parts[0]:
            # list all layers
            layers = []
            for d in sorted(LAKE_ROOT.iterdir()):
                if d.is_dir():
                    tables = [t.name for t in d.iterdir() if t.is_dir()]
                    layers.append({"layer": d.name, "tables": tables, "table_count": len(tables)})
            return self._json({"layers": layers})

        layer = parts[0]
        layer_dir = LAKE_ROOT / layer
        if not layer_dir.exists():
            return self._json({"error": f"layer not found: {layer}"}, 404)

        if len(parts) == 1:
            # list tables in layer
            tables = []
            for t in sorted(layer_dir.iterdir()):
                if t.is_dir():
                    partitions = _find_lake_dir(t)
                    tables.append({"table": t.name, "partitions": partitions,
                                   "latest_partition": partitions[-1] if partitions else None})
            return self._json({"layer": layer, "tables": tables})

        # specific table
        table = parts[1]
        table_dir = layer_dir / table
        if not table_dir.exists():
            return self._json({"error": f"table not found: {layer}/{table}"}, 404)

        # try specific dt, or latest
        dt_dir = table_dir / f"dt={dt}"
        if not dt_dir.exists():
            partitions = _find_lake_dir(table_dir)
            if partitions:
                dt_dir = table_dir / f"dt={partitions[-1]}"
                dt = partitions[-1]
            else:
                return self._json({"error": f"no data for {layer}/{table}"}, 404)

        csv_path = dt_dir / "part-00000.csv"
        if not csv_path.exists():
            return self._json({"error": f"no CSV at {csv_path}"}, 404)

        rows = _read_csv(csv_path)
        return self._json({
            "layer": layer, "table": table, "dt": dt,
            "rows": rows, "count": len(rows),
        })

    # ── Layers ───────────────────────────────────────────────────

    def _get_layers(self):
        query = self._query()
        dt = query.get("dt", [os.environ.get("BIZ_DT", "2026-07-06")])[0]

        layers = []
        for layer_name in ["ods", "dim", "dwd", "dws", "dwt", "ads"]:
            layer_dir = LAKE_ROOT / layer_name
            tables_info = []
            if layer_dir.exists():
                for t in sorted(layer_dir.iterdir()):
                    if t.is_dir():
                        p = t / f"dt={dt}" / "part-00000.csv"
                        row_count = 0
                        if p.exists():
                            row_count = len(_read_csv(p))
                        tables_info.append({"table": t.name, "rows": row_count, "has_data": row_count > 0})
            layers.append({
                "layer": layer_name,
                "tables": tables_info,
                "table_count": len(tables_info),
                "total_rows": sum(t["rows"] for t in tables_info),
            })

        return self._json({"layers": layers, "biz_dt": dt})

    # ── Pipeline ─────────────────────────────────────────────────

    def _get_pipeline_status(self):
        """Check which layers have data."""
        dt = os.environ.get("BIZ_DT", "2026-07-06")
        status = {}
        for layer in ["ods", "dim", "dwd", "dws", "dwt", "ads"]:
            layer_dir = LAKE_ROOT / layer
            has_data = False
            table_count = 0
            if layer_dir.exists():
                tables = [d for d in layer_dir.iterdir() if d.is_dir()]
                table_count = len(tables)
                has_data = any(
                    (t / f"dt={dt}" / "part-00000.csv").exists()
                    for t in tables
                )
            status[layer] = {"ready": has_data, "table_count": table_count}
        return self._json({"pipeline_status": status, "biz_dt": dt})

    def _post_pipeline_run(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "warehouse" / "jobs" / "run_full_pipeline.py")],
            capture_output=True, text=True, cwd=str(ROOT), timeout=60
        )
        return self._json({
            "success": result.returncode == 0,
            "stdout": result.stdout.strip().split("\n"),
            "stderr": result.stderr.strip(),
        })


# ── helpers ──────────────────────────────────────────────────────────

def _compute_column_diff(platform_meta: dict, dba_meta: dict) -> dict | None:
    """Compare platform table metadata columns vs DBA columns."""
    if not platform_meta or not dba_meta:
        return None

    plat_cols = {c["name"]: c.get("type", "") for c in platform_meta.get("columns", [])}
    dba_cols = {c["name"]: c.get("type", "") for c in dba_meta.get("columns", [])}

    only_platform = set(plat_cols.keys()) - set(dba_cols.keys())
    only_dba = set(dba_cols.keys()) - set(plat_cols.keys())
    type_diff = {
        col: {"platform": plat_cols[col], "dba": dba_cols[col]}
        for col in set(plat_cols.keys()) & set(dba_cols.keys())
        if plat_cols[col] != dba_cols[col]
    }

    if not only_platform and not only_dba and not type_diff:
        return {"status": "aligned", "diffs": {}}

    return {
        "status": "drift_detected",
        "diffs": {
            "only_in_platform": sorted(only_platform),
            "only_in_dba": sorted(only_dba),
            "type_mismatch": type_diff,
        }
    }


# ── main ─────────────────────────────────────────────────────────────

def main():
    port = int(os.environ.get("API_PORT", 8000))
    host = os.environ.get("API_HOST", "127.0.0.1")
    server = HTTPServer((host, port), APIHandler)
    print(f"CDC Warehouse API → http://{host}:{port}")
    print(f"  Dashboard : http://{host}:{port}/api/dashboard")
    print(f"  Data lake : http://{host}:{port}/api/data/ads")
    print(f"  Layers    : http://{host}:{port}/api/layers")
    print(f"  Pipeline  : http://{host}:{port}/api/pipeline/status")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
