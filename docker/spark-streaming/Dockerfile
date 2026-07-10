FROM confluentinc/cp-kafka:7.6.1

USER root
WORKDIR /workspace

COPY requirements.txt /tmp/requirements.txt
RUN python3 -m pip install --no-cache-dir -r /tmp/requirements.txt

USER appuser

CMD ["python3", "scripts/spark_streaming_kafka_to_hdfs_loop.py"]
