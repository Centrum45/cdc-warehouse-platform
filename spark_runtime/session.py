from __future__ import annotations


def has_pyspark() -> bool:
    try:
        import pyspark  # noqa: F401
    except Exception:
        return False
    return True


def create_spark(app_name: str, master: str = "local[2]"):
    from pyspark.sql import SparkSession

    return (
        SparkSession.builder
        .appName(app_name)
        .master(master)
        .config("spark.sql.session.timeZone", "Asia/Shanghai")
        .config("spark.hadoop.dfs.client.use.datanode.hostname", "true")
        .getOrCreate()
    )
