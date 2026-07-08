from __future__ import annotations

import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from admin_platform.onboarding.table_onboarding import onboard_table


def main() -> None:
    bootstrap = "--bootstrap" in sys.argv
    merge_bootstrap = "--merge-bootstrap" in sys.argv
    args = [arg for arg in sys.argv[1:] if arg not in {"--bootstrap", "--merge-bootstrap"}]

    dba_metadata_path = Path(args[0]) if len(args) > 0 else Path("metadata/dba/basiccomment.avatar_commentbatchsource.json")
    primary_keys = args[1].split(",") if len(args) > 1 else ["id"]
    version_column = args[2] if len(args) > 2 else "ver"
    partition_column = args[3] if len(args) > 3 else "ctime"
    outputs = onboard_table(dba_metadata_path, Path("."), primary_keys, version_column, partition_column)
    for name, path in outputs.items():
        print(f"{name}: {path}")
    if bootstrap:
        command = ["python3", "scripts/bootstrap_mysql_table.py", str(outputs["metadata"])]
        if merge_bootstrap:
            command.extend(["--replace-binlog", "--replace-ods"])
        subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
