# pipeline-kafka-flink

Build a streaming pipeline flow (left-to-right): Sources (IoT Sensors, Clickstream, Mobile Events, API Events) -> Kafka Topics (raw-events, enriched-events, alerts) -> Flink Jobs (Dedup, Enrich, Aggregate, Anomaly Detect) -> Sinks (Elasticsearch, S3 Data Lake, PagerDuty, Grafana Dashboard).

Use the pipeline pattern.
