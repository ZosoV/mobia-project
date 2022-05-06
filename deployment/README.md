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

## DeepStream Applications

There are two DeepStream applications in this project.

1. The first application [deepstream-main](./deepstream-main/) is the main deployment
2. The second application [deepstream-video2data](./deepstream-video2data/) is an util application to extract frames from videos, where there are correct detections.

