create view if not exists realtime.v_realtime_user_analysis as
select
  substr(register_time, 1, 10) as register_date,
  count(1) as user_cnt,
  max(utime) as latest_update_time
from realtime.user_info
group by substr(register_time, 1, 10);
