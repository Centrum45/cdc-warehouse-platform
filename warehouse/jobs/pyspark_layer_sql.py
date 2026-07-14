from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from warehouse.spark_runtime.session import create_spark

DEFAULT_HDFS_ROOT = "hdfs://localhost:8020/warehouse"


def _path_exists(spark, path: str) -> bool:
    hadoop_conf = spark.sparkContext._jsc.hadoopConfiguration()
    fs_path = spark.sparkContext._jvm.org.apache.hadoop.fs.Path(path)
    fs = fs_path.getFileSystem(hadoop_conf)
    return fs.exists(fs_path)


def _empty_view(spark, view_name: str, schema: str) -> None:
    spark.createDataFrame([], schema).createOrReplaceTempView(view_name)


def _read_csv_view(spark, view_name: str, path: str, schema: str, header: bool = False) -> None:
    if not _path_exists(spark, path):
        _empty_view(spark, view_name, schema)
        return
    (
        spark.read
        .option("header", str(header).lower())
        .schema(schema)
        .csv(path)
        .createOrReplaceTempView(view_name)
    )


def _read_table_view(spark, view_name: str, path: str, schema: str, header: bool = False) -> None:
    if not _path_exists(spark, path):
        _empty_view(spark, view_name, schema)
        return
    try:
        spark.read.schema(schema).parquet(path).createOrReplaceTempView(view_name)
    except Exception:
        _read_csv_view(spark, view_name, path, schema, header)


def _write_partition(df, lake_root: str, layer: str, table: str, biz_dt: str) -> str:
    target = f"{lake_root.rstrip('/')}/{layer}/{table}/dt={biz_dt}"
    df.coalesce(1).write.mode("overwrite").parquet(target)
    return target


def _register_inputs(spark, lake_root: str, biz_dt: str) -> None:
    yesterday = spark.sql(f"select date_sub('{biz_dt}', 1) as dt").collect()[0]["dt"]
    root = lake_root.rstrip("/")

    _read_table_view(
        spark,
        "ods_basiccomment_avatar_commentbatchsource_dic",
        f"{root}/ods/db=basiccomment/table=avatar_commentbatchsource/dt={biz_dt}",
        "id long,batchnumber string,batchtype string,ctime string,utime string,ver int,source_channel string,dt string",
        header=True,
    )
    _read_table_view(
        spark,
        "ods_user_user_info_dic",
        f"{root}/ods/db=user/table=user_info/dt={biz_dt}",
        "id long,user_name string,mobile string,email string,register_time string,ctime string,utime string,ver int,dt string",
        header=True,
    )
    _read_table_view(
        spark,
        "ods_trade_order_info_dic",
        f"{root}/ods/db=trade/table=order_info/dt={biz_dt}",
        "id long,user_id long,order_no string,pay_amount double,order_status string,ctime string,utime string,ver int,dt string",
        header=True,
    )
    _read_table_view(
        spark,
        "dwt_comment_batch_topic_td_yesterday",
        f"{root}/dwt/dwt_comment_batch_topic_td/dt={yesterday}",
        "batchtype string,total_batch_cnt long,priority_batch_cnt long,latest_batch_time string",
    )
    _read_table_view(
        spark,
        "dwt_trade_user_td_yesterday",
        f"{root}/dwt/dwt_trade_user_td/dt={yesterday}",
        "user_id long,total_order_cnt long,total_pay_amount double,first_order_date string,last_order_date string",
    )


def run_layers(lake_root: str, biz_dt: str, master: str = "local[2]") -> list[str]:
    spark = create_spark("cdc-warehouse-layer-sql", master)
    spark.sparkContext.setLogLevel("WARN")
    _register_inputs(spark, lake_root, biz_dt)

    written: list[str] = []
    try:
        dim_comment = spark.sql("""
            select 'normal' as batchtype, '普通批次' as batchtype_name, 0 as is_priority
            union all
            select 'priority' as batchtype, '优先批次' as batchtype_name, 1 as is_priority
        """)
        dim_comment.createOrReplaceTempView("dim_comment_batch_type")
        written.append(_write_partition(dim_comment, lake_root, "dim", "dim_comment_batch_type", biz_dt))

        dim_user = spark.sql("""
            select id as user_id, user_name, mobile, email, register_time
            from ods_user_user_info_dic
        """)
        dim_user.createOrReplaceTempView("dim_user_info")
        written.append(_write_partition(dim_user, lake_root, "dim", "dim_user_info", biz_dt))

        dwd_comment = spark.sql("""
            select
              o.id,
              o.batchnumber,
              o.batchtype,
              d.batchtype_name,
              o.ctime,
              o.utime,
              o.ver
            from ods_basiccomment_avatar_commentbatchsource_dic o
            left join dim_comment_batch_type d
              on o.batchtype = d.batchtype
        """)
        dwd_comment.createOrReplaceTempView("dwd_comment_batch_detail_di")
        written.append(_write_partition(dwd_comment, lake_root, "dwd", "dwd_comment_batch_detail_di", biz_dt))

        dwd_trade = spark.sql("""
            select
              o.id as order_id,
              o.user_id,
              o.order_no,
              o.pay_amount,
              o.order_status,
              u.user_name,
              o.ctime,
              o.utime
            from ods_trade_order_info_dic o
            left join ods_user_user_info_dic u
              on o.user_id = u.id
        """)
        dwd_trade.createOrReplaceTempView("dwd_trade_order_detail_di")
        written.append(_write_partition(dwd_trade, lake_root, "dwd", "dwd_trade_order_detail_di", biz_dt))

        dws_comment = spark.sql("""
            select
              batchtype,
              count(1) as batch_cnt,
              sum(case when batchtype = 'priority' then 1 else 0 end) as priority_batch_cnt
            from dwd_comment_batch_detail_di
            group by batchtype
        """)
        dws_comment.createOrReplaceTempView("dws_comment_batch_1d")
        written.append(_write_partition(dws_comment, lake_root, "dws", "dws_comment_batch_1d", biz_dt))

        dws_trade = spark.sql("""
            select
              user_id,
              count(1) as order_cnt,
              sum(pay_amount) as pay_amount
            from dwd_trade_order_detail_di
            group by user_id
        """)
        dws_trade.createOrReplaceTempView("dws_trade_user_1d")
        written.append(_write_partition(dws_trade, lake_root, "dws", "dws_trade_user_1d", biz_dt))

        dwt_comment = spark.sql(f"""
            select
              coalesce(today.batchtype, yesterday.batchtype) as batchtype,
              coalesce(yesterday.total_batch_cnt, 0) + coalesce(today.batch_cnt, 0) as total_batch_cnt,
              coalesce(yesterday.priority_batch_cnt, 0) + coalesce(today.priority_batch_cnt, 0) as priority_batch_cnt,
              '{biz_dt}' as latest_batch_time
            from dws_comment_batch_1d today
            full outer join dwt_comment_batch_topic_td_yesterday yesterday
              on today.batchtype = yesterday.batchtype
        """)
        dwt_comment.createOrReplaceTempView("dwt_comment_batch_topic_td")
        written.append(_write_partition(dwt_comment, lake_root, "dwt", "dwt_comment_batch_topic_td", biz_dt))

        dwt_trade = spark.sql(f"""
            select
              coalesce(today.user_id, yesterday.user_id) as user_id,
              coalesce(yesterday.total_order_cnt, 0) + coalesce(today.order_cnt, 0) as total_order_cnt,
              coalesce(yesterday.total_pay_amount, 0) + coalesce(today.pay_amount, 0) as total_pay_amount,
              coalesce(yesterday.first_order_date, '{biz_dt}') as first_order_date,
              '{biz_dt}' as last_order_date
            from dws_trade_user_1d today
            full outer join dwt_trade_user_td_yesterday yesterday
              on today.user_id = yesterday.user_id
        """)
        dwt_trade.createOrReplaceTempView("dwt_trade_user_td")
        written.append(_write_partition(dwt_trade, lake_root, "dwt", "dwt_trade_user_td", biz_dt))

        ads_comment = spark.sql("""
            select 'comment_batch_total' as metric_name, sum(total_batch_cnt) as metric_value
            from dwt_comment_batch_topic_td
            union all
            select 'comment_batch_priority_total' as metric_name, sum(priority_batch_cnt) as metric_value
            from dwt_comment_batch_topic_td
        """)
        written.append(_write_partition(ads_comment, lake_root, "ads", "ads_comment_dashboard_1d", biz_dt))

        ads_trade = spark.sql("""
            select 'gmv' as metric_name, sum(pay_amount) as metric_value
            from dws_trade_user_1d
            union all
            select 'pay_user_cnt' as metric_name, cast(count(distinct user_id) as double) as metric_value
            from dws_trade_user_1d
            union all
            select 'total_gmv' as metric_name, sum(total_pay_amount) as metric_value
            from dwt_trade_user_td
            union all
            select 'total_user_cnt' as metric_name, cast(count(distinct user_id) as double) as metric_value
            from dwt_trade_user_td
            union all
            select 'avg_order_per_user' as metric_name,
              case when count(distinct user_id) = 0 then null
                   else cast(sum(total_order_cnt) as double) / count(distinct user_id)
              end as metric_value
            from dwt_trade_user_td
        """)
        written.append(_write_partition(ads_trade, lake_root, "ads", "ads_trade_dashboard_1d", biz_dt))
        return written
    finally:
        spark.stop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run dim/dwd/dws/dwt/ads warehouse layers with Spark SQL.")
    parser.add_argument("--lake-root", default=DEFAULT_HDFS_ROOT)
    parser.add_argument("--biz-dt", required=True)
    parser.add_argument("--master", default="local[2]")
    args = parser.parse_args()

    for path in run_layers(args.lake_root, args.biz_dt, args.master):
        print(f"spark-sql-layer {path}", flush=True)


if __name__ == "__main__":
    main()
