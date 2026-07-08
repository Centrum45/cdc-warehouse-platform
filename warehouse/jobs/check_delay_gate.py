from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from warehouse.jobs.delay_gate import can_merge


def main() -> None:
    config_path = Path("configs/app.yaml")
    progress_root = Path("data/progress")
    max_delay_seconds = 900
    if config_path.exists():
        text = config_path.read_text(encoding="utf-8")
        if "progress_root: data/progress" in text:
            progress_root = Path("data/progress")
        if "max_delay_seconds: 900" in text:
            max_delay_seconds = 900

    metadata_path = Path("metadata/tables/basiccomment.avatar_commentbatchsource.json")
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    allowed, reason = can_merge(
        progress_root,
        metadata["source_database"],
        metadata["source_table"],
        max_delay_seconds
    )
    print(reason)
    if not allowed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
