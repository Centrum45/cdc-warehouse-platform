# 提交范围说明

本文用于提交前检查，避免把本地运行数据、缓存或临时产物误提交。

## 应提交

- 项目源码：`platform/`、`warehouse/`、`streaming/`、`warehouse/storage/`、`warehouse/spark_runtime/`、`realtime/`、`ingestion/`、`monitors/`、`configs/`。
- 部署脚本：`deploy/`、`docker/`、`scripts/`。
- 元数据、SQL、调度定义：`metadata/`、`warehouse/sql/`、`warehouse/scheduler/`。
- 文档：`README.md`、`docs/`。
- CI 和依赖声明：`.github/workflows/ci.yml`、`requirements.txt`、`.gitignore`。

## 应删除并提交

这些是历史遗留或本地模拟代码，当前生产/本地统一链路不再使用，删除属于有效改动：

- `platform/springboot-admin/.m2/`：Maven 本地仓库缓存，不应该进入 Git。
- 旧 JSONL/CSV 本地模拟链路脚本，例如 `scripts/run_local_pipeline.sh`、`streaming/offline_sink/kafka_to_local_lake.py`。
- 旧 loop/once 桥接脚本，例如 `scripts/spark_streaming_kafka_to_hdfs_loop.py`、`scripts/sync_lake_to_hdfs.sh`。
- 旧 mock 数据生成脚本，例如 `ingestion/mock/generate_binlog_events.py`。
- 已被新文档覆盖的旧选型文档，例如 `docs/realtime_engine_selection_zh.md`。

## 不应提交

这些是运行产物或本地私有配置，已在 `.gitignore` 中忽略：

- `.env`、`docker/.env`。
- `.venv/`、`.venv-kudu/`。
- `data/` 下的 Kafka、HDFS、Hive、checkpoint、ops、monitor、alert、runtime 数据。
- `platform/springboot-admin/target/`。
- `docker/hadoop/dist/`、`docker/hive/dist/` 下载包。
- `__pycache__/`、`.pytest_cache/`、`*.pyc`。

## 提交前检查

```bash
git status --short
./scripts/check_dependencies.sh --mode local
./scripts/test.sh
mvn -q -B -f platform/springboot-admin/pom.xml compile
python3 scripts/validate_deployment_config.py
docker compose -f docker/docker-compose.yml -f docker/docker-compose.hive.yml config --quiet
docker compose -f docker/docker-compose.kudu.yml config --quiet
./scripts/verify_end_to_end.sh
```

如果 `git status --short` 中出现 `data/`、`.env`、`.venv/`、`target/`，不要提交。
