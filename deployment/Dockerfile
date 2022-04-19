
# Before building this image, check that docker build with nvidia runtime is activated
# Check the following link: https://stackoverflow.com/questions/59691207/docker-build-with-nvidia-runtime

# For GPUs
# FROM nvcr.io/nvidia/deepstream:6.0.1-devel

# For Jetson
FROM nvcr.io/nvidia/deepstream-l4t:6.0.1-samples


# To get video driver libraries at runtime
ENV LD_LIBRARY_PATH /usr/local/cuda-10.2/lib64
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES all
ENV LOGLEVEL="INFO"
ENV SHELL="/bin/bash"
# To save logs into a file
# RUN mkdir /workspace/output/
# ENV GST_DEBUG="INFO"
# ENV GST_DEBUG_FILE=/workspace/output/GST_DEBUG.log

# First update
RUN apt-get update --fix-missing
RUN apt-get -y install nano

# Installing some Gstream dependencies
RUN apt-get install -y gstreamer-1.0 gstreamer1.0-dev \
    libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev

# Installing python3
RUN apt-get install -y python3.6 python3.6-dev python-dev \
    python3-dev python3-pip \
    python3-numpy python3-opencv

# Setting python3 as the base python
RUN update-alternatives --verbose --install /usr/bin/python python /usr/bin/python3 1

# Installing dependencies for compile gstream python
RUN apt install -y cmake g++ build-essential \
    libglib2.0-dev libglib2.0-dev-bin python-gi-dev libtool m4 autoconf automake
# Compile Gstream for python bindings
RUN cd /opt/nvidia/deepstream/deepstream/sources/ \
    && git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git \
    && cd deepstream_python_apps \
    && git submodule update --init \
    && apt-get install -y apt-transport-https ca-certificates -y \
    && update-ca-certificates \
    && cd 3rdparty/gst-python/ \
    && ./autogen.sh \
    && make \
    && make install

# Compile Deepstream Python Bindings (# For Jetson devices)
RUN cd /opt/nvidia/deepstream/deepstream/sources/ \
    && cd deepstream_python_apps/bindings/ \
    && mkdir build \
    && cd build \
    && cmake ..  -DPYTHON_MAJOR_VERSION=3 -DPYTHON_MINOR_VERSION=6 \
        -DPIP_PLATFORM=linux_aarch64 -DDS_PATH=/opt/nvidia/deepstream/deepstream \
    && make \
    && pip3 install ./pyds-1.1.1-py3-none*.whl

# For compiling in GPUs devices
# Replace the line:
#    && cmake .. -DPYTHON_MAJOR_VERSION=3 -DPYTHON_MINOR_VERSION=8 \
            # -DPIP_PLATFORM=linux_aarch64 -DDS_PATH=/opt/nvidia/deepstream/deepstream
# by 
#    && cmake .. 
# without any flags

# RTSP and Additional libraries
RUN apt-get install -y libgstrtspserver-1.0-0 gstreamer1.0-rtsp \
    libgirepository1.0-dev gobject-introspection gir1.2-gst-rtsp-server-1.0
RUN apt -y install python3-gi python-gst-1.0 gir1.2-gstreamer-1.0 

# COPY . /workspace
WORKDIR /workspace

# CMD python3 run.py "file:///app/data/videos/sample_720p.h264"