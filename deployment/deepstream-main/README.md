# Main DeepStream Application

## Requirements

1. Complete the steps on [deployment](../README.md) to build the adequate environment for this application.

2. Make sure that the library [`../nvinfer_custom_lpr_parser/libnvdsinfer_custom_impl_lpr.so`](../nvinfer_custom_lpr_parser/libnvdsinfer_custom_impl_lpr.so) is available. That library is useful for parsing the character recognition in a readable format. If that library is not available, please run the Makefile into the folder [`../nvinfer_custom_lpr_parser/`](../nvinfer_custom_lpr_parser/) for compiling the library.

    ```console
    cd nvinfer_custom_lpr_parser/ && make && cd ..
    ```

## Structure
![DeepStream Main diagram](img/diagram.png "DeepStream Main app comunication")

## Explanation

### The main script

The `main.py` script is called adding the `configs/global_config.cfg` as the default configuration file. 

### Imports

#### App

There are two packages in the same folder of `main.py`:

- `globals.py` contains the global variables for the app.
- `probes.py` handles the metadata display.

#### Common

There are four packages from `common` directory:

- `bus_call` streams message.
- `FPS` handles the frame streamming.
- `is_aarch_64` detects the ARM 64-bits architecture.
- `pipeline` inherits as parent to app pipelines.

#### Installed

Installed packages from repositories:

- `coloredlogs` — Colored terminal output for Python's logging module.
- `gi` — Pure Python GObject Introspection Bindings.

#### Built-in

Also, this app uses built-in packages:

- `argparse` — Parser for command-line options, arguments and sub-commands.
- `ctypes` — A foreign function library for Python.
- `logging` — Logging facility for Python.
- `sys` — System-specific parameters and functions.

### The configuration file

The `configs/global_config.cfg` contains information about the sources, streammux, detection models, tiler and sink. This file communicates with `../configs/` directory, which contains the configuration for all detection models. It should be noted that the LPRNet Secondary GPU Inference Engine uses a compiled library from C++ called `../nvinfer_custom_lpr_parser/libnvdsinfer_custom_impl_lpr.so`.

### Initialization

`main.py` contains the class `MainDeepStreamPipeline`, which receives the `Pipeline` class from `pipeline` package in order to build the appropriate conection according to requirements.

#### Sink Type

After reading the `configs/global_config.cfg`, the app check the configured output type: only RTSP protocol or MP4 format.

#### Streamming

Keep track of the frames per second of all configured streams using `FPS_STREAMS`, a global variable in the `globals.py` file.

#### Pipeline

The pipeline is built based on the `Pipeline` parent structure and also using `gi` package for bindings. The app refers to this class for the construction of each element. Also, `pipeline` uses `multistream.py` package. For a detailed view, please refer to [`../common/pipeline.py`](../common/pipeline.py) or [`../common/README.md`](../common/README.md).

### Adding and linking elements

Through list iterations using the `Pipeline` class too.

### Probes

`probes.py` to display FPS and get metadata information.

## Running steps

1. Run the Docker container by running the scrip [`../run_deepstream.sh`](../run_deepstream.sh). Check the Bash script for more details.

    ```console
    bash run_deepstream.sh
    ```

2. Navigate into the workspace to `deepstream-main` directory and run the script [`run_deepstream.sh`](run_deepstream.sh). Also, you can check the Bash script for more details

    ```console
    cd deepstream-main/ && bash run_deepstream.sh
    ```
    
