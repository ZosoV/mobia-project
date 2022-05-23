import globals as G
import argparse
import sys

sys.path.append("../")

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

import pyds

# Additional imports
import probes
import coloredlogs, logging
# you can use %(asctime)s if you need
coloredlogs.install(fmt= '[%(levelname)s] | (%(filename)s:%(levelno)s) | %(message)s',level='DEBUG')

from common.pipeline import Pipeline

class MainDeepstreamPipeline(Pipeline):
    def __init__(self,  *args, **kw):
        super().__init__(*args, **kw)

        # Get the sink type
        # Types-> RTSP: 0, MP4: 1, FakeSink: 2
        self.sink_type = self.config_global.getint("sink", "type")
        if self.sink_type != 0 and self.sink_type != 1:
            sys.stderr.write(f"This app only accepts rtsp or mp4 sinks. Check {kw['path_config_global']} \n" )
            sys.exit(1)

        self.create_pipeline()

    def create_pipeline(self):

        # Keep track of the frames per second with a global variable
        # in the globals.py file
        for i in range(self.number_sources):
            G.FPS_STREAMS["stream{0}".format(i)] = GETFPS(i)
            G.COUNTER_CARS["stream{0}".format(i)] = 0

        # Standard GStreamer initialization
        GObject.threads_init()
        Gst.init(None)

        # Create Pipeline element that will form a connection of other elements
        logging.info("Creating pipeline...\n")
        self.pipeline = Gst.Pipeline()
        self.is_live = False

        if not self.pipeline:
            logging.error(" Unable to create Pipeline \n")

        # Create nvstreammux instance to form batches from one or more sources.
        streammux = self._create_streammux()
        self.pipeline.add(streammux)

        # Creating multistream mechanism
        self._prepare_multistream(streammux)

        # Create queues
        logging.info("Creating queues")
        queue1 = self._create_element("queue", "queue1")
        queue2 = self._create_element("queue", "queue2")
        queue3 = self._create_element("queue", "queue3")
        queue4 = self._create_element("queue", "queue4")
        queue5 = self._create_element("queue", "queue5")
        queue6 = self._create_element("queue", "queue6")
        queue7 = self._create_element("queue", "queue7")
        queue8 = self._create_element("queue", "queue8")
        queue9 = self._create_element("queue", "queue9")

        # Getting configs paths of the models
        pgie_cfg_path = self.config_global.get("models", "pgie_config")
        sgie1_cfg_path = self.config_global.get("models", "sgie1_config")
        sgie2_cfg_path = self.config_global.get("models", "sgie2_config")
        sgie3_cfg_path = self.config_global.get("models", "sgie3_config")
        tracker_cfg_path = self.config_global.get("models", "tracker_config")

        # Create main plugins
        logging.info("Creating main plugins")
        pgie = self._create_pgie(config_path=pgie_cfg_path)
        tiler = self._create_tiler()
        tracker = self._create_tracker(config_path=tracker_cfg_path)
        sgie1 = self._create_sgie(
            name="secondary1-nvinference-engine", config_path=sgie1_cfg_path
        )
        sgie2 = self._create_sgie(
            name="secondary2-nvinference-engine", config_path=sgie2_cfg_path
        )
        sgie3 = self._create_sgie(
            name="secondary3-nvinference-engine", config_path=sgie3_cfg_path
        )
        nvvidconv = self._create_nvvidconv(name="convertor")
        nvosd = self._create_nvosd()
        nvvidconv_postosd = self._create_nvvidconv(name="convertor_postosd")
        caps = self._create_capsfilter(filter_type="I420")
        encoder = self._create_nvv4l2h264enc()
        
        # For RTSP Sink
        if self.sink_type == 0:
            rtppay = self._create_rtppay()
        
        # For MP4 Sink
        if self.sink_type == 1:
            codecparse = self._create_h264parse()
            mux = self._create_mux()
        
        # Output
        sink = self._create_sink(sink_type = self.sink_type)

        # TODO: Revisar si se puede incluir en la funcion de configuracion
        if self.is_live:
            logging.info("At least one of the sources is live")
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
            sgie3,
            queue6,
            tiler,
            queue7,
            nvvidconv,
            queue8,
            nvosd,
            queue9,
            nvvidconv_postosd,
            caps,
            encoder,
        ]

        # RTSP sink
        if self.sink_type == 0:
            temp_list = [rtppay, sink]
        
        # MP4 sink
        elif self.sink_type == 1:
            temp_list = [codecparse, mux, sink]

        plugins = plugins + temp_list

        logging.info("Adding elements to Pipeline \n")
        for plugin in plugins[1:]:
            logging.info(f"Adding plugin: {plugin.name}")
            self.pipeline.add(plugin)

        logging.info("Linking elements in the Pipeline \n")
        for i in range(len(plugins) - 1):
            logging.info(f"Linking {plugins[i].name} --> {plugins[i+1].name}")
            plugins[i].link(plugins[i + 1])

        # TODO: You can add probe callbacks here

        # Example to display classes counter per frame
        # self.set_probe(plugin = pgie, 
        #                pad_type = "src", 
        #                function = probes.tiler_src_pad_buffer_probe, 
        #                plugin_name = "tiler")        
        
        # Probe to display FPS per frame
        self.set_probe(plugin = tiler, 
                       pad_type = "sink", 
                       function = probes.tiler_sink_pad_buffer_probe, 
                       plugin_name = "tiler")


    def run_main_loop(self):

        # create an event loop and feed gstreamer bus mesages to it
        loop = GObject.MainLoop()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, loop)

        # -----------------RTSP-----------------
        # Start streaming
        if self.sink_type == 0:
            codec = self.config_global.get("sink", "codec")
            rtsp_port_num = self.config_global.getint("sink", "rtsp_port_num")
            updsink_port_num = self.config_global.getint(
                "sink", "updsink_port_num"
            )

            server = GstRtspServer.RTSPServer.new()
            server.props.service = "%d" % rtsp_port_num
            server.attach(None)

            factory = GstRtspServer.RTSPMediaFactory.new()
            factory.set_launch(
                '( udpsrc name=pay0 port=%d buffer-size=524288 caps="application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 " )'
                % (updsink_port_num, codec)
            )
            factory.set_shared(True)
            server.get_mount_points().add_factory("/ds-test", factory)

            logging.info(
                "\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/ds-test ***\n\n"
                % rtsp_port_num
            )
        ####################

        # List the sources
        logging.info("Now playing...")
        # TODO: cargar desde el archivo de configuracion
        for i, source in enumerate(self.sources):
            logging.info(f" {i} : {source}")

        logging.info("Starting pipeline \n")
        # start play back and listed to events
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            loop.run()
        except:
            pass
        # cleanup
        logging.info("Exiting app\n")
        self.pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    description = 'Deepstream Main Application set a config file'
    parser = argparse.ArgumentParser(description)
    
    parser.add_argument('--config',
                        default = 'configs/global_config.cfg',
                        type    = str,
                        help    = 'global configuration file',
                        )

    args = parser.parse_args()
    new_pipeline = MainDeepstreamPipeline(path_config_global = args.config )
    new_pipeline.run_main_loop()