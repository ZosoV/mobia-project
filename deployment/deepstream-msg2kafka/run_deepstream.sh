
python3 deepstream_test_4.py -i ../data/videos/sample_720p.h264 \
        -p /opt/nvidia/deepstream/deepstream/lib/libnvds_kafka_proto.so \
        --conn-str="localhost;9092;quickstart-events" \
        -s 1 \
        --no-display

# python3 main.py --config configs/global_config.cfg