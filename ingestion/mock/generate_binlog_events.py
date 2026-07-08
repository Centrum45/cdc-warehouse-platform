from __future__ import annotations

import json
from pathlib import Path


def build_events() -> list[dict]:
    return [
        {
            "database": "basiccomment",
            "table": "avatar_commentbatchsource",
            "type": "bootstrap-insert",
            "ts": 1783267200,
            "xid": 1001,
            "data": {
                "id": 1,
                "batchnumber": "B20260706001",
                "batchtype": "normal",
                "ctime": "2026-07-06 09:00:00",
                "utime": "2026-07-06 09:00:00",
                "ver": 1
            }
        },
        {
            "database": "basiccomment",
            "table": "avatar_commentbatchsource",
            "type": "insert",
            "ts": 1783270800,
            "xid": 1002,
            "data": {
                "id": 2,
                "batchnumber": "B20260706002",
                "batchtype": "normal",
                "ctime": "2026-07-06 10:00:00",
                "utime": "2026-07-06 10:00:00",
                "ver": 1
            }
        },
        {
            "database": "basiccomment",
            "table": "avatar_commentbatchsource",
            "type": "update",
            "ts": 1783274400,
            "xid": 1003,
            "data": {
                "id": 2,
                "batchnumber": "B20260706002",
                "batchtype": "priority",
                "ctime": "2026-07-06 10:00:00",
                "utime": "2026-07-06 11:00:00",
                "ver": 2
            },
            "old": {"batchtype": "normal", "utime": "2026-07-06 10:00:00", "ver": 1}
        },
        {
            "database": "basiccomment",
            "table": "avatar_commentbatchsource",
            "type": "delete",
            "ts": 1783278000,
            "xid": 1004,
            "data": {
                "id": 1,
                "batchnumber": "B20260706001",
                "batchtype": "normal",
                "ctime": "2026-07-06 09:00:00",
                "utime": "2026-07-06 12:00:00",
                "ver": 2
            }
        }
    ]


def main() -> None:
    output = Path("data/kafka/cdc.incremental.binlog.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as fp:
        for event in build_events():
            fp.write(json.dumps(event, ensure_ascii=False, sort_keys=True))
            fp.write("\n")
    print(output)


if __name__ == "__main__":
    main()

