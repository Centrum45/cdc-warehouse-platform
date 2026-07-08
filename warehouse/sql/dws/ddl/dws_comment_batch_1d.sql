drop table if exists dws.dws_comment_batch_1d;

create external table if not exists dws.dws_comment_batch_1d (
  batchtype string,
  batch_cnt bigint,
  priority_batch_cnt bigint
)
partitioned by (dt string)
row format delimited fields terminated by ','
stored as textfile
location '/warehouse/dws/dws_comment_batch_1d';
