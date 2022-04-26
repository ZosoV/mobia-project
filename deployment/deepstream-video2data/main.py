import globals as G
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
from common.bus_call import bus_call
from common.FPS import GETFPS

# Additional imports
import probes

import pyds
import os
import os.path
from os import path

from common.pipeline import Pipeline

class Video2DataPipeline(Pipeline):
    def __init__(self,  *args, **kw):
        super().__init__(*args, **kw)

        # Get the sink type
        # Types-> RTSP: 0, MP4: 1, FakeSink: 2
        self.sink_type = self.config_global.getint("sink", "type")
        if self.sink_type != 2:
            sys.stderr.write(f"This app only accepts fakesink. Check {kw['path_config_global']} \n" )
            sys.exit(1)

        self.create_pipeline()

    def create_pipeline(self):

        # Keep track of the frames per second with a global variable
        # in the globals.py file
        for i in range(self.number_sources):
            G.FPS_STREAMS["stream{0}".format(i)] = GETFPS(i)

        # Loading specific attributes for this application
        video2data_attribs = dict(self.config_global["video2data"])

        # Create output folder
        output_folder = video2data_attribs["output_folder"]
        if path.exists(output_folder):
            sys.stderr.write("The output folder %s already exists. Please remove it first.\n" % output_folder)
            sys.exit(1)
        
        os.mkdir(output_folder)
        print("Frames will be saved in ", output_folder)

        # Create subfolders and init global counters
        for i in range(self.number_sources):
            os.mkdir(output_folder + "/stream_" + str(i))
            os.mkdir(output_folder + "/stream_" + str(i) + "_crops")
            G.FRAME_COUNT["stream_" + str(i)] = 0
            G.SAVED_COUNT["stream_" + str(i)] = 0

        # Standard GStreamer initialization
        GObject.threads_init()
        Gst.init(None)

        # Create gstreamer elements */
        # Create Pipeline element that will form a connection of other elements
        print("Creating pipeline...\n")
        self.pipeline = Gst.Pipeline()
        self.is_live = False

        if not self.pipeline:
            sys.stderr.write(" Unable to create Pipeline \n")

        # Create nvstreammux instance to form batches from one or more sources.
        streammux = self._create_streammux()
        self.pipeline.add(streammux)

        # Creating multistream mechanism
        self._prepare_multistream(streammux)

        # Create queues
        print("\nCreating queues")
        queue1 = self._create_element("queue", "queue1")
        queue2 = self._create_element("queue", "queue2")
        queue3 = self._create_element("queue", "queue3")
        queue4 = self._create_element("queue", "queue4")
        queue5 = self._create_element("queue", "queue5")
        queue6 = self._create_element("queue", "queue6")
        queue7 = self._create_element("queue", "queue7")
        queue8 = self._create_element("queue", "queue8")
        queue9 = self._create_element("queue", "queue9")
        queue10 = self._create_element("queue", "queue10")

        # Getting configs paths of the models
        pgie_cfg_path = self.config_global.get("models","pgie_config")
        sgie1_cfg_path = self.config_global.get("models","sgie1_config")
        sgie2_cfg_path = self.config_global.get("models","sgie2_config")
        tracker_cfg_path = self.config_global.get("models","tracker_config")


        # Create main plugins
        print("\nCreating main plugins")
        pgie = self._create_pgie(config_path = pgie_cfg_path)
        tracker = self._create_tracker(config_path = tracker_cfg_path)
        sgie1 = self._create_sgie(name="secondary1-nvinference-engine",
                                  config_path=sgie1_cfg_path)
        sgie2 = self._create_sgie(name="secondary2-nvinference-engine",
                                  config_path=sgie2_cfg_path)
        nvvidconv1 = self._create_nvvidconv(name="convertor_1")
        caps_RGBA = self._create_capsfilter(filter_type = "RGBA")
        tiler = self._create_tiler()
        nvvidconv2 = self._create_nvvidconv(name="convertor_2")
        nvosd = self._create_nvosd()

        # For RTSP Sink
        if self.sink_type == 0:
            nvvidconv_postosd = self._create_nvvidconv(name="convertor_postosd")
            caps = self._create_capsfilter(filter_type="I420")
            encoder = self._create_nvv4l2h264enc()
            rtppay = self._create_rtppay()

        # output
        sink = self._create_sink(sink_type = self.sink_type)
        
        # Specific configurations for this application
        if not is_aarch64():
            # Use CUDA unified memory in the pipeline so frames
            # can be easily accessed on CPU in Python.
            mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)
            streammux.set_property("nvbuf-memory-type", mem_type)
            nvvidconv1.set_property("nvbuf-memory-type", mem_type)
            nvvidconv2.set_property("nvbuf-memory-type", mem_type)
            tiler.set_property("nvbuf-memory-type", mem_type)

        # TODO: Revisar si se lo puede incluir dentro de la funcion de configuracin
        if self.is_live:
            print("Atleast one of the sources is live")
            streammux.set_property("live-source", 1)


        # This list defines the order for linking the pluggins
        plugins = [
            streammux,
            queue1,
            pgie,
            queue2,
            tracker,
            queue3,
            sgie1,
            queue4,
            sgie2,
            queue5,
            nvvidconv1,
            queue6,
            caps_RGBA,
            queue7,
            tiler,
            queue8,
            nvvidconv2,
            queue9,
            nvosd,
            queue10,
            ]

        # RTSP sink
        if self.sink_type == 0:
            plugins += [nvvidconv_postosd,
                                caps,
                                encoder,
                                rtppay, 
                                sink]

        # Fake sink
        if self.sink_type == 2:
            plugins += [sink]

        print("Adding elements to Pipeline \n")
        for plugin in plugins[1:]:
            self.pipeline.add(plugin)

        print("Linking elements in the Pipeline \n")
        for i in range(len(plugins) - 1):
            plugins[i].link(plugins[i + 1])

        # TODO: You can add probe callbacks
        tiler_sink_pad = tiler.get_static_pad("sink")
        if not tiler_sink_pad:
            sys.stderr.write(" Unable to get src pad \n")
        else:
            tiler_sink_pad.add_probe(
                Gst.PadProbeType.BUFFER, probes.tiler_sink_pad_buffer_probe(video2data_attribs), 0
            )

    def run_main_loop(self):

        # create an event loop and feed gstreamer bus mesages to it
        loop = GObject.MainLoop()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, loop)

        # List the sources
        print("Now playing...")
        # TODO: cargar desde el archivo de configuracion
        for i, source in enumerate(self.sources):
            print(i, ": ", source)

        print("Starting pipeline \n")
        # start play back and listed to events
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            loop.run()
        except:
            pass
        # cleanup
        print("Exiting app\n")
        self.pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    description = 'Deepstream Main Application set a config file'
    parser = argparse.ArgumentParser(description)
    
    parser.add_argument('--config',
                        default = 'configs/global_config.cfg',
                        type    = str,
                        help    = 'global configuration file')

    args = parser.parse_args()
    new_pipeline = Video2DataPipeline(path_config_global = args.config )
    new_pipeline.run_main_loop()