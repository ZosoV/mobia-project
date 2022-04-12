sudo docker run --runtime nvidia -it --rm --network host \
    -v /tmp/.X11-unix/:/tmp/.X11-unix \
    -v /tmp/argus_socket:/tmp/argus_socket \
    -v ~/Documents/mobia-project/deployment:/dli/task/my_apps \
    nvcr.io/nvidia/dli/dli-nano-deepstream:v2.0.0-DS6.0.1

    # --device /dev/video0 \
     
