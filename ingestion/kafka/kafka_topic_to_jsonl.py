from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def export_topic_to_jsonl(
    topic: str,
    output_path: Path,
    bootstrap_server: str = "kafka:9092",
    container: str = "cdc-warehouse-kafka",
    max_messages: int = 100
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "docker",
        "exec",
        container,
        "kafka-console-consumer",
        "--bootstrap-server",
        bootstrap_server,
        "--topic",
        topic,
        "--from-beginning",
        "--max-messages",
        str(max_messages),
        "--timeout-ms",
        "10000",
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    if completed.returncode not in (0, 1):
        raise RuntimeError(completed.stderr or completed.stdout)
    lines = [line for line in completed.stdout.splitlines() if line.strip().startswith("{")]
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return output_path


def main() -> None:
    topic = sys.argv[1] if len(sys.argv) > 1 else "cdc.incremental.binlog"
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/kafka/cdc.incremental.binlog.jsonl")
    max_messages = int(sys.argv[3]) if len(sys.argv) > 3 else 100
    print(export_topic_to_jsonl(topic, output, max_messages=max_messages))


if __name__ == "__main__":
    main()
