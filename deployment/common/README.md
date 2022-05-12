# Pipeline Class

This is the parent class of the specific pipelines that will be built in the different applications. As a summary, the class loads a configuration file, creates elements/connectors and allows their use by adding and linking according to the applications. The explanation of the code is below, in the following sections.

## Initialization

The class is initialized through `__init__` using a configuration file that is loaded from the parser. The default configuration file is `../configs/global_config.cfg` and the first values loaded from it are the video sources.

## Element creation

The `_create_element(self, factory_name, name, detail="")` method, as the name suggests, creates a pipeline element using `Gst.ElementFactory.make` from the `gi` repository and also handles exceptions if an element cannot be created. The following pipeline elements can be created using this method.

- `_create_streammux(self)` batch video streams before sending for AI inference. The attributes are loaded from `../configs/global_config.cfg`.
- `_prepare_multistream(self, streammux)` according to the sources specified in `../configs/global_config.cfg`. The `multistream.py` contains the functions to prepare source bin, and `streammux` is for the creation of `sinkpad`.
- `_create_pgie(self, config_path)` uses the batch information in `../configs/global_config.cfg` to create the primary inference for cars. Also, this configuration file has the path to `config_path` in order to set pgie.
- `_create_tiler(self)` composites a 2D tile from batched buffers.
- `_create_tracker(self, config_path)` enables multiple neural networks to reside within a single pipeline.
- `_create_sgie(self, name, config_path)` allows to create secondary inferences.
- `_create_nvvidconv(self, name)` performs video color format conversion.
- `_create_nvosd(self)` draws bounding boxes, text and region of interest (ROI) polygons.
- `_create_capsfilter(self, filter_type)` constructs a color channel filter for a `filter_type`: I420 or RGBA.
- `_create_nvv4l2h264enc(self)` encodes RAW data in I420 or RGBA format to H264 or H265.
- `_create_rtppay(self)` converts H264 or H265 encoded Payload to RTP packets (RFC 3984).
- `_create_h264parse(self)` parses the incoming H264 stream.
- `_create_mux(self)` merges streams (audio and video) into ISO MPEG-4 (.mp4) files.
- `_create_sink(self, sink_type=0)` writes incoming data to a `sink_type`: RSTP, MP4 or Fake sink. 
- `_create_tee(self)` branches the data. Useful for Kafka.
- `_create_msgconv(self)` converts metadata into messages.
- `_create_msgbroker(self)` sends payload messages to the server using a specified communication protocol.
- `set_probe(self, plugin, pad_type, function, plugin_name = "")` gets the metadata information between plugins (source and sink).
