# https://lifestyletransfer.com/how-to-install-gstreamer-python-bindings/

apt-get update --fix-missing

apt-get install nano
apt-get install gstreamer-1.0 gstreamer1.0-dev \
apt-get install libgstreamer1.0-dev libgstreamer-plugins-base1.0-dev -y

apt-get install python3.6 python3.6-dev python-dev python3-dev \
apt-get install python3-pip python-dev \
apt-get install python3.6-venv

echo "alias python='/usr/bin/python3'" > ~/.bash_profile
source ~/.bash_profile 


apt install -y cmake g++ build-essential \
    libglib2.0-dev libglib2.0-dev-bin python-gi-dev libtool m4 autoconf automake


git clone https://github.com/NVIDIA-AI-IOT/deepstream_python_apps.git

cd deepstream_python_apps

git submodule update --init

# Insta GST Python
apt-get install -y apt-transport-https ca-certificates -y
update-ca-certificates

cd 3rdparty/gst-python/
./autogen.sh
make
make install

# Bindings Compile
cd ../../bindings
mkdir build
cd build
cmake ..  -DPYTHON_MAJOR_VERSION=3 -DPYTHON_MINOR_VERSION=6 \
    -DPIP_PLATFORM=linux_aarch64 -DDS_PATH=/opt/nvidia/deepstream/deepstream
make


apt install python3-gi python-gst-1.0 gir1.2-gstreamer-1.0 gir1.2-gst-rtsp-server-1.0
apt install libgirepository1.0-dev libcairo2-dev
pip3 install ./pyds-1.1.1-py3-none*.whl
