# Deployment

The main pipeline for the Mobia project is built in the following files. The main components are three Artificial Intelligence models, which are cascaded as follows:

1. A primary detector, known as **TrafficCamNet**, which detects **cars** in a video (streaming or stored).
2. A secondary detector, known as **LPDNet**, which detects a **license plate** in the region of interest built on the previous detection.
3. Another secondary detector, known as **LPRNet**, is applied on the previous license plate detection to recognize the **characters**.

Note: there are other components in the pipeline, but they will be explained later.

## Build the environment

We followed the steps below to build this project on Jetson Xavier NX with JetPack :tm: 4.6.1:

1. [Install Docker](https://docs.docker.com/get-docker/) and follow the [post-installation steps for Linux in the Docker Documentation](https://docs.docker.com/engine/install/linux-postinstall/). We will run the project in a Docker container that includes all the libraries needed.
2. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html).
3. Before building the Docker image, we must check that NVIDIA runtime is activated. Please refer to [Docker build with NVIDIA runtime](https://stackoverflow.com/questions/59691207/docker-build-with-nvidia-runtime).
4. Build the image through the CLI. This step can take some minutes.

    ```console
    docker build -t "mobia-deployment:jetson" .
    ```

    *Note*: There are minor changes for building the image into GPU systems. Check the [`deepstream-main/Dockerfile`](./deepstream-main/Dockerfile) and replace the lines according your needs.

5. Run a Docker container in interactive mode. Check the Bash script [`run_docker_ds.sh`](./run_docker_ds.sh) for more details.

    ```console
    bash ../run_docker_ds.sh
    ```

    *Note*: There are some volumes that must be added if you want to connect your display to see the video frames on the same computer.

## Directory Structure

```
deployment
|   Dockerfile          -> Instructions to build the Docker image
|   README.md           -> Repo instructions
|   run_docker_ds.sh    -> Bash file to run Docker
├── commons -> Useful libraries
|   ├── FPS.py          -> FPS handling
|   ├── __init__.py     -> Treat directory as package container
|   ├── bus_call.py     -> For streamming message
|   ├── is_aarch_64.py  -> Check ARM 64-bits architecture
|   ├── multistream.py  -> Creation and handling of GstElements
|   ├── pipeline.py     -> Inheritance pipeline mold
|   └── utils.py        -> Unsigned int codification
├── configs
|   ├── general_tracker_config.txt  -> Tracker
|   ├── lpdnet_sgie1_config.txt     -> LPDNet
|   ├── lprnet_sgie2_config.txt     -> LPRNet
|   ├── tcnet_pgie_config.txt       -> TrafficCamNet
|   └── tracker_config.yml          -> Tracker complement
├── data    -> Model information
|   ├── pgies/tcnet -> Primary detector
|   |   ├── labels.txt
|   |   ├── resnet18_trafficcamnet_pruned.etlt
|   |   ├── resnet18_trafficcamnet_pruned.etlt_b1_gpu0_int8.engine
|   |   ├── resnet18_trafficcamnet_pruned.etlt_b2_gpu0_int8.engine
|   |   └── trafficcamnet_int8.txt
|   ├── sgies -> Secondary detectors
|   |   ├── lpdnet
|   |   |   ├── usa_lpd_cal_dla.bin
|   |   |   ├── usa_lpd_label.txt
|   |   |   ├── usa_pruned.etlt
|   |   |   └── usa_pruned.etlt_b16_gpu0_int8.engine
|   |   ├── lprnet
|   |   |   ├── us_lp_characters.txt
|   |   |   ├── us_lprnet_baseline18_deployable.etlt
|   |   |   └── us_lprnet_baseline18_deployable.etlt_b16_gpu0_fp16.engine
|   ├── videos
|   └── download_base_models.sh -> Bash script to download detection models
├── deepstream-main
|   ├── configs
|   |   └── global_config.cfg   -> App configuration
|   ├── README.md   -> App instructions
|   ├── globals.py  -> Variables
|   ├── main.py     -> Core
|   ├── probes.py   -> Display and metadata extraction
|   └── run_deepstream.sh   -> Bash script to run the app
├── deepstream-msg2kafka
|   ├── configs
|   |   └── global_config.cfg
|   ├── nvmsgconv
|   |   ├── deepstream_schema
|   |   |   ├── deepstream_schema.cpp
|   |   |   ├── deepstream_schema.h
|   |   |   ├── dsmeta_payload.cpp
|   |   |   └── eventmsg_payload.cpp
|   |   ├── Makefile
|   |   ├── README
|   |   ├── nvmsgconv.cpp
|   |   └── nvmsgconv.h
|   ├── README.md
|   ├── cfg_kafka.txt
|   ├── create_topic.sh
|   ├── deepstream_test_4.py
|   ├── download_kafka.sh
|   ├── dstest4_pgie_config.txt
|   ├── globals.py
|   ├── main.py
|   ├── probes.py
|   ├── run_consumer.py
|   ├── run_deepstream.sh
|   ├── run_kafka_server.sh
├── deepstream-video2data
|   ├── configs
|   |   └── global_config.cfg   -> App configuration
|   ├── README.md   -> App instructions
|   ├── globals.py  -> Variables
|   ├── imagedata-app-block-diagram.png -> Pipeline design
|   ├── main.py     -> Core
|   ├── probes.py   -> Display and metadata extraction
|   └── run_deepstream.sh   -> Bash script to run the app
└── nvinfer_custom_lpr_parser
    ├── Makefile    -> Building
    └── nvinfer_custom_lpr_parser.cpp   -> Character processing
```

## DeepStream Applications

There are two DeepStream applications in this project.

1. The first application [deepstream-main](./deepstream-main/) is the main deployment
2. The second application [deepstream-msg2kafka](./deepstream-msg2kafka/) is an application under development for analytica.
3. The third application [deepstream-video2data](./deepstream-video2data/) is an util application to extract frames from videos, where there are correct detections.

## Pipeline Architecture

_Pass_
