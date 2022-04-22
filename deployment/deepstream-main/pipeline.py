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

import pyds

# Additional imports
import multistream
import probes

# TODO: aqui van a recidir las variables globales

# vamos a tener un  core.py que llame a este script e inicie las variable globales y una
# instancia de pipeline
# en core vamos añadir tambien la funcion callback de los probes


class Pipeline:
    def __init__(self, path_config_global = "configs/global_config.cfg") -> None:

        self.logger = logging.getLogger(__name__ + "." + self.__class__.__name__)

        self.config_global = configparser.ConfigParser()
        self.config_global.read(path_config_global)
        self.config_global.sections()

        self.general_batch_size = self.config_global.getint("streammux", "batch-size")
        
        self.sources = [ val for _, val in self.config_global.items("sources")]
        self.number_sources = len(self.sources)

        self.codec = self.config_global.get("protocols",'codec')
        self.bitrate = self.config_global.getint("protocols","bitrate")

        # Sink
        self.updsink_port_num = self.config_global.getint("sink","updsink_port_num")


        self.create_pipeline()

    def _create_element(self, factory_name, name, detail=""):
        """Creates an element with Gst Element Factory make.
        Return the element if successfully created, otherwise print to stderr
        and return None.
        """
        print(f"Creating {name}")
        elm = Gst.ElementFactory.make(factory_name, name)

        if not elm:
            self.logger.error(f"Unable to create {name}")
            if detail:
                self.logger.error(detail)

        return elm

    def _create_streammux(self):
        streammux = self._create_element("nvstreammux", "stream-muxer")

        streammux_properties = [
            "width",
            "height",
            "batched-push-timeout",
            "batch-size",
        ]
        for key, value in self.config_global.items("streammux"):
            if key in streammux_properties:
                streammux.set_property(key, int(value))
            else:
                logging.exception(f"Key {key} is not a property of streammux. Check config file")

        return streammux

    def _prepare_multistream(self, streammux):

        # Creating sources bin
        for i in range(self.number_sources):
            print("\nCreating source_bin {}...".format(i))

            # TODO: leer del archivo de configuracion
            uri_name = self.sources[i]
            if uri_name.find("rtsp://") == 0:
                is_live = True
            source_bin = multistream.create_source_bin(i, uri_name)
            if not source_bin:
                sys.stderr.write("Unable to create source bin \n")
            self.pipeline.add(source_bin)
            padname = "sink_%u" % i
            sinkpad = streammux.get_request_pad(padname)
            if not sinkpad:
                sys.stderr.write("Unable to create sink pad bin \n")
            srcpad = source_bin.get_static_pad("src")
            if not srcpad:
                sys.stderr.write("Unable to create src pad bin \n")
            srcpad.link(sinkpad)

    def _create_pgie(self):

        # Creating pgie
        pgie = self._create_element("nvinfer", "primary-inference")

        # TODO: set the config file in global file
        config_path = self.config_global.get("models","pgie_config")
        pgie.set_property("config-file-path", config_path)
        pgie_batch_size = pgie.get_property("batch-size")

        if pgie_batch_size != self.general_batch_size :
            print(
                "WARNING: Overriding infer-config batch-size",
                pgie_batch_size,
                " with number of sources ",
                self.general_batch_size,
                " \n",
            )
            pgie.set_property("batch-size", self.general_batch_size)

        return pgie

    def _create_tiler(self):

        tiler = self._create_element("nvmultistreamtiler", "nvtiler")

        tiler_rows = int(math.sqrt(self.number_sources))
        tiler_columns = int(
            math.ceil((1.0 * self.number_sources) / tiler_rows)
        )
        tiler.set_property("rows", tiler_rows)
        tiler.set_property("columns", tiler_columns)

        # TODO: hacer una funcion para contralar las excepciones
        # al llamar config_globalss
        width = self.config_global.getint("tiler", "width")
        height = self.config_global.getint("tiler", "height")

        tiler.set_property("width", width)
        tiler.set_property("height", height)

        return tiler

    def _create_tracker(self):
        tracker = self._create_element("nvtracker", "tracker")

        # Set properties of tracker
        config = configparser.ConfigParser()
        config.read("configs/general_tracker_config.txt")
        config.sections()

        for key, value in config.items("tracker"):
            if key == "tracker-width":
                tracker_width = config.getint("tracker", key)
                tracker.set_property("tracker-width", tracker_width)
            elif key == "tracker-height":
                tracker_height = config.getint("tracker", key)
                tracker.set_property("tracker-height", tracker_height)
            elif key == "gpu-id":
                tracker_gpu_id = config.getint("tracker", key)
                tracker.set_property("gpu_id", tracker_gpu_id)
            elif key == "ll-lib-file":
                tracker_ll_lib_file = config.get("tracker", key)
                tracker.set_property("ll-lib-file", tracker_ll_lib_file)
            elif key == "ll-config-file":
                tracker_ll_config_file = config.get("tracker", key)
                tracker.set_property("ll-config-file", tracker_ll_config_file)
            elif key == "enable-batch-process":
                tracker_enable_batch_process = config.getint("tracker", key)
                tracker.set_property(
                    "enable_batch_process", tracker_enable_batch_process
                )
            elif key == "enable-past-frame":
                tracker_enable_past_frame = config.getint("tracker", key)
                tracker.set_property(
                    "enable_past_frame", tracker_enable_past_frame
                )

        return tracker

    def _create_sgie(self, config):
        sgie = self._create_element(
            "nvinfer", "secondary{}-nvinference-engine".format(G.SGIE_INITIAL)
        )
        sgie.set_property("config-file-path", config)
        G.SGIE_INITIAL +=1

        return sgie
        
    # TODO: Aqui nos quedamos

    def _create_nvvidconv(self, name):
        # Creating nvvidconv
        return self._create_element("nvvideoconvert", name)

    def _create_nvosd(self):
        return self._create_element("nvdsosd", "onscreendisplay")

    def _create_capsfilter(self):
        # Create a capsfilter
        caps = self._create_element("capsfilter", "filter")
        caps.set_property(
            "caps",
            Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"),
        )
        return caps

    def _create_nvv4l2h264enc(self):
        # Make the encoder
        # TODO: el codec tambien se podria configurar desde el archivo de
        # configuracion global
        if self.codec == "H264":
            encoder = self._create_element("nvv4l2h264enc", "encoder H264")
        elif self.codec == "H265":
            encoder = self._create_element("nvv4l2h265enc", "encoder H265")

        # TODO: este bitrate podria configurarse desde el archivo de
        # configuracion global
        encoder.set_property("bitrate", self.bitrate)
        if is_aarch64():
            encoder.set_property("preset-level", 1)
            encoder.set_property("insert-sps-pps", 1)
            encoder.set_property("bufapi-version", 1)

        return encoder

    def _create_rtppay(self):
        # Make the payload-encode video into RTP packets
        if self.codec == "H264":
            rtppay = self._create_element("rtph264pay", "rtppay H264")
        elif self.codec == "H265":
            rtppay = self._create_element("rtph265pay", "rtppay H265")

        return rtppay

    def _create_sink(self, type_sink="udp"):

        # TODO: place a parameter to choose a type sink
        # UDP, Eglsink, Fakesink, MP4

        # Make the UDP sink
        self.updsink_port_num = 5400
        sink = self._create_element("udpsink", "udpsink")
        if not sink:
            sys.stderr.write(" Unable to create udpsink")

        sink.set_property("host", "224.224.255.255")
        sink.set_property("port", self.updsink_port_num)
        sink.set_property("async", False)
        sink.set_property("sync", 1)
        sink.set_property("qos", 0)

        return sink

    def create_pipeline(self):

        for i in range(self.number_sources):
            G.FPS_STREAMS["stream{0}".format(i)] = GETFPS(i)

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

        # Getting configs paths
        sgie1_cfg_path = self.config_global.get("models","sgie1_config")
        sgie2_cfg_path = self.config_global.get("models","sgie2_config")
        
        # Create main plugins
        print("\nCreating main plugins")
        pgie = self._create_pgie()
        tiler = self._create_tiler()
        tracker = self._create_tracker()
        sgie1 = self._create_sgie(config=sgie1_cfg_path)
        sgie2 = self._create_sgie(config=sgie2_cfg_path)
        nvvidconv = self._create_nvvidconv(name="convertor")
        nvosd = self._create_nvosd()
        nvvidconv_postosd = self._create_nvvidconv(name="convertor_postosd")
        caps = self._create_capsfilter()
        encoder = self._create_nvv4l2h264enc()
        rtppay = self._create_rtppay()
        sink = self._create_sink()

        # TODO: Revisar si se lo puede incluir dentro de la funcion de configuracin
        if self.is_live:
            print("Atleast one of the sources is live")
            streammux.set_property("live-source", 1)

        # This define the order for linking the pluggins
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
            tiler,
            queue6,
            nvvidconv,
            queue7,
            nvosd,
            queue8,
            nvvidconv_postosd,
            caps,
            encoder,
            rtppay,
            sink,
        ]

        print("Adding elements to Pipeline \n")
        for plugin in plugins[1:]:
            self.pipeline.add(plugin)

        print("Linking elements in the Pipeline \n")
        for i in range(len(plugins) - 1):
            plugins[i].link(plugins[i + 1])

        # TODO: You can add probe callbacks
        tiler_src_pad = pgie.get_static_pad("src")
        if not tiler_src_pad:
            sys.stderr.write(" Unable to get src pad \n")
        else:
            tiler_src_pad.add_probe(
                Gst.PadProbeType.BUFFER, probes.tiler_src_pad_buffer_probe, 0
            )


    def run_main_loop(self):

        # create an event loop and feed gstreamer bus mesages to it
        loop = GObject.MainLoop()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, loop)

        # -----------------RTSP-----------------
        # Start streaming
        rtsp_port_num = 8554

        server = GstRtspServer.RTSPServer.new()
        server.props.service = "%d" % rtsp_port_num
        server.attach(None)

        factory = GstRtspServer.RTSPMediaFactory.new()
        factory.set_launch(
            '( udpsrc name=pay0 port=%d buffer-size=524288 caps="application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 " )'
            % (self.updsink_port_num, self.codec)
        )
        factory.set_shared(True)
        server.get_mount_points().add_factory("/ds-test", factory)

        print(
            "\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/ds-test ***\n\n"
            % rtsp_port_num
        )
        ####################

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
