# Main DeepStream Application

## Requirements

1. Complete the steps on [deployment](../README.md) to build the adequate environment for this application.

2. Make sure that the library [`../nvinfer_custom_lpr_parser/libnvdsinfer_custom_impl_lpr.so`](../nvinfer_custom_lpr_parser/libnvdsinfer_custom_impl_lpr.so) is available. That library is useful for parsing the character recognition in a readable format. If that library is not available, please run the Makefile into the folder [`../nvinfer_custom_lpr_parser/`](../nvinfer_custom_lpr_parser/) for compiling the library.

    ```console
    cd nvinfer_custom_lpr_parser/ && make && cd ..
    ```

## Running steps

1. Run the Docker container by running the scrip [`../run_deepstream.sh`](../run_deepstream.sh). Check the Bash script for more details.

    ```console
    bash run_deepstream.sh
    ```

2. Navigate into the workspace to `deepstream-main` directory and run the script [`run_deepstream.sh`](run_deepstream.sh). Also, you can check the Bash script for more details

    ```console
    cd deepstream-main/ && bash run_deepstream.sh
    ```
    
