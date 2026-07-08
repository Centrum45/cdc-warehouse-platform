# Binlog Merge

ODS snapshot is rebuilt from new binlog plus old ODS partitions touched by those
binlog events.

Algorithm:

```text
1. Check delay gate. Merge can start only when table sync progress reaches threshold.
2. Read new ods_binlog rows in process window.
3. Parse Maxwell JSON into business columns.
4. Find affected business dt by partition column, usually ctime.
5. Read old ODS rows from affected dt partitions.
6. union all new binlog rows and old ODS rows.
7. partition by primary key.
8. order by version desc, binlog_type desc.
9. keep row_number = 1.
10. drop rows where latest binlog_type is delete.
```

Tie breaker:

```text
insert/bootstrap-insert = 1
update                  = 2
delete                  = 3
```
