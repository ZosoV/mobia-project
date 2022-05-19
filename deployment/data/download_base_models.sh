#!/bin/bash

# Download CAR model
mkdir -p ./pgies/tcnet
cd ./pgies/tcnet
wget https://api.ngc.nvidia.com/v2/models/nvidia/tao/trafficcamnet/versions/pruned_v1.0.1/files/labels.txt
wget https://api.ngc.nvidia.com/v2/models/nvidia/tao/trafficcamnet/versions/pruned_v1.0.1/files/trafficcamnet_int8.txt
wget https://api.ngc.nvidia.com/v2/models/nvidia/tao/trafficcamnet/versions/pruned_v1.0.1/files/resnet18_trafficcamnet_pruned.etlt
cd -


# Download LPD model
mkdir -p ./sgies/lpdnet
cd ./sgies/lpdnet
wget https://api.ngc.nvidia.com/v2/models/nvidia/tao/lpdnet/versions/pruned_v1.0/files/usa_pruned.etlt
wget https://api.ngc.nvidia.com/v2/models/nvidia/tao/lpdnet/versions/pruned_v1.0/files/usa_lpd_cal_dla.bin
wget https://api.ngc.nvidia.com/v2/models/nvidia/tao/lpdnet/versions/pruned_v1.0/files/usa_lpd_label.txt
cd -

# # Download LPR model
mkdir -p ./sgies/lprnet
cd ./sgies/lprnet
wget https://api.ngc.nvidia.com/v2/models/nvidia/tao/lprnet/versions/deployable_v1.0/files/us_lp_characters.txt
wget https://api.ngc.nvidia.com/v2/models/nvidia/tao/lprnet/versions/deployable_v1.0/files/us_lprnet_baseline18_deployable.etlt
# touch labels_us.txt
cd -

# Download NN for color detection
mkdir -p ./sgies/colornet
cd ./sgies/colornet
# ZIP file
# wget https://drive.google.com/uc?id=19WrliM63gyCtYMg99G0ACIX_M480iKMu&export=download
wget -O cal_trt.bin https://drive.google.com/uc?id=1SmxdXvwk-jm3Z1LfQNCau1LkcvZYKsf4&export=download
wget -O labels.txt https://drive.google.com/uc?id=1y2sVeYRAdAtxdNaa7_NPDI5yZrrYQB6h&export=download
wget -O mean.ppm https://drive.google.com/uc?id=1sGLJj7zAgi--FzXiy6KvdWwEGCISyoNW&export=download
wget -O resnet18.caffemodel https://drive.google.com/uc?id=1IEhzttk2AoxhkcsTOy-lJrYS1xPnqWU6&export=download
wget -O resnet18.prototxt https://drive.google.com/uc?id=1JxsIRT58EaPQUNlixww9sPnLMweMlsqR&export=download
cd -
# TODO: Download Sample Videos