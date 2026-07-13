# CDC Warehouse Platform 项目进度文档

## 1. 项目目标

本项目目标是实现一个可本地调试、也可部署到服务器生产环境的数据仓库平台。

核心链路：

```text
MySQL
  -> Maxwell 采集 binlog
  -> Kafka
  -> SparkStreaming 消费
  -> HDFS ods_binlog 分区
  -> Spark SQL / PySpark ODS merge
  -> Hive ODS/DIM/DWD/DWS/DWT/ADS
  -> SpringBoot 管理平台
  -> FineBI / Impala 查询展示
```

项目同时覆盖：

- 增量 binlog 采集。
- Maxwell bootstrap 全量重放。
- ODS 快照 merge。
- 数仓分层建模。
- 调度与任务管理。
- 数据延迟、字段、特殊值、表更新时间、明文检测等监控。
- SpringBoot + Freemarker 数据管理平台。
- Kudu/Impala 实时数仓路径。
- Docker Compose 本地完整部署。
- Linux systemd 服务器部署。

## 2. 当前整体状态

当前项目已经达到：

```text
本地 Docker 全链路可跑通
核心代码已合并到 main
GitHub Actions main 分支 CI 已通过
服务器部署脚本已有 dry-run/preflight/health/smoke
```

最近一次 main 分支提交：

```text
93485be feat: add realtime kudu impala bootstrap
```

CI 状态：

```text
main 分支 GitHub Actions: success
```

## 3. 已完成内容

### 3.1 本地开发与部署

已完成：

- Docker Compose 本地环境。
- MySQL、Maxwell、Kafka、HDFS、Hive、DolphinScheduler、SparkStreaming、SpringBoot Admin 容器。
- Hadoop/Hive 本地下载脚本。
- 本地健康检查脚本。
- 本地 E2E 脚本。
- 本地/服务器一键端到端验收脚本。
- 本地 HDFS/Hive 全链路验证。

已验证链路：

```text
MySQL insert
-> Maxwell binlog
-> Kafka
-> SparkStreaming
-> HDFS ods_binlog
-> PySpark ODS merge
-> Hive ODS
-> Hive DIM/DWD/DWS/DWT/ADS
```

### 3.2 Binlog 采集

已完成：

- Maxwell binlog JSON 格式解析。
- Kafka topic 消费。
- SparkStreaming 风格消费脚本。
- HDFS ods_binlog 按库、表、日期分区写入。
- 本地 JSONL 模式兜底，方便无 Kafka/HDFS 时调试。
- 敏感字段检测与脱敏逻辑。

### 3.3 Bootstrap 全量同步

已完成：

- MySQL 表全量 bootstrap 逻辑。
- 接入新表前先做全量同步的流程。
- bootstrap 事件写入 ods_binlog。
- bootstrap 数据参与 ODS merge。

### 3.4 ODS Merge

已完成：

- 按用户原始 SQL 思路实现 merge：

```text
新增 binlog
union all 受影响 ODS 分区
按主键开窗
按 ver desc、binlog_type desc 取最新
过滤 delete
生成 ODS 快照
```

已完成实现：

- 本地 fallback merge。
- PySpark merge。
- 每日离线 merge 脚本。
- HDFS 读写模式。
- delay gate 检查。
- 幂等重跑基础能力。

### 3.5 数仓分层

已完成：

- ODS 层。
- DIM 层。
- DWD 层。
- DWS 层。
- DWT 层。
- ADS 层。
- Hive DDL。
- Hive 分层 SQL。
- ADS 示例指标。

当前已验证 ADS 指标：

```text
comment_batch_total
comment_batch_priority_total
```

### 3.6 SpringBoot 数据管理平台

已完成：

- SpringBoot + Freemarker 管理后台。
- MySQL 元数据库连接。
- Dashboard 首页。
- Logs 页面。
- Onboarding 页面。
- Tasks 页面。
- 任务执行历史。
- 任务失败明细和重跑入口。
- ODS merge 状态表。
- 页面一键触发本地/服务器 E2E 验收。
- 表级补数入口。
- 表级链路检查。
- 表级 MySQL/ODS 一致性检查。
- 新表接入后自动验收。
- 失败任务关联日志上下文。
- Replay 页面。
- Monitors 页面。
- Rules 页面。
- Hive 查询页面/API。
- Docker 容器状态展示。
- Kafka 信息展示。
- Maxwell/Kafka/Spark/Admin 日志展示。
- E2E 验收日志和诊断展示。
- 5 秒刷新日志。
- 日志页避免自动跳顶部。

### 3.7 管理平台安全

已完成：

- `/login` 登录页。
- `/logout` 退出。
- JWT 登录。
- HttpOnly Cookie。
- dev 模式允许本地免登录调试。
- prod 模式页面/API 强制鉴权。
- API 未登录返回 401。
- 页面未登录跳转 `/login`。
- 禁止生产使用默认 `admin123`。
- 强制生产 `JWT_SECRET` 长度不少于 32。
- 高风险平台动作操作审计，记录 merge、监控、DS 发布、实时 Kafka->Kudu 等操作的请求、执行结果、耗时和客户端来源。

### 3.8 监控与质量

已完成基础能力：

- 数据延迟监控。
- 字段差异监控。
- ODS alter SQL 生成。
- 特殊值监控。
- 非空监控。
- 表更新时间监控。
- 明文检测。
- 监控结果存储。
- 通知器接口。
- 分区检查。
- 行数检查。
- 空值率检查。

### 3.9 DolphinScheduler

已完成：

- DolphinScheduler 客户端封装。
- workflow 发布逻辑。
- audit 模式。
- DAG/依赖描述。
- 本地 DolphinScheduler 容器。
- 基础调度脚本。

### 3.10 实时数仓 Kudu/Impala

已完成：

- Kudu DDL。
- Impala View SQL。
- Kudu client，经 Impala 执行 UPSERT/DELETE。
- Impala query client。
- 实时 sink 本地 CSV 模拟模式。
- 真实 Kudu/Impala bootstrap 脚本。
- 实时 smoke 脚本。
- dry-run SQL 预览。
- 真实模式失败不静默 fallback，直接报错。

相关命令：

```bash
python3 scripts/run_realtime_kudu_smoke.py --dry-run
python3 -m realtime.impala.bootstrap
python3 scripts/run_realtime_kudu_smoke.py
```

### 3.11 服务器部署

已完成：

- Linux systemd 部署方案。
- `cdc-admin.service`
- `cdc-spark-streaming.service`
- `cdc-ops-refresh.service`
- `cdc-daily-merge.service`
- `cdc-daily-merge.timer`
- `install.sh`
- `uninstall.sh`
- `control.sh`
- `preflight.sh`
- `healthcheck.sh`
- `prod_smoke.sh`
- `install.sh --dry-run`

服务器部署能力：

```text
dry-run: 预演安装，不写 /opt、/etc、systemd
preflight: 启动前检查环境变量、密码、JWT、项目目录
health: 检查服务、命令、MySQL/Kafka/HDFS/Hive
smoke: 检查生产链路关键分区和 Hive count
```

### 3.12 CI/CD

已完成 GitHub Actions：

- Python 3.8/3.9/3.10/3.11 单测。
- Java SpringBoot compile。
- Python 语法检查。
- 核心模块 import 检查。
- Shell 语法检查。
- Docker Compose config 检查。
- 部署文档和 env 示例校验。
- server install dry-run 校验。

main 分支最新 CI 已通过。

### 3.13 文档

已完成：

- 架构文档。
- binlog merge 原理文档。
- 数仓分层文档。
- Docker runbook。
- 英文部署文档。
- 中文部署文档。
- server systemd 部署说明。
- 生产检查清单。
- SpringBoot MySQL 文档。
- Realtime Kudu/Impala 文档。
- 实时数仓引擎选型文档。
- FineBI 映射说明。
- 指标说明。

## 4. 未完成内容

### 4.1 真实服务器部署验证

未完成：

- 还没有在一台干净 Linux 服务器完整部署。
- 还没有真实执行 systemd start/stop/restart。
- 还没有用真实生产 MySQL/Kafka/HDFS/Hive 跑 smoke。

当前状态：

```text
脚本和文档已具备
dry-run/preflight 已可用
真实服务器未验证
```

### 4.2 真实 Kudu/Impala 集群联调

未完成：

- 本机没有安装 `impyla`。
- 本地没有真实 Kudu/Impala 集群。
- 真实 Impala 认证、Kudu 建表权限、UPSERT 性能还未验证。

当前状态：

```text
代码支持真实模式
dry-run 已验证
CSV 模拟已验证
真实集群未验证
```

### 4.3 权限体系

未完成：

- 多用户。
- RBAC。
- 菜单级权限。
- 操作级权限。
- 审批流。
- SSO/LDAP/OAuth 集成。

当前已有：

```text
admin 单账号
JWT 登录
prod 强制鉴权
操作审计日志
```

### 4.4 生产安全

未完成：

- HTTPS/Nginx 示例配置。
- Cookie Secure/SameSite 强化。
- IP 白名单。
- VPN/内网访问控制落地。
- 密钥托管。
- 敏感配置加密。

### 4.5 调度闭环

未完成：

- 真实 DolphinScheduler DAG 完整生产联调。
- 失败重试策略。
- 补数流程。
- 参数化调度。
- 任务 SLA。
- 调度报警闭环。

### 4.6 数据一致性

未完成：

- Kafka offset、HDFS 写入、ODS merge 状态之间的强事务。
- exactly-once 语义。
- 更完整的失败恢复策略。
- merge 任务状态表。
- 数据版本回滚。

### 4.7 存储格式与性能优化

未完成：

- 压缩策略。
- Hive 表分桶。
- 大表 merge 性能压测。
- 热分区优化。
- 小文件治理。
- Iceberg/Hudi/Delta 等湖仓表格式支持。

当前已完成：

```text
ods_binlog/ods/dim/dwd/dws/dwt/ads 已统一 Parquet
ods_binlog 保留 raw_json/data_json/old_json，兼顾字段演进和追溯
```

### 4.8 Schema 演进

未完成：

- 字段类型变更自动处理。
- 删除字段处理策略。
- 主键变更处理。
- 表迁移/换表自动识别后的治理流程。
- 历史分区 schema 兼容。

当前已完成：

```text
新增字段检测
alter SQL 生成
```

### 4.9 告警通道

未完成：

- 企业微信。
- 飞书。
- 邮件。
- 电话/短信。
- 告警收敛。
- 告警升级。

当前只有通知器接口和基础结果存储。

### 4.10 管理平台产品化

未完成：

- 更完整的元数据编辑。
- 配置版本管理。
- 配置 diff。
- 配置回滚。
- 更丰富的任务失败诊断，例如失败类型归因、关联日志跳转、补数参数推荐。
- 数据血缘图 UI。
- 数据质量看板。
- 实时链路看板。

### 4.11 多表大规模验证

未完成：

- 批量接入多库多表验证。
- 多主键验证。
- 复杂字段类型验证。
- 大数据量压测。
- 高频更新表压测。
- 删除事件密集场景压测。

当前重点验证表：

```text
basiccomment.avatar_commentbatchsource
```

## 5. 当前风险

### 5.1 本地跑通不等于生产跑通

本地 Docker 环境能模拟大部分链路，但生产会遇到：

- Kerberos。
- Kafka ACL。
- Hive 权限。
- HDFS 权限。
- Impala 认证。
- Kudu 建表权限。
- YARN 队列资源。
- 网络防火墙。

### 5.2 ODS merge 大表性能风险

当前 merge 逻辑正确，但大表场景可能 shuffle 压力较大。

后续需要：

- 分区裁剪。
- 分桶。
- 文件格式优化。
- 增量索引。
- Spark 参数调优。
- 湖仓格式评估。

### 5.3 管理平台安全等级不足

当前适合内网或测试环境。

生产对外开放前必须补：

- HTTPS。
- 访问控制。
- 权限分级。
- 密钥保护。

## 6. 下一步建议

优先级从高到低：

1. 找一台干净 Linux 服务器，按 `docs/deployment_guide_zh.md` 完整部署一次。
2. 接一套真实 Kafka/HDFS/Hive 环境，跑 `control.sh preflight/health/smoke`。
3. 接真实 Kudu/Impala，跑 `scripts/run_realtime_kudu_smoke.py`。
4. 补 Nginx/HTTPS/内网访问控制。
5. 补多用户 RBAC 和审批流。
6. 对 Parquet 小文件、压缩参数和分区粒度做压测优化。
7. 对 3 到 5 张真实业务表做批量接入和压测。
8. 补 DolphinScheduler 真实 DAG 联调和失败报警。

## 7. 结论

当前项目已经完成从 0 到 1：

```text
能部署
能本地跑通
能解释核心链路
能做 ODS merge
能产出 ADS
有管理后台
有 CI
有服务器部署脚本
有实时 Kudu/Impala 真实模式代码
有实时引擎选型说明
```

但还不是成熟企业级数据平台。

后续重点是从“可运行样板”推进到“生产级平台”：

```text
真实服务器验证
真实大数据组件联调
权限安全
调度闭环
一致性保障
性能优化
多表规模化验证
```
