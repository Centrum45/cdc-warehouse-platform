# 实时数仓引擎选型

## 1. 结论

本项目当前实时链路使用 Kudu/Impala 是合理的，但不应把 Kudu 设计成唯一方案。

建议定位：

```text
默认可选方案：Kudu + Impala
本地调试方案：CSV simulation
可替换方案：Hudi / Iceberg / Delta / ClickHouse
```

当前项目的实时目标是：

```text
MySQL binlog
  -> Kafka
  -> SparkStreaming
  -> 按主键 upsert/delete
  -> 秒级/分钟级查询最新状态
```

这个目标和 Kudu 能力匹配。

## 2. 为什么 Kudu 合理

Kudu 适合 CDC 实时明细层，原因：

- 支持主键。
- 支持 UPSERT。
- 支持 DELETE。
- 和 Impala 集成好。
- 能做低延迟明细查询。
- 适合保存“最新状态表”。
- 比 Hive 普通表更适合频繁更新。

本项目里这些表天然适合 Kudu：

```text
basiccomment.avatar_commentbatchsource
trade.order_info
user.user_info
```

因为它们都有主键，并且 CDC 中会出现 insert/update/delete。

## 3. Kudu 的主要弊端

Kudu 不适合无脑上生产，主要问题：

- 运维成本高，需要 Kudu master/tablet server。
- 团队需要懂 tablet、partition、replica、compaction。
- 写入热点主键可能导致 tablet 热点。
- 对超大规模历史明细留存不是最优。
- Schema 演进能力不如湖仓格式灵活。
- Time travel、版本回溯能力弱。
- 如果公司没有 Kudu/Impala 集群，落地成本高。

## 4. 什么时候继续用 Kudu

满足这些条件时，用 Kudu 合理：

- 公司已有 Kudu/Impala 集群。
- 业务需要近实时最新状态查询。
- 数据有明确主键。
- CDC update/delete 比较多。
- 查询主要是明细查询、轻聚合、实时看板。
- 团队能维护 Kudu。

典型链路：

```text
Kafka -> SparkStreaming/Flink -> Kudu -> Impala -> 实时看板
```

## 5. 什么时候不要用 Kudu

这些情况建议不用 Kudu：

- 公司没有 Kudu 运维经验。
- 更关注统一湖仓架构。
- 主要需求是批流一体。
- 需要历史版本、time travel、schema evolution。
- 数据更多是追加型明细，不需要强 upsert。
- 查询压力主要是高并发 OLAP 聚合。

## 6. 替代方案对比

### 6.1 Hudi

适合：

- CDC upsert。
- 数据湖增量更新。
- 和 Spark/Flink 结合。
- 需要 MOR/COW 表。

优点：

- CDC 友好。
- 支持 upsert/delete。
- 湖仓生态较成熟。
- 适合离线和准实时统一。

缺点：

- 查询延迟通常高于 Kudu/ClickHouse。
- 表服务、compaction、cleaner 需要治理。

### 6.2 Iceberg

适合：

- 湖仓统一。
- 大规模离线分析。
- Schema 演进。
- Time travel。
- 多引擎查询。

优点：

- 当前主流湖仓方向。
- 表格式开放。
- 分区演进能力强。
- 多引擎支持好。

缺点：

- 高频 update/delete 实时写入成本较高。
- 秒级实时明细查询不是强项。

### 6.3 Delta Lake

适合：

- Spark 生态。
- 湖仓 ACID。
- 批流一体。

优点：

- ACID 体验好。
- Spark 结合紧。
- 使用门槛相对低。

缺点：

- 非 Spark 生态兼容性要看公司技术栈。
- 如果不是 Databricks/Spark 主导，选型要谨慎。

### 6.4 ClickHouse

适合：

- 高并发 OLAP 查询。
- 实时聚合看板。
- 明细宽表查询。

优点：

- 查询快。
- 聚合强。
- 运维经验更普遍。

缺点：

- 原生 update/delete 不如 Kudu/Hudi 直接。
- CDC 主键覆盖写需要 ReplacingMergeTree 等设计。
- 最终一致性语义需要解释清楚。

## 7. 本项目建议架构

推荐保持双路径：

```text
离线数仓：
MySQL -> Maxwell -> Kafka -> HDFS ods_binlog -> ODS merge -> Hive ADS

实时数仓：
MySQL -> Maxwell -> Kafka -> Realtime Sink -> Realtime Engine -> 查询引擎
```

其中 Realtime Engine 可配置：

```text
local_csv       本地调试
kudu_impala     当前默认真实方案
hudi            湖仓 CDC 方案
iceberg         湖仓统一方案
clickhouse      实时 OLAP 看板方案
```

## 8. 当前项目状态

已实现：

```text
local_csv simulation
kudu_impala bootstrap
kudu_impala upsert/delete
impala views
realtime smoke dry-run
```

未实现：

```text
hudi sink
iceberg sink
clickhouse sink
真实 Kudu/Impala 集群联调
实时链路任务调度和监控看板
```

## 9. 后续建议

短期：

- 保留 Kudu/Impala 代码。
- 文档明确 Kudu 是可选实时引擎。
- 本地继续用 CSV simulation。
- 有真实 Kudu/Impala 环境时跑 `--real` smoke。

中期：

- 增加 `REALTIME_ENGINE` 配置。
- Sink 入口按引擎路由。
- 当前已支持：

```text
REALTIME_ENGINE=local_csv
REALTIME_ENGINE=kudu_impala
```

长期：

- 如果项目要贴近主流湖仓，可补 Hudi/Iceberg sink。
- 如果项目要贴近实时看板，可补 ClickHouse sink。

## 10. 面试表达

可以这样说：

```text
实时数仓这里我选择 Kudu/Impala，是因为 CDC 数据天然需要按主键 upsert/delete，
Kudu 对最新状态表和低延迟明细查询比较友好。离线链路仍然用 Hive 做 T+1 分层，
实时链路用 Kudu 补 T+0 查询能力。

但我没有把 Kudu 设计成唯一方案。因为如果公司更偏湖仓，可以替换为 Hudi/Iceberg；
如果更偏实时 OLAP 看板，可以替换为 ClickHouse。所以项目里把实时引擎作为可替换模块设计。
```
