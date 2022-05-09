# kafka directory
KAFKA_DIR=/opt/kafka/kafka_2.13-3.1.0/

# Start the ZooKeeper service
# Note: Soon, ZooKeeper will no longer be required by Apache Kafka.
echo "Starting ZooKeeper ..."
nohup $KAFKA_DIR/bin/zookeeper-server-start.sh $KAFKA_DIR/config/zookeeper.properties > /dev/null1 2>&1 &

# Start the Kafka broker service
echo "Starting Kafka broker ..."
nohup $KAFKA_DIR/bin/kafka-server-start.sh $KAFKA_DIR/config/server.properties > /dev/null2 2>&1 &

# Create default topic
echo "Creating default topic: quickstart-events ..."
nohup $KAFKA_DIR/bin/kafka-topics.sh --create --topic quickstart-events --bootstrap-server localhost:9092 > /dev/null3 2>&1 &

/bin/bash