STREAMS=/opt/nvidia/deepstream/deepstream/samples/streams
STREAMS_NEW=/workspace/deepstream-video2data/data/videos

python3 main.py \
    file://$STREAMS_NEW/cars_test01.mp4 output/frames \
    # file://$STREAMS/sample_720p.h264 \
    # file://$STREAMS/sample_720p.mp4  \
    # file://$STREAMS/sample_1080p_h265.mp4

# python3 main.py \
#     file://$STREAMS_NEW/sample_720p.mp4 output/frames \