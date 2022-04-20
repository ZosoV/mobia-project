#!/usr/bin/env python3

import sys

sys.path.append('../')
import gi
import configparser

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')

from gi.repository import GObject, Gst, GstRtspServer
from gi.repository import GLib
from ctypes import *
import time
import sys
import math
import platform
from common.is_aarch_64 import is_aarch64
from common.bus_call import bus_call
from common.FPS import GETFPS
import numpy as np
import pyds
import cv2
import os
import os.path
from os import path

fps_streams = {}
frame_count = {}
saved_count = {}
global PGIE_CLASS_ID_VEHICLE
PGIE_CLASS_ID_VEHICLE = 0
global PGIE_CLASS_ID_PERSON
PGIE_CLASS_ID_PERSON = 2

MAX_DISPLAY_LEN = 64
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3
MUXER_OUTPUT_WIDTH = 1920
MUXER_OUTPUT_HEIGHT = 1080
MUXER_BATCH_TIMEOUT_USEC = 4000000
TILED_OUTPUT_WIDTH = 1920
TILED_OUTPUT_HEIGHT = 1080
GST_CAPS_FEATURES_NVMM = "memory:NVMM"
pgie_classes_str = ["Vehicle", "TwoWheeler", "Person", "RoadSign"]

MIN_CONFIDENCE = 0.3
MAX_CONFIDENCE = 0.4


# tiler_sink_pad_buffer_probe  will extract metadata received on tiler src pad
# and update params for drawing rectangle, object information etc.
# pad – the GstPad that is blocked
# info – GstPadProbeInfo
# user_data – the gpointer to optional user data.
def tiler_sink_pad_buffer_probe(pad, info, u_data):
    frame_number = 0
    num_rects = 0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        print("Unable to get GstBuffer ")
        return

    # Retrieve batch metadata from the gst_buffer
    # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
    # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))

    l_frame = batch_meta.frame_meta_list
    while l_frame is not None:
        try:
            # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
            # The casting is done by pyds.NvDsFrameMeta.cast()
            # The casting also keeps ownership of the underlying memory
            # in the C code, so the Python garbage collector will leave
            # it alone.
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break

        frame_number = frame_meta.frame_num
        l_obj = frame_meta.obj_meta_list
        num_rects = frame_meta.num_obj_meta
        is_first_obj = True
        save_image = False
        obj_counter = {
            PGIE_CLASS_ID_VEHICLE: 0,
            PGIE_CLASS_ID_PERSON: 0,
            PGIE_CLASS_ID_BICYCLE: 0,
            PGIE_CLASS_ID_ROADSIGN: 0
        }

        kittie_lines_per_frame = []

        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            obj_counter[obj_meta.class_id] += 1
            # Periodically check for objects with borderline confidence value that may be false positive detections.
            # If such detections are found, annotate the frame with bboxes and confidence value.
            # Save the annotated frame to file.
            if saved_count["stream_{}".format(frame_meta.pad_index)] % 30 == 0 and (
                    MIN_CONFIDENCE < obj_meta.confidence < MAX_CONFIDENCE):
                if is_first_obj:
                    is_first_obj = False
                    # Getting Image data using nvbufsurface
                    # the input should be address of buffer and batch_id
                    n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
                    n_frame = draw_bounding_boxes(n_frame, obj_meta, obj_meta.confidence)
                    # convert python array into numpy array format in the copy mode.
                    frame_copy = np.array(n_frame, copy=True, order='C')
                    # convert the array into cv2 default color format
                    frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_RGBA2BGRA)

                kitti_line  = "{} 0.00 0 0.00 {} {} {} {} 0.00 0.00 0.00 0.00 0.00 0.00 0.00"
                kitti_line.format(label, xmin, ymin, xmax, ymax)
                kittie_lines_per_frame.append(kitti_line)

                save_image = True

            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        print("Frame Number=", frame_number, "Number of Objects=", num_rects, "Vehicle_count=",
              obj_counter[PGIE_CLASS_ID_VEHICLE], "Person_count=", obj_counter[PGIE_CLASS_ID_PERSON])
        # Get frame rate through this probe
        fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()
        if save_image:
            
            # Saving Image
            img_path = "{}/stream_{}/frame_{}.jpg".format(folder_name, frame_meta.pad_index, frame_number)
            cv2.imwrite(img_path, frame_copy)

            # Saving Label Annotation
            annotation_path = "{}/stream_{}/frame_{}.txt".format(folder_name, frame_meta.pad_index, frame_number)

            
        saved_count["stream_{}".format(frame_meta.pad_index)] += 1
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK

def saving_annotation(obj_meta, annotation_path):
    pass

def draw_bounding_boxes(image, obj_meta, confidence):
    confidence = '{0:.2f}'.format(confidence)
    rect_params = obj_meta.rect_params
    top = int(rect_params.top)
    left = int(rect_params.left)
    width = int(rect_params.width)
    height = int(rect_params.height)
    obj_name = pgie_classes_str[obj_meta.class_id]
    # image = cv2.rectangle(image, (left, top), (left + width, top + height), (0, 0, 255, 0), 2, cv2.LINE_4)
    color = (0, 0, 255, 0)
    w_percents = int(width * 0.05) if width > 100 else int(width * 0.1)
    h_percents = int(height * 0.05) if height > 100 else int(height * 0.1)
    linetop_c1 = (left + w_percents, top)
    linetop_c2 = (left + width - w_percents, top)
    image = cv2.line(image, linetop_c1, linetop_c2, color, 6)
    linebot_c1 = (left + w_percents, top + height)
    linebot_c2 = (left + width - w_percents, top + height)
    image = cv2.line(image, linebot_c1, linebot_c2, color, 6)
    lineleft_c1 = (left, top + h_percents)
    lineleft_c2 = (left, top + height - h_percents)
    image = cv2.line(image, lineleft_c1, lineleft_c2, color, 6)
    lineright_c1 = (left + width, top + h_percents)
    lineright_c2 = (left + width, top + height - h_percents)
    image = cv2.line(image, lineright_c1, lineright_c2, color, 6)
    # Note that on some systems cv2.putText erroneously draws horizontal lines across the image
    image = cv2.putText(image, obj_name + ',C=' + str(confidence), (left - 10, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 0, 255, 0), 2)
    return image


def cb_newpad(decodebin, decoder_src_pad, data):
    print("In cb_newpad\n")
    caps = decoder_src_pad.get_current_caps()
    gststruct = caps.get_structure(0)
    gstname = gststruct.get_name()
    source_bin = data
    features = caps.get_features(0)

    # Need to check if the pad created by the decodebin is for video and not
    # audio.
    if (gstname.find("video") != -1):
        # Link the decodebin pad only if decodebin has picked nvidia
        # decoder plugin nvdec_*. We do this by checking if the pad caps contain
        # NVMM memory features.
        if features.contains("memory:NVMM"):
            # Get the source bin ghost pad
            bin_ghost_pad = source_bin.get_static_pad("src")
            if not bin_ghost_pad.set_target(decoder_src_pad):
                sys.stderr.write("Failed to link decoder src pad to source bin ghost pad\n")
        else:
            sys.stderr.write(" Error: Decodebin did not pick nvidia decoder plugin.\n")


def decodebin_child_added(child_proxy, Object, name, user_data):
    print("Decodebin child added:", name, "\n")
    if name.find("decodebin") != -1:
        Object.connect("child-added", decodebin_child_added, user_data)

    # TODO: Revisar que hace este paso
    # if "source" in name:
    #     Object.set_property("drop-on-latency", True)

def create_source_bin(index, uri):
    print("Creating source bin")

    # Create a source GstBin to abstract this bin's content from the rest of the
    # pipeline
    bin_name = "source-bin-%02d" % index
    print(bin_name)
    nbin = Gst.Bin.new(bin_name)
    if not nbin:
        sys.stderr.write(" Unable to create source bin \n")

    # Source element for reading from the uri.
    # We will use decodebin and let it figure out the container format of the
    # stream and the codec and plug the appropriate demux and decode plugins.
    uri_decode_bin = Gst.ElementFactory.make("uridecodebin", "uri-decode-bin")
    if not uri_decode_bin:
        sys.stderr.write(" Unable to create uri decode bin \n")
    # We set the input uri to the source element
    uri_decode_bin.set_property("uri", uri)
    # Connect to the "pad-added" signal of the decodebin which generates a
    # callback once a new pad for raw data has beed created by the decodebin
    uri_decode_bin.connect("pad-added", cb_newpad, nbin)
    uri_decode_bin.connect("child-added", decodebin_child_added, nbin)

    # We need to create a ghost pad for the source bin which will act as a proxy
    # for the video decoder src pad. The ghost pad will not have a target right
    # now. Once the decode bin creates the video decoder and generates the
    # cb_newpad callback, we will set the ghost pad target to the video decoder
    # src pad.
    Gst.Bin.add(nbin, uri_decode_bin)
    bin_pad = nbin.add_pad(Gst.GhostPad.new_no_target("src", Gst.PadDirection.SRC))
    if not bin_pad:
        sys.stderr.write(" Failed to add ghost pad in source bin \n")
        return None
    return nbin


def main(args):
    # Check input arguments
    if len(args) < 2:
        sys.stderr.write("usage: %s <uri1> [uri2] ... [uriN] <folder to save frames>\n" % args[0])
        sys.exit(1)

    for i in range(0, len(args) - 2):
        fps_streams["stream{0}".format(i)] = GETFPS(i)
    number_sources = len(args) - 2

    global folder_name
    folder_name = args[-1]
    if path.exists(folder_name):
        sys.stderr.write("The output folder %s already exists. Please remove it first.\n" % folder_name)
        sys.exit(1)

    os.mkdir(folder_name)
    print("Frames will be saved in ", folder_name)
    # Standard GStreamer initialization
    GObject.threads_init()
    Gst.init(None)

    # Create gstreamer elements */
    # Create Pipeline element that will form a connection of other elements
    print("Creating Pipeline \n ")
    pipeline = Gst.Pipeline()
    is_live = False

    if not pipeline:
        sys.stderr.write(" Unable to create Pipeline \n")
    print("Creating streamux \n ")

    # Create nvstreammux instance to form batches from one or more sources.
    streammux = Gst.ElementFactory.make("nvstreammux", "Stream-muxer")
    if not streammux:
        sys.stderr.write(" Unable to create NvStreamMux \n")

    pipeline.add(streammux)
    for i in range(number_sources):
        os.mkdir(folder_name + "/stream_" + str(i))
        frame_count["stream_" + str(i)] = 0
        saved_count["stream_" + str(i)] = 0
        print("Creating source_bin ", i, " \n ")
        uri_name = args[i + 1]
        if uri_name.find("rtsp://") == 0:
            is_live = True
        source_bin = create_source_bin(i, uri_name)
        if not source_bin:
            sys.stderr.write("Unable to create source bin \n")
        pipeline.add(source_bin)
        padname = "sink_%u" % i
        sinkpad = streammux.get_request_pad(padname)
        if not sinkpad:
            sys.stderr.write("Unable to create sink pad bin \n")
        srcpad = source_bin.get_static_pad("src")
        if not srcpad:
            sys.stderr.write("Unable to create src pad bin \n")
        srcpad.link(sinkpad)
    print("Creating Pgie \n ")
    pgie = Gst.ElementFactory.make("nvinfer", "primary-inference")
    if not pgie:
        sys.stderr.write(" Unable to create pgie \n")
    # Add nvvidconv1 and filter1 to convert the frames to RGBA
    # which is easier to work with in Python.
    print("Creating nvvidconv1 \n ")
    nvvidconv1 = Gst.ElementFactory.make("nvvideoconvert", "convertor1")
    if not nvvidconv1:
        sys.stderr.write(" Unable to create nvvidconv1 \n")
    print("Creating filter1 \n ")
    caps1 = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=RGBA")
    filter1 = Gst.ElementFactory.make("capsfilter", "filter1")
    if not filter1:
        sys.stderr.write(" Unable to get the caps filter1 \n")
    filter1.set_property("caps", caps1)
    print("Creating tiler \n ")
    tiler = Gst.ElementFactory.make("nvmultistreamtiler", "nvtiler")
    if not tiler:
        sys.stderr.write(" Unable to create tiler \n")
    print("Creating nvvidconv \n ")
    nvvidconv = Gst.ElementFactory.make("nvvideoconvert", "convertor")
    if not nvvidconv:
        sys.stderr.write(" Unable to create nvvidconv \n")
    print("Creating nvosd \n ")
    nvosd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    if not nvosd:
        sys.stderr.write(" Unable to create nvosd \n")


    # FOR RSTP and mp4
    # nvvidconv_postosd = Gst.ElementFactory.make("nvvideoconvert", "convertor_postosd")
    # if not nvvidconv_postosd:
    #     sys.stderr.write(" Unable to create nvvidconv_postosd \n")

    # # Create a caps filter
    # caps_postosd = Gst.ElementFactory.make("capsfilter", "filter")
    # caps_postosd.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))

    # # Make the encoder
    # if codec == "H264":
    #     encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
    #     print("Creating H264 Encoder")
    # elif codec == "H265":
    #     encoder = Gst.ElementFactory.make("nvv4l2h265enc", "encoder")
    #     print("Creating H265 Encoder")
    # if not encoder:
    #     sys.stderr.write(" Unable to create encoder")
    # encoder.set_property('bitrate', bitrate)
    # if is_aarch64():
    #     encoder.set_property('preset-level', 1)
    #     encoder.set_property('insert-sps-pps', 1)
    #     encoder.set_property('bufapi-version', 1)
    
    # Make the payload-encode video into RTP packets
    # if codec == "H264":
    #     rtppay = Gst.ElementFactory.make("rtph264pay", "rtppay")
    #     print("Creating H264 rtppay")
    # elif codec == "H265":
    #     rtppay = Gst.ElementFactory.make("rtph265pay", "rtppay")
    #     print("Creating H265 rtppay")
    # if not rtppay:
    #     sys.stderr.write(" Unable to create rtppay")
    
    # # Make the UDP sink
    # updsink_port_num = 5400
    # sink = Gst.ElementFactory.make("udpsink", "udpsink")
    # if not sink:
    #     sys.stderr.write(" Unable to create udpsink")
    
    # sink.set_property('host', '224.224.255.255')
    # sink.set_property('port', updsink_port_num)
    # sink.set_property('async', False)
    # sink.set_property('sync', 1)


    # Eglsink and fakesink

    # if (is_aarch64()):
    #     print("Creating transform \n ")
    #     transform = Gst.ElementFactory.make("nvegltransform", "nvegl-transform")
    #     if not transform:
    #         sys.stderr.write(" Unable to create transform \n")

    print("Creating FakeSink \n")
    sink = Gst.ElementFactory.make("fakesink", "fakesink")
    if not sink:
        sys.stderr.write(" Unable to create fake sink \n")
    

    # print("Creating EGLSink \n")
    # sink = Gst.ElementFactory.make("nveglglessink", "nvvideo-renderer")
    # if not sink:
    #     sys.stderr.write(" Unable to create egl sink \n")

    codecparse = Gst.ElementFactory.make("h264parse", "h264_parse")
    if not codecparse:
        sys.stderr.write(" Unable to create codecparse \n")
        
    mux = Gst.ElementFactory.make("mp4mux", "mux")
    if not mux:
        sys.stderr.write(" Unable to create mux \n")

    sink = Gst.ElementFactory.make("filesink", "filesink")
    if not sink:
        sys.stderr.write(" Unable to create filesink \n")
    sink.set_property('location', output_path)

    sink.set_property("sync", 0)
    sink.set_property("qos", 0)

    if is_live:
        print("Atleast one of the sources is live")
        streammux.set_property('live-source', 1)

    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', number_sources)
    streammux.set_property('batched-push-timeout', 4000000)
    pgie.set_property('config-file-path', "dstest_imagedata_config.txt")
    pgie_batch_size = pgie.get_property("batch-size")
    if (pgie_batch_size != number_sources):
        print("WARNING: Overriding infer-config batch-size", pgie_batch_size, " with number of sources ",
              number_sources, " \n")
        pgie.set_property("batch-size", number_sources)
    tiler_rows = int(math.sqrt(number_sources))
    tiler_columns = int(math.ceil((1.0 * number_sources) / tiler_rows))
    tiler.set_property("rows", tiler_rows)
    tiler.set_property("columns", tiler_columns)
    tiler.set_property("width", TILED_OUTPUT_WIDTH)
    tiler.set_property("height", TILED_OUTPUT_HEIGHT)



    if not is_aarch64():
        # Use CUDA unified memory in the pipeline so frames
        # can be easily accessed on CPU in Python.
        mem_type = int(pyds.NVBUF_MEM_CUDA_UNIFIED)
        streammux.set_property("nvbuf-memory-type", mem_type)
        nvvidconv.set_property("nvbuf-memory-type", mem_type)
        nvvidconv1.set_property("nvbuf-memory-type", mem_type)
        tiler.set_property("nvbuf-memory-type", mem_type)

    print("Adding elements to Pipeline \n")
    pipeline.add(pgie)
    pipeline.add(tiler)
    pipeline.add(nvvidconv)
    pipeline.add(filter1)
    pipeline.add(nvvidconv1)
    pipeline.add(nvosd)
    # if is_aarch64():
    #     pipeline.add(transform)
    # pipeline.add(sink)
    # pipeline.add(nvvidconv_postosd)
    # pipeline.add(caps_postosd)
    # pipeline.add(encoder)
    # pipeline.add(rtppay)
    # pipeline.add(codecparse)
    # pipeline.add(mux)
    pipeline.add(sink)

    print("Linking elements in the Pipeline \n")

    # TODO: check what is doing a caps
    # Here filter1 is a caps, but here it is used before nvosd
    # why?
    streammux.link(pgie)
    pgie.link(nvvidconv1)
    nvvidconv1.link(filter1)
    filter1.link(tiler)

    # Aqui viene el probe

    tiler.link(nvvidconv)
    nvvidconv.link(nvosd)
    # if is_aarch64():
    #     nvosd.link(transform)
    #     transform.link(sink)
    # else:
        # nvosd.link(sink)
    nvosd.link(sink)

    # nvosd.link(nvvidconv_postosd)
    # nvvidconv_postosd.link(caps_postosd)
    # caps_postosd.link(encoder)
    # encoder.link(rtppay)
    # rtppay.link(sink)
    # encoder.link(codecparse)
    # codecparse.link(mux)
    # mux.link(sink)

    # create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)

    # Start streaming
    # rtsp_port_num = 8554
    
    # server = GstRtspServer.RTSPServer.new()
    # server.props.service = "%d" % rtsp_port_num
    # server.attach(None)
    
    # factory = GstRtspServer.RTSPMediaFactory.new()
    # factory.set_launch( "( udpsrc name=pay0 port=%d buffer-size=524288 caps=\"application/x-rtp, media=video, clock-rate=90000, encoding-name=(string)%s, payload=96 \" )" % (updsink_port_num, codec))
    # factory.set_shared(True)
    # server.get_mount_points().add_factory("/ds-test", factory)

    # print("\n *** DeepStream: Launched RTSP Streaming at rtsp://localhost:%d/ds-test ***\n\n" % rtsp_port_num)

    
    # Lets add probe to get informed of the meta data generated, we add probe to
    # the sink pad of the osd element, since by that time, the buffer would have
    # had got all the metadata.
    tiler_sink_pad = tiler.get_static_pad("sink")
    if not tiler_sink_pad:
        sys.stderr.write(" Unable to get src pad \n")
    else:
        tiler_sink_pad.add_probe(Gst.PadProbeType.BUFFER, tiler_sink_pad_buffer_probe, 0)

    # List the sources
    print("Now playing...")
    for i, source in enumerate(args[:-1]):
        if i != 0:
            print(i, ": ", source)

    print("Starting pipeline \n")
    # start play back and listed to events		
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except:
        pass
    # cleanup
    print("Exiting app\n")
    pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    global codec
    codec = "H264"

    global bitrate
    bitrate = 4000000

    global output_path
    output_path = '/workspace/deepstream-video2data/result.mp4'

    sys.exit(main(sys.argv))



