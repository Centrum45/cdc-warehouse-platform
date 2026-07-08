insert overwrite table dwd.dwd_comment_batch_detail_di partition(dt='${biz_dt}')
select
  o.id,
  o.batchnumber,
  o.batchtype,
  d.batchtype_name,
  o.ctime,
  o.utime,
  o.ver
from ods.ods_basiccomment_avatar_commentbatchsource_dic o
left join dim.dim_comment_batch_type d
  on o.batchtype = d.batchtype
 and d.dt = '${biz_dt}'
where o.dt = '${biz_dt}';

