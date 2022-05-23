# Video to Data DeepStream Application

This DeepStream application help us to extract frames from videos where there are correct detections, which guarantees is certain degree that the frame contains a car/plate. To the detection, we used the base models.

## Prerequisites

The following software is already installed in the Docker container:
- DeepStreamSDK 6.0.1
- Python 3.6
- Gst-python
- NumPy package
- OpenCV package

If you want to install required packages (last two) for any reason, run the following CLI command:

```bash
sudo apt update
sudo apt install python3-numpy python3-opencv -y
```

## Running App

On CLI, run the command:

```bash
python3 main.py <uri1> [uri2] ... [uriN] <FOLDER NAME TO SAVE FRAMES>
```  
For example, to get data from MP4 videos and save in `frames` folder:

```bash
python3 main.py file:///home/ubuntu/video1.mp4 file:///home/ubuntu/video2.mp4 frames
```

And for example, to get data using RTSP and save in `frames` folder:

```bash
python3 main.py rtsp://127.0.0.1/video1 rtsp://127.0.0.1/video2 frames
```

## Explanation

### `configs/global_config.cfg`

This configuration file is based on the main app configuration file and differs from it by having one more section `[video2data]`. The key names in this section are the following:

- **output_folder** – *str*, Directory to save the frames.
- **period_per_save** – *int*, Period of frames in which the information is stored.
- **min_confidence_car** – *float*, Minimal confidence to save car image. Accepted values are between 0,0 and 1,0.
- **min_confidence_plate** – *float*, Minimal confidence to save license plate image. Accepted values are between 0,0 and 1,0.
- **min_confidence_characters** – *float*, Minimal confidence to save image with license plate characters. Accepted values are between 0,0 and 1,0.
- **save_labeled_copy** – *int*, Flag to save or not a labeled copy of image. Accepted values are 0 or 1.
- **save_with_date_time** – *int*, Flag to save or not image with date and time information. Accepted values are 0 or 1.

### `main.py`

#### Initialization (`__init__`)

`main.py` contains the class `Video2DataPipeline`, which inherits the `Pipeline` class from `pipeline` package in order to use their methods to create pluggins and other util functions.

1. Use `super().__init__(*args, **kw)` to read the config file `configs/global_config.cfg`.
2. Check the configured output type: only FakeSink. Note that the reading of the configuration file is done from the parent class.
3. Execute `create_pipeline()`.

#### `create_pipeline(self)`

The function consists in the following steps:

1. Assign FPS per each configured camera using `FPS_STREAMS`, a global variable in the `globals.py` file.
2. Loading specific attributes for this application located on `configs/global_config.cfg`.
3. Set current date and time, and create the output folder. 
3. Initialize the GObject using `GObject.threads_init()`, `Gst.init(None)` and `Gst.Pipeline()`.
4. As the class is based on `Pipeline`, the app uses their methods to create each element/plugin. In order to do that, we mostly used the following lines: `self._create_<plugin_name>(<parameters>)`. For a detailed view, please check the methods on [`../common/pipeline.py`](../common/pipeline.py) or [`../common/README.md`](../common/README.md).
5. Adding elements to `self.pipeline`.
6. Linking elements through list iterations using the `Pipeline` class too.
7. If necessary, add probes using the function `self.set_probe(plugin, pad_type, function, plugin_name)`. Note that the `function` attribute must be defined in `probes.py`.

##### Structure
![Main pipeline diagram](img/pipeline.png "DeepStream Main pipeline diagram")

### `probes.py`

`probes.py` gets metadata information from inference: pgie and sgie. The probe must be attached to a pad on a plugin. In this application, the probe is attached to the sink pad (the input) of the tiler plugin.

#### Extract Metadata with a GStreamer Probe

The `tiler_sink_pad_buffer_probe(video2data_attribs)` function use `auxiliar_func(pad, info, u_data)` as a callback that executes each time there is new frame data on the sink pad. The `video2data_attribs` come from `[video2data]` section of `configs/global_config.cfg`. With this probe, we can extract a snapshot of the metadata coming into the tiler plugin. For more information about metadata structure, check the [`README.md`](../deepstream-main/README.md) of the main application.

#### Saving Data and Annotation per Period

Inside `auxiliar_func(pad, info, u_data)` there is a checker of the frame number. If this number is a period of `period_per_save`, then we proceed to save information using `extract_save_data` function. This function makes the following actions:

1. Extract the frame data using the [`get_nvds_buf_surface`](https://docs.nvidia.com/metropolis/deepstream/python-api/PYTHON_API/Methods/methodsdoc.html?highlight=get_nvds_buf_surface#pyds.get_nvds_buf_surface) method.
2. Convert to NumPy format and then to OpenCV. If applicable, copy the result to draw bounding boxes and check detections.
3. If the object is a car or a plate with a higher confidence that a threshold, save the annotation in a specific format with respect to the current frame in a file.
4. Additionally, if the object is a plate, check the classification of this object. If the confidence is higher than the threshold, then we save the crop of the plate and  its label (characters).
5. If applicable, save information of the current frame (frame_img, crops and annotations) from the previous collected information.

#### Display Frame Information through MetaData

A `display_meta` object of type `NvDsDisplayMeta` is allocated to be copied later into `frame_meta`.  The text element of `display_meta` is set as the `py_nvosd_text_params` variable, of structure `NvOSD_TextParams`, with the following elements:

- **display_text** – *str*, Holds the text to be overlaid.
- **x_offset** – *int*, Holds horizontal offset w.r.t top left pixel of the frame.
- **y_offset** – *int*, Holds vertical offset w.r.t top left pixel of the frame.
- **font_params** – `NvOSD_FontParams`, Holds the font parameters of the text to be overlaid.
- **set_bg_clr** – *int*, Boolean to indicate text has background color.
- **text_bg_clr** – `NvOSD_ColorParams`, Holds the text’s background color, if specified.

The [DeepStream Python API Reference](https://docs.nvidia.com/metropolis/deepstream/python-api/index.html) provides details for all of the metadata structure properties and methods.

This document describes the sample deepstream-imagedata-multistream application.

This sample builds on top of the deepstream-test3 sample to demonstrate how to:

* Access imagedata in a multistream source
* Modify the images in-place. Changes made to the buffer will reflect in the downstream but color format, resolution and numpy transpose operations are not permitted.  
* Make a copy of the image, modify it and save to a file. These changes are made on the copy of the image and will not be seen downstream.
* Extract the stream metadata, imagedata, which contains useful information about the
  frames in the batched buffer.
* Annotating detected objects within certain confidence interval
* Use OpenCV to draw bboxes on the image and save it to file.
* Use multiple sources in the pipeline.
* Use a uridecodebin so that any type of input (e.g. RTSP/File), any GStreamer
  supported container format, and any codec can be used as input.
* Configure the stream-muxer to generate a batch of frames and infer on the
  batch for better resource utilization.

NOTE:
- For x86, only CUDA unified memory is supported.
- Only RGBA color format is supported for access from Python. Color conversion
  is added in the pipeline for this reason.

This sample accepts one or more H.264/H.265 video streams as input. It creates
a source bin for each input and connects the bins to an instance of the
"nvstreammux" element, which forms the batch of frames. The batch of
frames is fed to "nvinfer" for batched inferencing. The batched buffer is
composited into a 2D tile array using "nvmultistreamtiler." The rest of the
pipeline is similar to the deepstream-test3 and deepstream-imagedata sample.

The "width" and "height" properties must be set on the stream-muxer to set the
output resolution. If the input frame resolution is different from
stream-muxer's "width" and "height", the input frame will be scaled to muxer's
output resolution.

The stream-muxer waits for a user-defined timeout before forming the batch. The
timeout is set using the "batched-push-timeout" property. If the complete batch
is formed before the timeout is reached, the batch is pushed to the downstream
element. If the timeout is reached before the complete batch can be formed
(which can happen in case of rtsp sources), the batch is formed from the
available input buffers and pushed. Ideally, the timeout of the stream-muxer
should be set based on the framerate of the fastest source. It can also be set
to -1 to make the stream-muxer wait infinitely.

The "nvmultistreamtiler" composite streams based on their stream-ids in
row-major order (starting from stream 0, left to right across the top row, then
across the next row, etc.).


