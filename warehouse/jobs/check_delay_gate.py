from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from configs.loader import load_config
from warehouse.jobs.delay_gate import can_merge


def main() -> None:
    config = load_config()

    delay_cfg = config.get("delay_gate", {})
    configured_root = delay_cfg.get("progress_root", "data/progress")
    progress_root = configured_root if str(configured_root).startswith("hdfs://") else Path(configured_root)
    max_delay_seconds = delay_cfg.get("max_delay_seconds", 900)
    enabled = delay_cfg.get("enabled", True)

    if not enabled:
        print("delay gate disabled — merge allowed")
        sys.exit(0)

    metadata_path = Path("metadata/tables/basiccomment.avatar_commentbatchsource.json")
    if not metadata_path.exists():
        print("no metadata — merge allowed (no table to check)")
        sys.exit(0)

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    allowed, reason = can_merge(
        progress_root,
        metadata["source_database"],
        metadata["source_table"],
        max_delay_seconds,
    )
    print(reason)
    if not allowed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
