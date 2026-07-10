#!/usr/bin/env python3
"""Static deployment checks for CI.

These checks catch broken deployment docs/env examples before a server install.
They do not contact MySQL, Kafka, HDFS, Hive, or Docker.
"""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def check_code_fences():
    for path in [
        "README.md",
        "docs/deployment_guide.md",
        "docs/deployment_guide_zh.md",
        "docs/production_checklist.md",
        "docs/realtime_kudu_impala.md",
        "deploy/server/README.md",
    ]:
        text = read(path)
        require(text.count("```") % 2 == 0, f"{path}: unmatched markdown code fence")


def parse_env(path):
    values = {}
    for line in read(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def check_env_examples():
    admin_required = {
        "SPRING_PROFILES_ACTIVE",
        "WAREHOUSE_PROJECT_ROOT",
        "WAREHOUSE_ACTIONS_PUBLIC_ENABLED",
        "DB_HOST",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "ADMIN_USER",
        "ADMIN_PASS",
        "JWT_SECRET",
        "HIVE_JDBC_URL",
    }
    jobs_required = {
        "ENVIRONMENT",
        "KAFKA_BOOTSTRAP_SERVERS",
        "KAFKA_TOPIC",
        "LAKE_ROOT",
        "WAREHOUSE_HDFS_ROOT",
        "PROGRESS_ROOT",
        "DELAY_GATE_MAX_SECONDS",
    }
    for path in ["deploy/server/admin.env.example", "deploy/prod/admin.env.example"]:
        env = parse_env(path)
        missing = sorted(admin_required - env.keys())
        require(not missing, f"{path}: missing {missing}")
        require(env["SPRING_PROFILES_ACTIVE"] == "prod", f"{path}: profile must be prod")
        require(env["WAREHOUSE_ACTIONS_PUBLIC_ENABLED"] == "false", f"{path}: public actions must be false")
        require(env["ADMIN_PASS"] != "admin123", f"{path}: default admin password forbidden")
    for path in ["deploy/server/jobs.env.example", "deploy/prod/jobs.env.example"]:
        env = parse_env(path)
        missing = sorted(jobs_required - env.keys())
        require(not missing, f"{path}: missing {missing}")
        require(env["ENVIRONMENT"] == "prod", f"{path}: environment must be prod")


def check_docs_reference_preflight():
    for path in ["README.md", "docs/deployment_guide.md", "docs/deployment_guide_zh.md", "deploy/server/README.md"]:
        text = read(path)
        require("control.sh preflight" in text, f"{path}: missing preflight command")
    checklist = read("docs/production_checklist.md")
    for token in [
        "SPRING_PROFILES_ACTIVE=prod",
        "WAREHOUSE_ACTIONS_PUBLIC_ENABLED=false",
        "ADMIN_PASS",
        "JWT_SECRET",
        "control.sh preflight",
    ]:
        require(token in checklist, f"docs/production_checklist.md: missing {token}")


def check_control_script():
    control = read("deploy/server/control.sh")
    require("preflight)" in control, "control.sh: missing preflight action")
    require("preflight.sh" in control, "control.sh: missing preflight.sh call")
    preflight = read("deploy/server/preflight.sh")
    for token in [
        "SPRING_PROFILES_ACTIVE must be prod",
        "WAREHOUSE_ACTIONS_PUBLIC_ENABLED must be false",
        "ADMIN_PASS must not use default admin123",
        "JWT_SECRET must be at least 32 characters",
    ]:
        require(token in preflight, f"preflight.sh: missing guard {token}")


def main():
    check_code_fences()
    check_env_examples()
    check_docs_reference_preflight()
    check_control_script()
    print("deployment config checks ok")


if __name__ == "__main__":
    main()
