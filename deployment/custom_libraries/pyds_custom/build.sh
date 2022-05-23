NAME=pyds_custom
PKGS="gstreamer-1.0 gstreamer-video-1.0"
CUSTOM_INCLUDES="/opt/custom_libraries/includes"

c++ -O3 -Wall -shared -std=c++11 \
    -fPIC `python3 -m pybind11 --includes` \
    pyds_custom.cpp \
    -o ${NAME}.so \
    -I${CUSTOM_INCLUDES} \
    `pkg-config --cflags ${PKGS}`
