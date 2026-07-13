from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from monitors.notifier import Notifier


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a CDC Warehouse test alert.")
    parser.add_argument("--channel", default="", help="file/stdout/email/dingtalk/wechat/feishu. Empty uses ALERT_CHANNELS.")
    parser.add_argument("--target", default="", help="email address or target label")
    parser.add_argument("--title", default="CDC Warehouse test alert")
    parser.add_argument("--body", default="Alert channel check from CDC Warehouse Platform.")
    args = parser.parse_args()

    notifier = Notifier()
    if args.channel:
        outbox = notifier.send(args.channel, args.target, args.title, args.body)
    else:
        outbox = notifier.send_default(args.title, args.body, args.target)
    print(outbox)


if __name__ == "__main__":
    main()
