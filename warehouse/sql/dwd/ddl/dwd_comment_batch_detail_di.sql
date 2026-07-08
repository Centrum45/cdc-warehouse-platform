create external table if not exists dwd.dwd_comment_batch_detail_di (
  id bigint,
  batchnumber string,
  batchtype string,
  batchtype_name string,
  ctime string,
  utime string,
  ver int
)
partitioned by (dt string)
stored as parquet;

