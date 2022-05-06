# docker exec -it 328409b5ea6e /bin/bash
cd kafka_2.13-3.1.0

bin/kafka-console-consumer.sh --topic quickstart-events --from-beginning --bootstrap-server localhost:9092