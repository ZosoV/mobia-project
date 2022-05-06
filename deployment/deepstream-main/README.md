# Main DeepStream Application

## Requirements

1. Complete the steps on [deployment](../README.md) to build the adequate environment for this application.

2. Make sure that the library [`../nvinfer_custom_lpr_parser/libnvdsinfer_custom_impl_lpr.so`](../nvinfer_custom_lpr_parser/libnvdsinfer_custom_impl_lpr.so) is available. That library is useful for parsing the character recognition in a readable format. If that library is not available, please run the Makefile into the folder [./nvinfer_custom_lpr_parser/](./nvinfer_custom_lpr_parser/) for compiling the library.

    ```console
    cd nvinfer_custom_lpr_parser
    make
    cd ..
    ```

## Running steps

2. Run the deepstream app into the docker container by running the scrip [run_deepstream.sh](./run_deepstream.sh). Check the bash script for more details.

    ```console
    bash run_deepstream.sh
    ```

### Docker Build

### Running App

  $ python3 deepstream_test_3.py <uri1> [uri2] ... [uriN]
e.g.
  $ python3 deepstream_test_3.py file:///home/ubuntu/video1.mp4 file:///home/ubuntu/video2.mp4
  $ python3 deepstream_test_3.py rtsp://127.0.0.1/video1 rtsp://127.0.0.1/video2

This document describes the sample deepstream-test3 application.

This sample builds on top of the deepstream-test1 sample to demonstrate how to:

* Use multiple sources in the pipeline.
* Use a uridecodebin so that any type of input (e.g. RTSP/File), any GStreamer
  supported container format, and any codec can be used as input.
* Configure the stream-muxer to generate a batch of frames and infer on the
  batch for better resource utilization.
* Extract the stream metadata, which contains useful information about the
  frames in the batched buffer.

Refer to the deepstream-test1 sample documentation for an example of simple
single-stream inference, bounding-box overlay, and rendering.

This sample accepts one or more H.264/H.265 video streams as input. It creates
a source bin for each input and connects the bins to an instance of the
"nvstreammux" element, which forms the batch of frames. The batch of
frames is fed to "nvinfer" for batched inferencing. The batched buffer is
composited into a 2D tile array using "nvmultistreamtiler." The rest of the
pipeline is similar to the deepstream-test1 sample.

The "width" and "height" properties must be set on the stream-muxer to set the
output resolution. If the input frame resolution is different from
stream-muxer's "width" and "height", the input frame will be scaled to muxer's
output resolution.

The stream-muxer waits for a user-defined timeout before forming the batch. The
timeout is set using the "batched-push-timeout" property. If the complete batch
is formed before the timeout is reached, the batch is pushed to the downstream
element. If the timeout is reached before the complete batch can be formed
(which can happen in case of rtsp sources), the batch is formed from the
available input buffers and pushed. Ideally, the timeout of the stream-muxer
should be set based on the framerate of the fastest source. It can also be set
to -1 to make the stream-muxer wait infinitely.

The "nvmultistreamtiler" composite streams based on their stream-ids in
row-major order (starting from stream 0, left to right across the top row, then
across the next row, etc.).
