create external table if not exists dim.dim_comment_batch_type (
  batchtype string,
  batchtype_name string,
  is_priority int
)
partitioned by (dt string)
stored as parquet;

