from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class HdfsPath:
    value: str

    def __truediv__(self, child: str) -> "HdfsPath":
        return HdfsPath(self.value.rstrip("/") + "/" + child.strip("/"))

    @property
    def parent(self) -> "HdfsPath":
        parsed = urlparse(self.value)
        path = parsed.path.rstrip("/")
        parent_path = path.rsplit("/", 1)[0] or "/"
        return HdfsPath(urlunparse((parsed.scheme, parsed.netloc, parent_path, "", "", "")))

    def __str__(self) -> str:
        return self.value


class WebHdfsLake:
    """Small WebHDFS adapter for local Docker HDFS writes."""

    def __init__(self, root: str) -> None:
        parsed = urlparse(root)
        if parsed.scheme != "hdfs":
            raise ValueError(f"expected hdfs:// root, got {root}")
        self.root = HdfsPath(root.rstrip("/"))
        host = parsed.hostname or "localhost"
        self._namenode_host = host
        endpoint = os.environ.get("WEBHDFS_ENDPOINT", f"http://{host}:9870").rstrip("/")
        self._http_base = f"{endpoint}/webhdfs/v1"
        self._user = os.environ.get("WEBHDFS_USER", "root")

    def binlog_partition(self, database: str, table: str, dt: str) -> HdfsPath:
        return self.root / "ods_binlog" / f"db={database}" / f"table={table}" / f"dt={dt}"

    def ods_partition(self, database: str, table: str, dt: str) -> HdfsPath:
        return self.root / "ods" / f"db={database}" / f"table={table}" / f"dt={dt}"

    def read_text(self, path: HdfsPath) -> str:
        data = self.read_bytes(path)
        return data.decode("utf-8") if data else ""

    def read_bytes(self, path: HdfsPath) -> bytes:
        request = Request(self._url(path, "OPEN"), method="GET")
        opener = build_opener(_NoRedirect)
        try:
            with opener.open(request, timeout=20) as response:
                return response.read()
        except HTTPError as exc:
            if exc.code == 404:
                return b""
            if exc.code in (307, 308):
                location = self._rewrite_redirect(exc.headers["Location"])
                with urlopen(location, timeout=30) as response:
                    return response.read()
            raise

    def write_text(self, path: HdfsPath, text: str) -> None:
        self.write_bytes(path, text.encode("utf-8"))

    def write_bytes(self, path: HdfsPath, data: bytes) -> None:
        self.mkdirs(path.parent)
        create_url = self._url(path, "CREATE", overwrite="true")
        request = Request(create_url, method="PUT")
        try:
            urlopen(request, timeout=20)
        except HTTPError as exc:
            if exc.code != 307:
                raise
            location = self._rewrite_redirect(exc.headers["Location"])
            put_request = Request(location, data=data, method="PUT")
            with urlopen(put_request, timeout=30):
                return
        raise RuntimeError(f"WebHDFS CREATE did not redirect: {path}")

    def mkdirs(self, path: HdfsPath) -> None:
        request = Request(self._url(path, "MKDIRS"), method="PUT")
        with urlopen(request, timeout=20):
            return

    def exists(self, path: HdfsPath) -> bool:
        try:
            with urlopen(self._url(path, "GETFILESTATUS"), timeout=20):
                return True
        except HTTPError as exc:
            if exc.code == 404:
                return False
            raise

    def delete(self, path: HdfsPath, recursive: bool = False) -> None:
        try:
            request = Request(self._url(path, "DELETE", recursive=str(recursive).lower()), method="DELETE")
            with urlopen(request, timeout=20):
                return
        except HTTPError as exc:
            if exc.code == 404:
                return
            raise

    def list_status(self, path: HdfsPath) -> list[dict[str, Any]]:
        try:
            with urlopen(self._url(path, "LISTSTATUS"), timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                return []
            raise
        return payload.get("FileStatuses", {}).get("FileStatus", [])

    def _url(self, path: HdfsPath, op: str, **params: str) -> str:
        parsed = urlparse(path.value)
        query = urlencode({"op": op, "user.name": self._user, **params})
        return f"{self._http_base}{parsed.path}?{query}"

    def _rewrite_redirect(self, location: str) -> str:
        parsed = urlparse(location)
        if self._namenode_host in {"localhost", "127.0.0.1"}:
            netloc = f"{self._namenode_host}:{parsed.port or 9864}"
        elif parsed.hostname in {"localhost", "127.0.0.1", "0.0.0.0"}:
            netloc = f"hdfs-datanode:{parsed.port or 9864}"
        else:
            return location
        return urlunparse((parsed.scheme, netloc, parsed.path, "", parsed.query, ""))


def is_hdfs_root(root: str | Any) -> bool:
    return str(root).startswith("hdfs://")
