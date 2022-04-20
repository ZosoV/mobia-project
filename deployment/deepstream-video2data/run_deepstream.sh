STREAMS=/opt/nvidia/deepstream/deepstream/samples/streams
STREAMS_NEW=/workspace/deepstream-video2data

python3 main.py \
    file://$STREAMS_NEW/cars_test01.mp4 frames \
    # file://$STREAMS/sample_720p.h264 \
    # file://$STREAMS/sample_720p.mp4  \
    # file://$STREAMS/sample_1080p_h265.mp4