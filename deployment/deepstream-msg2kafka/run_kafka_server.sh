cd kafka_2.13-3.1.0

# Start the ZooKeeper service
# Note: Soon, ZooKeeper will no longer be required by Apache Kafka.
bin/zookeeper-server-start.sh config/zookeeper.properties &

# Start the Kafka broker service
bin/kafka-server-start.sh config/server.properties
