import argparse
import sys

sys.path.append("../")
import logging

import gi
import configparser

gi.require_version("Gst", "1.0")
from gi.repository import GObject, Gst

gi.require_version("GstRtspServer", "1.0")
from gi.repository import GstRtspServer

from gi.repository import GLib
from ctypes import *
import sys
import math

from common.is_aarch_64 import is_aarch64

# Additional imports
import common.multistream as multistream

import pyds
import os
import os.path
from os import path


class Pipeline:
    def __init__(self, path_config_global="configs/global_config.cfg") -> None:

        self.logger = logging.getLogger(
            __name__ + "." + self.__class__.__name__
        )
        
        self.config_global = configparser.ConfigParser()
        self.config_global.read(path_config_global)
        self.config_global.sections()

        self.sources = [val for _, val in self.config_global.items("sources")]
        self.number_sources = len(self.sources)

    def _create_element(self, factory_name, name, detail=""):
        """Creates an element with Gst Element Factory make.
        Return the element if successfully created, otherwise print to stderr
        and return None.
        """
        self.logger.info(f"Creating {name}")
        elm = Gst.ElementFactory.make(factory_name, name)

        if not elm:
            self.logger.error(f"Unable to create {name}")
            if detail:
                self.logger.error(detail)

        return elm

    def _create_h264parser(self):
        return self._create_element("h264parse", "h264-parser")

    def _decoder(self):
        return self._create_element("nvv4l2decoder", "nvv4l2-decoder")

    def _create_streammux(self):
        # Load attributes from global config file
        width = self.config_global.getint("streammux", "width")
        height = self.config_global.getint("streammux", "height")
        batched_push_timeout = self.config_global.getint("streammux", "batched-push-timeout")
        batch_size = self.config_global.getint("streammux", "batch-size")

        # Create plugin and set properties
        streammux = self._create_element("nvstreammux", "stream-muxer")

        streammux.set_property("width", int(width))
        streammux.set_property("height", int(height))
        streammux.set_property(
            "batched-push-timeout", int(batched_push_timeout)
        )
        streammux.set_property("batch_size", int(batch_size))

        return streammux

    def _prepare_multistream(self, streammux):

        # Creating sources bin
        for i in range(self.number_sources):
            self.logger.info("Creating source_bin {}...".format(i))

            # TODO: leer del archivo de configuracion
            uri_name = self.sources[i]
            if uri_name.find("rtsp://") == 0:
                self.is_live = True
            source_bin = multistream.create_source_bin(i, uri_name)
            if not source_bin:
                self.logger.error("Unable to create source bin \n")
            self.pipeline.add(source_bin)
            padname = "sink_%u" % i
            sinkpad = streammux.get_request_pad(padname)
            if not sinkpad:
                sys.stderr.write("Unable to create sink pad bin \n")
            srcpad = source_bin.get_static_pad("src")
            if not srcpad:
                sys.stderr.write("Unable to create src pad bin \n")
            srcpad.link(sinkpad)

    def _create_pgie(self, config_path):

        # Load attributes from global config file
        streammux_batch_size = self.config_global.getint("streammux", "batch-size")

        # Creating plugin and set properties
        pgie = self._create_element("nvinfer", "primary-inference")

        pgie.set_property("config-file-path", config_path)
        pgie_batch_size = pgie.get_property("batch-size")

        # Override the batch size with the streammux batch size
        # if there is not coincidence
        if pgie_batch_size != streammux_batch_size:
            self.logger.warning(
                "Overriding infer-config batch-size {} with streammux batch-size={}".format(
                    pgie_batch_size,
                    streammux_batch_size
                )
            )

            # Overriding the bath-size property
            pgie.set_property("batch-size", streammux_batch_size)
            
            # Overriding the engine property
            model_engine = pgie.get_property("model-engine-file")
            idx = model_engine.find("_b") + 2
            model_engine = model_engine[:idx] + str(streammux_batch_size) + model_engine[idx+1:]
            pgie.set_property("model-engine-file", model_engine)


        return pgie

    def _create_tiler(self):

        # Load attributes from global config file
        width = self.config_global.getint("tiler", "width")
        height = self.config_global.getint("tiler", "height")

        # Assign other attributes
        tiler_rows = int(math.sqrt(self.number_sources))
        tiler_columns = int(
            math.ceil((1.0 * self.number_sources) / tiler_rows)
        )

        # Create plugin and set properties
        tiler = self._create_element("nvmultistreamtiler", "nvtiler")
        tiler.set_property("rows", tiler_rows)
        tiler.set_property("columns", tiler_columns)
        tiler.set_property("width", width)
        tiler.set_property("height", height)

        return tiler

    def _create_tracker(self, config_path):

        # Load tracker config tracker
        config = configparser.ConfigParser()
        config.read(config_path)
        config.sections()

        # Load attributes from config tracker
        tracker_width = config.getint("tracker", "tracker-width", )
        tracker_height = config.getint("tracker", "tracker-height")
        gpu_id = config.getint("tracker", "gpu-id")
        ll_lib_file = config.get("tracker", "ll-lib-file")
        ll_config_file = config.get("tracker", "ll-config-file")
        enable_batch_process = config.getint("tracker", "enable-batch-process")
        enable_past_frame = config.getint("tracker", "enable-past-frame", fallback=None)

        # Create the plugin and set the properties
        tracker = self._create_element("nvtracker", "tracker")

        tracker.set_property("tracker-width", tracker_width)
        tracker.set_property("tracker-height", tracker_height)
        tracker.set_property("gpu_id", gpu_id)
        tracker.set_property("ll-lib-file", ll_lib_file)
        tracker.set_property("ll-config-file", ll_config_file)
        tracker.set_property("enable_batch_process", enable_batch_process)
        if enable_past_frame:
            tracker.set_property("enable_past_frame", enable_past_frame)

        return tracker

    def _create_sgie(self, name, config_path):
        sgie = self._create_element("nvinfer", name)
        sgie.set_property("config-file-path", config_path)
        return sgie

    def _create_nvvidconv(self, name):
        return self._create_element("nvvideoconvert", name)

    def _create_nvosd(self):
        return self._create_element("nvdsosd", "onscreendisplay")

    def _create_capsfilter(self, filter_type):
        # filter_type: I420 or RGBA
        str_line = f"video/x-raw(memory:NVMM), format={filter_type}"
        filter_type = Gst.Caps.from_string(str_line)

        # Create plugin and set properties
        caps = self._create_element("capsfilter", "filter")
        caps.set_property("caps", filter_type)
        return caps

    def _create_nvv4l2h264enc(self):
        # Load attributes from global config file
        codec = self.config_global.get("sink", "codec")
        bitrate = self.config_global.getint("sink", "bitrate")

        # Create plugin and set properties
        if codec == "H264":
            encoder = self._create_element("nvv4l2h264enc", "encoder H264")
        elif codec == "H265":
            encoder = self._create_element("nvv4l2h265enc", "encoder H265")

        encoder.set_property("bitrate", bitrate)
        if is_aarch64():
            encoder.set_property("preset-level", 1)
            encoder.set_property("insert-sps-pps", 1)
            encoder.set_property("bufapi-version", 1)

        return encoder

    def _create_rtppay(self):
        # Load attributes from global config file
        codec = self.config_global.get("sink", "codec")

        # Make the payload-encode video into RTP packets
        if codec == "H264":
            rtppay = self._create_element("rtph264pay", "rtppay H264")
        elif codec == "H265":
            rtppay = self._create_element("rtph265pay", "rtppay H265")

        return rtppay

    def _create_h264parse(self):
        return self._create_element("h264parse","h264_parse")

    def _create_mux(self):
        return self._create_element("mp4mux", "mux")

    def _create_sink(self, sink_type=0):

        # Check type of sink
        # Types-> RTSP: 0, MP4: 1, FakeSink: 2
        if sink_type == 0:
            # Load attributes from global config file
            updsink_port_num = self.config_global.getint(
                "sink", "updsink_port_num"
            )

            # Create plugin and set properties
            sink = self._create_element("udpsink", "udpsink")

            sink.set_property("host", "224.224.255.255")
            sink.set_property("port", updsink_port_num)
            sink.set_property("async", False)
            sink.set_property("sync", 1)
            sink.set_property("qos", 0)
        
        # MP4 Sink
        elif sink_type == 1:
            output_file = self.config_global.get("sink", "output_file")
            sink = self._create_element("filesink", "filesink")
            sink.set_property('location', output_file)

        # Fake Sink 
        elif sink_type == 2:
            sink = self._create_element("fakesink", "fakesink")

        return sink

    def _create_tee(self):
        return self._create_element("tee", "nvsink-tee")

    def _create_msgconv(self):

        # Load attributes from global config file
        config_file = self.config_global.get("nvmsgconv", "config_file")
        schema_type = self.config_global.getint("nvmsgconv", "schema_type")
        msg2p_newapi = self.config_global.getint("nvmsgconv", "msg2p-newapi", fallback=None)

        # Create plugin and set properties
        msgconv = self._create_element("nvmsgconv", "nvmsg-converter")
        msgconv.set_property('config', config_file)
        msgconv.set_property('payload-type', schema_type)
        if msg2p_newapi:
            msgconv.set_property('msg2p-newapi', msg2p_newapi)

        return msgconv

    def _create_msgbroker(self):

        # Load attributes from global config file
        proto_lib = self.config_global.get("nvmsgbroker", "proto_lib")
        cfg_file = self.config_global.get("nvmsgbroker", "cfg_file", fallback=None)

        conn_str = self.config_global.get("nvmsgbroker", "host") + ";"
        conn_str += self.config_global.get("nvmsgbroker", "port") + ";"
        conn_str += self.config_global.get("nvmsgbroker", "topic")

        # Create plugin and set properties
        msgbroker = self._create_element("nvmsgbroker", "nvmsg-broker")
        msgbroker.set_property('proto-lib', proto_lib)
        msgbroker.set_property('conn-str', conn_str)
        if cfg_file is not None:
            msgbroker.set_property('config', cfg_file)
        msgbroker.set_property('sync', False)

        return msgbroker

    def set_probe(self, plugin, pad_type, function, plugin_name = ""):
        # pad_type: sink or src
        pad = plugin.get_static_pad(pad_type)
        if not pad:
            sys.stderr.write(f"Unable to get {plugin_name}_{pad_type} pad \n")
        else:
            pad.add_probe(Gst.PadProbeType.BUFFER, function, 0)

    def create_pipeline(self):
        # method to override

        # Init the Gst streamer and pipeline classes
        # Create the plugins
        # Add the plugins to the pipeline
        # Link the plugins
        # Add probes it is needed
        pass

    def run_main_loop(self):
        # Method to override
        pass
