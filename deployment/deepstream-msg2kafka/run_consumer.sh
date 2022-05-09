# kafka directory
KAFKA_DIR=/opt/kafka/kafka_2.13-3.1.0/

echo "Running Test Consumer ..."
$KAFKA_DIR/bin/kafka-console-consumer.sh --topic quickstart-events --from-beginning --bootstrap-server localhost:9092