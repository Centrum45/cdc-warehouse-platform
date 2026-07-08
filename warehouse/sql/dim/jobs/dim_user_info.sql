insert overwrite table dim.dim_user_info partition(dt='${biz_dt}')
select
  id as user_id,
  user_name,
  mobile,
  email,
  register_time
from ods.ods_user_user_info_dic
where dt = '${biz_dt}';
