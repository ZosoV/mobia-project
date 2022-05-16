# Pipeline Class

This is the parent class of the specific pipelines that will be built in the different applications. As a summary, the class loads a configuration file, creates elements/plugins and allows their use by adding and linking according to the applications. 

This class allow us to create new applications easily. To create a new application we need to instantiate a new class `NewPipeline` and inherit our class `Pipeline`. Then, we just need to update two methods: `create_pipeline` and `run_main_loop`, according to specifications.

## Initialization

The class is initialized through `__init__` using a configuration file that is loaded from the parser. The default configuration file is `../configs/global_config.cfg` and the first values loaded from it are the video sources.

## Methods
The following methods allow us to create specific components of a given application. The explanation of each methods is below.

One of the most used method is `_create_element(self, factory_name, name, detail="")`, as the name suggests, creates a pipeline element using `Gst.ElementFactory.make` from the `gi` repository and also handles exceptions if an element cannot be created. In this way, the following pipeline elements can be created using this method.

- `_create_streammux(self)` creates a batch of video frames before sending for AI inference.
- `_prepare_multistream(self, streammux)` allows the creation multiple entries to the pipeline using the attributes `self.sources`, which was previously loaded in `__init__` function. This method uses some functions of `multistream.py`, which prepare source bin. Note that you requiere to pass the `streammux` attribute for the creation of `sinkpad`. 
- `_create_pgie(self, config_path)` creates the primary inference.
- `_create_tiler(self)` composites a 2D tile from batched buffers.
- `_create_tracker(self, config_path)` creates a tracker plugin and enables multiple neural networks to reside within a single pipeline.
- `_create_sgie(self, name, config_path)` allows to create secondary inferences.
- `_create_nvvidconv(self, name)` performs video color format conversion.
- `_create_nvosd(self)` draws bounding boxes, text and region of interest (ROI) polygons.
- `_create_capsfilter(self, filter_type)` constructs a color channel filter for a `filter_type`: I420 or RGBA.
- `_create_nvv4l2h264enc(self)` encodes RAW data in I420 or RGBA format to H264 or H265.
- `_create_rtppay(self)` converts H264 or H265 encoded Payload to RTP packets (RFC 3984).
- `_create_h264parse(self)` parses the incoming H264 stream.
- `_create_mux(self)` merges streams (audio and video) into ISO MPEG-4 (.mp4) files.
- `_create_sink(self, sink_type=0)` create a pipeline output according to a `sink_type`: RSTP, MP4 or Fake sink. 
- `_create_tee(self)` branches the incoming video streams in different source pads. Useful for Kafka.
- `_create_msgconv(self)` converts metadata into event messages and consequently into a payload messages.
- `_create_msgbroker(self)` sends payload messages to the server using a specified communication protocol.
- `set_probe(self, plugin, pad_type, function, plugin_name = "")` allows to embed a probe function into the pipeline, indicating the place with the plugin and pad type.
