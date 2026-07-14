from __future__ import annotations


def maxwell_schema():
    from pyspark.sql.types import IntegerType, LongType, MapType, StringType, StructField, StructType

    return StructType([
        StructField("database", StringType(), False),
        StructField("table", StringType(), False),
        StructField("type", StringType(), False),
        StructField("ts", LongType(), False),
        StructField("xid", LongType(), True),
        StructField("data", MapType(StringType(), StringType()), True),
        StructField("old", MapType(StringType(), StringType()), True)
    ])


def metadata_to_spark_schema(metadata: dict):
    from pyspark.sql.types import DoubleType, IntegerType, LongType, StringType, StructField, StructType

    type_map = {
        "bigint": LongType(),
        "int": IntegerType(),
        "double": DoubleType(),
        "float": DoubleType(),
        "string": StringType()
    }
    fields = [StructField(column["name"], type_map.get(column["type"], StringType()), True) for column in metadata["columns"]]
    fields.append(StructField("dt", StringType(), True))
    return StructType(fields)
