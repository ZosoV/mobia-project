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