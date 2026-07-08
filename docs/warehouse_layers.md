# Warehouse Layers

```text
ods_binlog: raw Maxwell binlog JSON
ods:        MySQL-like current snapshot
dim:        shared dimensions
dwd:        detail fact layer
dws:        subject aggregation layer
dwt:        topic wide table layer
ads:        application/report layer
```

Local HDFS simulation:

```text
data/lake/ods_binlog/db=.../table=.../dt=.../part-00000.jsonl
data/lake/ods/db=.../table=.../dt=.../part-00000.csv
```

Docker HDFS:

```text
hdfs://localhost:8020/warehouse/ods_binlog
hdfs://localhost:8020/warehouse/ods
hdfs://localhost:8020/warehouse/dim
hdfs://localhost:8020/warehouse/dwd
hdfs://localhost:8020/warehouse/dws
hdfs://localhost:8020/warehouse/dwt
hdfs://localhost:8020/warehouse/ads
```

Hive databases:

```text
ods_binlog, ods, dim, dwd, dws, dwt, ads
```

Modeling path:

```text
ods snapshot
  -> dim shared dimensions
  -> dwd detail facts, cleaning, degenerate dimensions
  -> dws daily subject summaries
  -> dwt topic wide tables
  -> ads FineBI report tables
```
