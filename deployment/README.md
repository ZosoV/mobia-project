# Deployment

In the following files, there is built the main pipeline for the mobia project. The main components of the pipeline are three models of Artificial Intelligence, which work in a cascade style in the following way:

1. A primary detector, known as **TrafficCamNet**, detects cars in a video (stream or storage).
2. A secondary detector, known as **LPDNet**, is applied on the previous detection to detect a plate into the car bbox.
3. Another secondary detector, known as **LPRNet**, is applied on the previous plate detection to recognize the characters on the license plate bbox.

Note: there are other components in the pipeline, but they will be explained later.

## How to build the environment?

To build this project, you have to follow the following steps:

1. Install docker. We will run the project in a docker container that includes all the libraries needed.
    * Please, refer to [Get Docker | Docker Documentation](https://docs.docker.com/get-docker/).
    * If applicable, follow the [Post-installation steps for Linux| Docker Documentation](https://docs.docker.com/engine/install/linux-postinstall/).
2. Install NVIDIA Container Toolkit
    * Please refer to [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
3. Before building the docker image, we must check that nvidia runtime is activated.
    * Please refer to [docker build with nvidia runtime](https://stackoverflow.com/questions/59691207/docker-build-with-nvidia-runtime)
4. Build the image. This step can take some minutes.

    ```console
    docker build -t "mobia-deployment:jetson" .
    ```
Note: The lines above are meant for Jetson devices. There are minor changes for building the image into GPU systems. Check [deepstream-main/Dockerfile](./deepstream-main/Dockerfile) and replace the lines according your needs.

5. Run a docker container in interactive mode. Check the bash [run_docker_ds.sh](./run_docker_ds.sh) for more details.
    ```console
    bash ../run_docker_ds.sh
    ```

Note: There are some volumes that must be added if you want to connect your display to see the video frames on the same computer.

## Deepstream Applications 

There are two deepstream applications in this project.

1. The first application [deepstream-main](./deepstream-main/) is the main deployment
2. The second application [deepstream-video2data](./deepstream-video2data/) is an util application to extract frames from videos, where there are correct detections.

