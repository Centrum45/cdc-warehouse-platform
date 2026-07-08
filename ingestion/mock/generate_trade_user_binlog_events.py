from __future__ import annotations

import json
from pathlib import Path


def events() -> list[dict]:
    return [
        {
            "database": "user",
            "table": "user_info",
            "type": "insert",
            "ts": 1783267200,
            "xid": 2001,
            "data": {
                "id": 501,
                "user_name": "alice",
                "mobile": "13800000000",
                "email": "alice@example.com",
                "register_time": "2026-07-01 00:00:00",
                "ctime": "2026-07-01 00:00:00",
                "utime": "2026-07-01 00:00:00",
                "ver": 1
            }
        },
        {
            "database": "trade",
            "table": "order_info",
            "type": "insert",
            "ts": 1783270800,
            "xid": 2002,
            "data": {
                "id": 1001,
                "user_id": 501,
                "order_no": "O20260706001",
                "pay_amount": 128.5,
                "order_status": "PAID",
                "ctime": "2026-07-06 10:00:00",
                "utime": "2026-07-06 10:05:00",
                "ver": 1
            }
        }
    ]


def main() -> None:
    output = Path("data/kafka/cdc.trade_user.binlog.jsonl")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(json.dumps(event, sort_keys=True) for event in events()) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
