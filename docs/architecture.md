# Architecture

```text
MySQL
  -> Maxwell raw binlog
  -> Kafka incremental/bootstrap topics
  -> Spark Streaming
     -> HDFS ods_binlog -> ODS -> DIM/DWD/DWS/DWT/ADS -> FineBI
     -> Kudu -> Impala -> realtime analysis
```

Control plane:

- task config
- metadata query
- data replay
- delay monitor
- plaintext/sensitive monitor
- special value monitor
- field monitor
- table update monitor

Core modules:

```text
ingestion/maxwell      Maxwell incremental config
ingestion/bootstrap    Maxwell bootstrap/replay entry
streaming/offline_sink Kafka -> HDFS ods_binlog
streaming/realtime_sink Kafka -> Kudu
warehouse/jobs         SparkSQL/Python local merge jobs
warehouse/sql          ods/dim/dwd/dws/dwt/ads SQL
warehouse/scheduler    DolphinScheduler workflow
platform/springboot-admin SpringBoot + Freemarker platform skeleton
```
