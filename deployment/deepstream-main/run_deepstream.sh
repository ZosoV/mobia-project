STREAMS=/opt/nvidia/deepstream/deepstream/samples/streams
STREAMS_NEW=/workspace/deepstream-main/data/videos

python3 main_copy.py -i \
    file://$STREAMS_NEW/cars_test01.mp4 #\
    # file://$STREAMS/sample_720p.h264 \
    # file://$STREAMS/sample_720p.mp4  \
    # file://$STREAMS/sample_1080p_h265.mp4