from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]


class Handler(BaseHTTPRequestHandler):
    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/health":
            self._json({"status": "ok"})
            return
        if path == "/metadata/tables":
            tables = sorted(str(path.name) for path in (ROOT / "metadata/tables").glob("*.json"))
            self._json({"tables": tables})
            return
        if path == "/tasks":
            self._json({
                "tasks": [
                    {"name": "offline_sink", "type": "streaming", "target": "ods_binlog"},
                    {"name": "ods_merge", "type": "batch", "target": "ods"},
                    {"name": "warehouse_daily", "type": "batch", "target": "dim/dwd/dws/ads"}
                ]
            })
            return
        self._json({"error": "not found"}, 404)


def main() -> None:
    server = HTTPServer(("127.0.0.1", 8000), Handler)
    print("http://127.0.0.1:8000")
    server.serve_forever()


if __name__ == "__main__":
    main()

