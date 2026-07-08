drop table if exists dim.dim_comment_batch_type;

create external table if not exists dim.dim_comment_batch_type (
  batchtype string,
  batchtype_name string,
  is_priority int
)
partitioned by (dt string)
row format delimited fields terminated by ','
stored as textfile
location '/warehouse/dim/dim_comment_batch_type';
