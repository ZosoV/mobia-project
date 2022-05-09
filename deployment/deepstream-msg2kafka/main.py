import globals as G
import argparse

import sys

sys.path.append('../')
import gi

gi.require_version('Gst', '1.0')
from gi.repository import GObject, Gst

from optparse import OptionParser
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.utils import long_to_uint64
from common.FPS import GETFPS
import pyds

# Additional imports
import probes
import coloredlogs, logging
# you can use %(asctime)s if you need
coloredlogs.install(fmt= '[%(levelname)s] | (%(filename)s:%(levelno)s) | %(message)s',level='DEBUG')

from common.pipeline import Pipeline

class Msg2KafkaDeepstreamPipeline(Pipeline):
    def __init__(self,  *args, **kw):
        super().__init__(*args, **kw)

        # Get the sink type
        # Types-> RTSP: 0, MP4: 1, FakeSink: 2
        self.sink_type = self.config_global.getint("sink", "type")
        if self.sink_type != 2:
            logging.error(f"This app only accepts Fake sink. Check {kw['path_config_global']} \n" )
            sys.exit(1)

        self.create_pipeline()

    def create_pipeline(self):

        # Init Global Variables per source
        # FPS_STREAMS: Keep track of the frames per second
        for i in range(self.number_sources):
            G.FPS_STREAMS["stream{0}".format(i)] = GETFPS(i)

        # Standard GStreamer initialization
        GObject.threads_init()
        Gst.init(None)

        # registering callbacks
        pyds.register_user_copyfunc(probes.meta_copy_func)
        pyds.register_user_releasefunc(probes.meta_free_func)

        # Create gstreamer elements */
        # Create Pipeline element that will form a connection of other elements
        logging.info("Creating pipeline...")
        self.pipeline = Gst.Pipeline()
        self.is_live = False

        if not self.pipeline:
            logging.error(" Unable to create Pipeline")

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

        # Getting configs paths of the models
        pgie_cfg_path = self.config_global.get("models", "pgie_config")
        # sgie1_cfg_path = self.config_global.get("models", "sgie1_config")
        # sgie2_cfg_path = self.config_global.get("models", "sgie2_config")
        # tracker_cfg_path = self.config_global.get("models", "tracker_config")

        # Create main plugins
        logging.info("Creating main plugins")
        pgie = self._create_pgie(config_path=pgie_cfg_path)

        tiler = self._create_tiler()
        # tracker = self._create_tracker(config_path=tracker_cfg_path)
        # sgie1 = self._create_sgie(name="secondary1-nvinference-engine", 
        #                         config_path=sgie1_cfg_path)
        # sgie2 = self._create_sgie(name="secondary2-nvinference-engine",
        #                         config_path=sgie2_cfg_path)
        nvvidconv = self._create_nvvidconv(name="convertor")
        nvosd = self._create_nvosd()
        tee = self._create_tee()

        # Create two additional quees for divide stream with tee
        queue_tee1 = self._create_element("queue", "nvtee-que1")
        queue_tee2 = self._create_element("queue", "nvtee-que2")

        # Create the msgconv and msgbroker to send msg to Kafka
        msgconv = self._create_msgconv()
        msgbroker = self._create_msgbroker()


        # nvvidconv_postosd = self._create_nvvidconv(name="convertor_postosd")
        # caps = self._create_capsfilter(filter_type="I420")
        # encoder = self._create_nvv4l2h264enc()
        
        # # For RTSP Sink
        # if self.sink_type == 0:
        #     rtppay = self._create_rtppay()
        
        # # For MP4 Sink
        # if self.sink_type == 1:
        #     codecparse = self._create_h264parse()
        #     mux = self._create_mux()
        
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
            # tracker,
            # queue3,
            # sgie1,
            # queue4,
            # sgie2,
            # queue5,
            tiler,
            queue6,
            nvvidconv,
            queue7,
            nvosd,
            queue8,
            tee,
            queue_tee1,
            queue_tee2,
            msgconv,
            msgbroker,
            sink
            # nvvidconv_postosd,
            # caps,
            # encoder,
        ]

        # RTSP sink
        # if self.sink_type == 0:
        #     temp_list = [rtppay, sink]
        
        # # MP4 sink
        # elif self.sink_type == 1:
        #     temp_list = [codecparse, mux, sink]

        # plugins = plugins + temp_list

        logging.info("Adding elements to Pipeline")
        for plugin in plugins[1:]:
            logging.info(f"Adding plugin: {plugin.name}")
            self.pipeline.add(plugin)

        # Note: only link until tee, so we use - 6
        logging.info("Linking elements in the Pipeline")
        for i in range(len(plugins) - 6):
            logging.info(f"Linking {plugins[i].name} --> {plugins[i+1].name}")
            plugins[i].link(plugins[i + 1])

        # Linking the msg branch
        queue_tee1.link(msgconv)
        msgconv.link(msgbroker)

        # Linking the render branch
        queue_tee2.link(sink)

        # Linking both branches to the tee
        tee_msg_pad = tee.get_request_pad("src_%u")
        tee_render_pad = tee.get_request_pad("src_%u")
        if not tee_msg_pad or not tee_render_pad:
            logging.error("Unable to get request pads")
        sink_pad = queue_tee1.get_static_pad("sink")
        tee_msg_pad.link(sink_pad)
        sink_pad = queue_tee2.get_static_pad("sink")
        tee_render_pad.link(sink_pad)

        # TODO: You can add probe callbacks here

        # Example to display classes counter per frame
        # self.set_probe(plugin = pgie, 
        #                pad_type = "src", 
        #                function = probes.tiler_src_pad_buffer_probe, 
        #                plugin_name = "tiler")        
        
        # Probe to display FPS per frame
        
        # Loading specific attributes for this probe
        # nvmsgconv_attribs = dict(self.config_global["nvmsgconv"])
        # self.set_probe(plugin = tiler, 
        #                pad_type = "sink", 
        #                function = probes.osd_sink_pad_buffer_probe(nvmsgconv_attribs), 
        #                plugin_name = "tiler")

    def run_main_loop(self):

        # create an event loop and feed gstreamer bus mesages to it
        loop = GObject.MainLoop()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, loop)

        # -----------------RTSP-----------------
        # Start streaming
        # if self.sink_type == 0:
        #     codec = self.config_global.get("sink", "codec")
        #     rtsp_port_num = self.config_global.getint("sink", "rtsp_port_num")
        #     updsink_port_num = self.config_global.getint(
        #         "sink", "updsink_port_num"
        #     )

        #     server = GstRtspServer.RTSPServer.new()
        #     server.props.service = "%d" % rtsp_port_num
        #     server.attach(None)

        #     factory = GstRtspServer.RTSPMediaFactory.new()
        #     factory.set_launch(
        #         '( udpsrc name=pay0 port=%d buffer-size=524288 caps="application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 " )'
        #         % (updsink_port_num, codec)
        #     )
        #     factory.set_shared(True)
        #     server.get_mount_points().add_factory("/ds-test", factory)

        #     logging.info(
        #         "\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/ds-test ***\n\n"
        #         % rtsp_port_num
        #     )
        ####################

        # List the sources
        logging.info("Now playing...")
        # TODO: cargar desde el archivo de configuracion
        for i, source in enumerate(self.sources):
            logging.info( f"{i}, :  {source}")

        logging.info("Starting pipeline \n")
        # start play back and listed to events
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            loop.run()
        except:
            pass
        # cleanup
        logging.info("Exiting app\n")
        pyds.unset_callback_funcs()
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
    new_pipeline = Msg2KafkaDeepstreamPipeline(path_config_global = args.config)
    new_pipeline.run_main_loop()