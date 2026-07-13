FROM apache/spark:3.5.1

USER root
WORKDIR /workspace
ENV PATH="/opt/spark/bin:${PATH}"
ARG SPARK_KAFKA_PACKAGE=org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1

RUN mkdir -p /home/spark/.ivy2/cache /home/spark/.ivy2/jars \
    && chown -R spark:spark /home/spark/.ivy2 \
    && su spark -s /bin/sh -c "/opt/spark/bin/spark-submit --master local[1] --packages ${SPARK_KAFKA_PACKAGE} --class org.apache.spark.examples.SparkPi /opt/spark/examples/jars/spark-examples_2.12-3.5.1.jar 1"

USER spark

CMD ["spark-submit", "--version"]
