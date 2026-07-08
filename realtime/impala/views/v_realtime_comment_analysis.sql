create view if not exists realtime.v_realtime_comment_analysis as
select
  batchtype,
  count(1) as batch_cnt,
  max(utime) as latest_update_time
from realtime.avatar_commentbatchsource
group by batchtype;

