
# TODO: aqui van a recidir las variables globales

# vamos a tener un  core.py que llame a este script e inicie las variable globales y una
# instancia de pipeline
# en core vamos añadir tambien la funcion callback de los probes

class Pipeline():

    def __init__(self) -> None:

        self.config_global = configparser.ConfigParser()
        self.config_global.read("configs/global_config.cfg")
        self.config_global.sections()

        # TODO: read a section of uris and set this value
        self.number_sources = 5

        self.fps_streams = {}

        

        self.plugins = []

        self.codec = 5
        self.bitrate = 1

    
    def _create_element(self, factory_name, name, detail=""):
        """Creates an element with Gst Element Factory make.
        Return the element if successfully created, otherwise print to stderr and return None.
        """
        self.logger.info(f"Creating {name}")
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
                logging.exception("DANGER!")
        streammux.set_property("batch-size", self.number_sources)


        return streammux

    def _prepare_multistream(self, streammux):
        
        
        # Creating sources bin
        for i in range(self. number_sources):
            print("\nCreating source_bin {}...".format(i))

            # TODO: leer del archivo de configuracion
            uri_name = args[i + 1]
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
        pgie =  self._create_element("nvinfer", "primary-inference")

        # TODO: set the config file in global file
        pgie.set_property("config-file-path", "configs/tcnet_pgie_config.txt")
        pgie_batch_size = pgie.get_property("batch-size")

        if pgie_batch_size != self.number_sources:
            print(
                "WARNING: Overriding infer-config batch-size",
                pgie_batch_size,
                " with number of sources ",
                self.number_sources,
                " \n",
            )
            pgie.set_property("batch-size", self.number_sources)

        return pgie

    def _create_tiler(self):
        tiler = self._create_element("nvmultistreamtiler", "nvtiler")

        tiler_rows = int(math.sqrt(self.number_sources))
        tiler_columns = int(math.ceil((1.0 * self.number_sources) / tiler_rows))
        tiler.set_property("rows", tiler_rows)
        tiler.set_property("columns", tiler_columns)
        tiler.set_property("width", TILED_OUTPUT_WIDTH)
        tiler.set_property("height", TILED_OUTPUT_HEIGHT)

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

    def _create_sgie(self, number, config_path ):
        sgie = self._create_element("nvinfer", "secondary{}-nvinference-engine".format(number))
        sgie.set_property("config-file-path", config_path)

        return sgie

    def _create_nvvidconv(self, name):
        # Creating nvvidconv
        return self._create_element("nvvideoconvert", name)

    def _create_nvosd(self):
        return self._create_element("nvdsosd", "onscreendisplay")

    def _create_capsfilter(self):
        # Create a capsfilter
        caps = self._create_element("capsfilter", "filter")
        caps.set_property(
            "caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420")
        )
        return caps

    def _create_nvv4l2h264enc(self):
        # Make the encoder
        # TODO: el codec tambien se podria configurar desde el archivo de configuracion global
        if self.codec == "H264":
            encoder = self._create_element("nvv4l2h264enc", "encoder H264")
        elif self.codec == "H265":
            encoder = self._create_element("nvv4l2h265enc", "encoder H265")

        # TODO: este bitrate podria configurarse desde el archivo de configuracion global
        encoder.set_property("bitrate", self.bitrate)
        if is_aarch64():
            encoder.set_property("preset-level", 1)
            encoder.set_property("insert-sps-pps", 1)
            encoder.set_property("bufapi-version", 1)

        return encoder

    def _create_rtppay(self):
        # Make the payload-encode video into RTP packets
        if codec == "H264":
            rtppay = self._create_element("rtph264pay", "rtppay H264")
        elif codec == "H265":
            rtppay = self._create_element("rtph265pay", "rtppay H265")

    def _create_sink(self, type_sink = "udp"):

        # TODO: place a parameter to choose a type sink
        # UDP, Eglsink, Fakesink, MP4

        # Make the UDP sink
        updsink_port_num = 5400
        sink = Gst.ElementFactory.make("udpsink", "udpsink")
        if not sink:
            sys.stderr.write(" Unable to create udpsink")

        sink.set_property("host", "224.224.255.255")
        sink.set_property("port", updsink_port_num)
        sink.set_property("async", False)
        sink.set_property("sync", 1)
        sink.set_property("qos", 0)

        return sink

    def main(self):

        for i in range(self.number_sources):
            self.fps_streams["stream{0}".format(i)] = GETFPS(i)

        # Standard GStreamer initialization
        GObject.threads_init()
        Gst.init(None)

        # Create gstreamer elements */
        # Create Pipeline element that will form a connection of other elements
        # TODO: Check if I can change this pipeline in the init of the whole class
        print("Creating pipeline...\n")
        self.pipeline = Gst.Pipeline()
        self.is_live = False
        
        if not pipeline:
            sys.stderr.write(" Unable to create Pipeline \n")

        # Create nvstreammux instance to form batches from one or more sources.
        print("Creating streamux...")
        streammux = self._create_streammux()

        self.pipeline.add(streammux)
        self._prepare_multistream(streammux)

        queue1 = Gst.ElementFactory.make("queue", "queue1")
        queue2 = Gst.ElementFactory.make("queue", "queue2")
        queue3 = Gst.ElementFactory.make("queue", "queue3")
        queue4 = Gst.ElementFactory.make("queue", "queue4")
        queue5 = Gst.ElementFactory.make("queue", "queue5")
        queue6 = Gst.ElementFactory.make("queue", "queue6")
        queue7 = Gst.ElementFactory.make("queue", "queue7")
        queue8 = Gst.ElementFactory.make("queue", "queue8")

        pgie = self._create_pgie()
        tiler = self._create_tiler()
        tracker = self._create_tracker()
        sgie1 = self._create_sgie(number = 1, config_path="configs/lpdnet_sgie1_config.txt")
        sgie2 = self._create_sgie(number = 1, config_path="configs/lprnet_sgie2_config.txt")
        nvvidconv = self._create_nvvidconv(name = "convertor")

        nvosd = self._create_nvosd()
        nvvidconv_postosd = self._create_nvvidconv(name = "convertor_postosd")
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
            sink
        ]

        print("Adding elements to Pipeline \n")
        for plugin in plugins[1:]:
            self.pipeline.add(plugin)

        print("Linking elements in the Pipeline \n")
        for i in range(len(plugins)-1):
            plugins[i].link(plugins[i+1])

        # create an event loop and feed gstreamer bus mesages to it
        loop = GObject.MainLoop()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", bus_call, loop)

        # HERE: You can add probe callbacks
        tiler_src_pad = pgie.get_static_pad("src")
        if not tiler_src_pad:
            sys.stderr.write(" Unable to get src pad \n")
        else:
            tiler_src_pad.add_probe(
                Gst.PadProbeType.BUFFER, tiler_src_pad_buffer_probe, 0
            )

        # -----------------RTSP-----------------
        # Start streaming
        rtsp_port_num = 8554

        server = GstRtspServer.RTSPServer.new()
        server.props.service = "%d" % rtsp_port_num
        server.attach(None)

        factory = GstRtspServer.RTSPMediaFactory.new()
        # factory_msg = (("""( udpsrc name=pay0 port=%d buffer-size=524288 
        # caps="application/x-rtp, media=video, clock-rate=90000,
        # encoding-name=(string)%s, payload=96 " )""" % (updsink_port_num, codec)))
        factory.set_launch(
            '( udpsrc name=pay0 port=%d buffer-size=524288 caps="application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 " )'
            % (updsink_port_num, codec)
        )
        factory.set_launch(factory_msg)
        factory.set_shared(True)
        server.get_mount_points().add_factory("/ds-test", factory)

        # print_msg = ("""\n *** DeepStream: Launched RTSP Streaming at
        # rtsp://localhost:%d/ds-test ***\n\n""" % rtsp_port_num)

        # print(print_msg)

        print(
            "\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/ds-test ***\n\n"
            % rtsp_port_num
        )
        ####################

        # List the sources
        print("Now playing...")
        # TODO: cargar desde el archivo de configuracion
        for i, source in enumerate(args):
            if i != 0:
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
