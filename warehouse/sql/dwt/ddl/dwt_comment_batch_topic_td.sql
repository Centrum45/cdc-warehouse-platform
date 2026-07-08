create external table if not exists dwt.dwt_comment_batch_topic_td (
  batchtype string,
  total_batch_cnt bigint,
  priority_batch_cnt bigint,
  latest_batch_time string
)
partitioned by (dt string)
stored as parquet;
