from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from monitors.field_monitor_job import diff_columns
from monitors.notifier import Notifier
from monitors.result_store import MonitorResultStore
from warehouse.jobs.delay_gate import can_merge


def run_suite() -> None:
    store = MonitorResultStore()
    notifier = Notifier()

    allowed, reason = can_merge("data/progress", "basiccomment", "avatar_commentbatchsource", 999999999)
    store.append("delay", "basiccomment", "avatar_commentbatchsource", "OK" if allowed else "FAIL", reason)
    if not allowed:
        notifier.send("dingtalk", "dba", "CDC delay alert", reason)

    missing = diff_columns(
        Path("metadata/tables/basiccomment.avatar_commentbatchsource.json"),
        Path("metadata/dba/basiccomment.avatar_commentbatchsource.json")
    )
    status = "OK" if not missing else "WARN"
    message = "metadata aligned" if not missing else f"missing columns: {[column['name'] for column in missing]}"
    store.append("field", "basiccomment", "avatar_commentbatchsource", status, message, len(missing))
    if missing:
        notifier.send("email", "dba@example.com", "CDC field drift", message)

    print(store.path)


if __name__ == "__main__":
    run_suite()
