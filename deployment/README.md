# Deployment

In the following files, there is built the main pipeline for the mobia project. The main components of the pipeline are three models of Artificial Intelligence, which work in a cascade style in the following way:

1. A primary detector, known as **TrafficCamNet**, detects cars in a video (stream or storage).
2. A secundary detector, known as **LPDNet**, is applied on the previous detection to detect plate into the car bbox.
3. Another secundary detector, known as **LPRNet**, is applied on the previous plate detection to recognize the characters on the license plate bbox.

Note: there are other components in the pipeline, but there will be explained later.

## How to run?

To run this project, you have to follow the next steps:

1. Install docker. We are going to run the project in a docker container which includes all the libraries needed.
    * Please, refer to [Get Docker | Docker Documentation](https://docs.docker.com/get-docker/).
    * If applicable, follow the [Post-installation steps for Linux| Docker Documentation](https://docs.docker.com/engine/install/linux-postinstall/).
2. Install NVIDIA Container Toolkit
    * Please refer to [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
3. Before building the docker image, we have to check that nvidia runtime is activated.
    * Please refer to [docker build with nvidia runtime](https://stackoverflow.com/questions/59691207/docker-build-with-nvidia-runtime)
4. Build the image within the folder [deepstream-main/](./deepstream-main/)

    ```console
    cd ..
    docker build -t "mobia-deployment:jetson" .
    ```
Note: The lines above are meant to Jetson devices. There are minor changes for building the image into GPU systems. Check [deepstream-main/Dockerfile](./deepstream-main/Dockerfile) and replace the lines according your needs.

5. Run a docker container in interactive mode. Check the bash [run_docker_ds.sh](./run_docker_ds.sh) for more details.
    ```console
    bash ../run_docker_ds.sh
    ```

Note: There are some volumenes that must be added if you want to connect your display for see the video frames in the same computer.

6. Before running the deepstream app, we have to make sure that the library [./deepstream-main/nvinfer_custom_lpr_parser/libnvdsinfer_custom_impl_lpr.so](./deepstream-main/nvinfer_custom_lpr_parser/libnvdsinfer_custom_impl_lpr.so) is available. That library is useful for parsing the character detection in a readable format. If that library is not available, please run the Makefile into the folder [./deepstream-main/nvinfer_custom_lpr_parser/](./deepstream-main/nvinfer_custom_lpr_parser/).
    ```console
    cd deepstream-main/nvinfer_custom_lpr_parser
    make
    cd ..
    ```

6. Run the deepstream app into the docker container by running the scrip [run_deepstream.sh](./deepstream-main/run_deepstream.sh). Check the script for more details.
    ```console
    bash run_deepstream.sh
    ```
