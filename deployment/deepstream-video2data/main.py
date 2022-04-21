#!/usr/bin/env python3

import logging
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

MAX_DISPLAY_LEN = 64
PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3
SGIE_CLASS_NAME_LPD = "lpd"
MUXER_OUTPUT_WIDTH = 1920
MUXER_OUTPUT_HEIGHT = 1080
MUXER_BATCH_TIMEOUT_USEC = 4000000
TILED_OUTPUT_WIDTH = 1920
TILED_OUTPUT_HEIGHT = 1080
GST_CAPS_FEATURES_NVMM = "memory:NVMM"
SAVING_OUTPUT = True
pgie_classes_str = ["car", "lpd"]
CLASS_MAPPING = {"car":"0", "lpd":"1"}


MIN_CONFIDENCE = 0.6
MAX_CONFIDENCE = 1.0

MIN_LPR_CONFIDENCE = 0.6
MAX_LPR_CONFIDENCE = 1.0

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
        save_image = False
        obj_counter = {
            PGIE_CLASS_ID_VEHICLE: 0,
            PGIE_CLASS_ID_PERSON: 0,
            PGIE_CLASS_ID_BICYCLE: 0,
            PGIE_CLASS_ID_ROADSIGN: 0
        }

        # Getting Image data using nvbufsurface
        # the input should be address of buffer and batch_id
        n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
        # convert python array into numpy array format in the copy mode.
        frame_copy = np.array(n_frame, copy=True, order='C')

        # convert the array into cv2 default color format
        frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_RGBA2BGRA)


        annotations_per_frame = []
        plates_per_frame = {}

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

                frame_copy = draw_bounding_boxes(frame_copy, obj_meta, obj_meta.confidence)
                
                annotation_line = create_yolo_annotation(obj_meta, frame_copy.shape)
                annotations_per_frame.append(annotation_line)

                save_image = True

                if obj_meta.obj_label == SGIE_CLASS_NAME_LPD:
                    
                    # TODO: loop through classifier meta and save that annotations
                    rect_params = obj_meta.rect_params
                    xmin = int(rect_params.left)
                    ymin = int(rect_params.top)
                    xmax = int(rect_params.left) + int(rect_params.width)
                    ymax = int(rect_params.top) + int(rect_params.height)
                    crop_plate = frame_copy[ymin:ymax, xmin:xmax]
                    
                    # Here I access the label information whitout while loops
                    # because I'm sure that there is just one label
                    class_obj=obj_meta.classifier_meta_list
                    try:
                        class_meta=pyds.NvDsClassifierMeta.cast(class_obj.data)
                    except StopIteration:
                        break
                    c_obj=class_meta.label_info_list
                    try:
                        c_meta=pyds.NvDsLabelInfo.cast(c_obj.data)
                    except StopIteration:
                        break
                    if MIN_LPR_CONFIDENCE < c_meta < MAX_LPR_CONFIDENCE:
                        plates_per_frame[str(c_meta.result_label)] = crop_plate

            try:
                l_obj = l_obj.next
            except StopIteration:
                break

        # print("Frame Number=", frame_number, "Number of Objects=", num_rects, "Vehicle_count=",
        #       obj_counter[PGIE_CLASS_ID_VEHICLE], "Person_count=", obj_counter[PGIE_CLASS_ID_PERSON])
        # Get frame rate through this probe
        fps_streams["stream{0}".format(frame_meta.pad_index)].get_fps()
        if save_image:
            
            # Saving Image Frame
            img_path = "{}/stream_{}/frame_{}.jpg".format(folder_name, frame_meta.pad_index, frame_number)
            cv2.imwrite(img_path, frame_copy)

            # Saving Plate and Cars Detection Annotation
            annotation_path = "{}/stream_{}/frame_{}.txt".format(folder_name, frame_meta.pad_index, frame_number)
            print("Saving annotation: {}".format(annotation_path))

            with open(annotation_path, "w+") as file:
                for idx, line in enumerate(annotations_per_frame):
                    if idx != len(annotations_per_frame) - 1:
                        line += "\n"
                    file.write(line)

           
            crop_number = 0
            for label, crop in plates_per_frame.items():
                # Saving Crop Plate
                img_path = "{}/stream_{}_crops/frame_{}_crop_{}.jpg".format(
                    folder_name, 
                    frame_meta.pad_index, 
                    frame_number,
                    crop_number)
                cv2.imwrite(img_path, crop)
                

                # Saving LPR Annotations
                label_path = "{}/stream_{}_crops/frame_{}_crop_{}.txt".format(
                    folder_name, 
                    frame_meta.pad_index, 
                    frame_number,
                    crop_number)
                with open(label_path, "w+") as file:
                    file.write(label)
                crop_number += 1

        saved_count["stream_{}".format(frame_meta.pad_index)] += 1
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK

def create_yolo_annotation(obj_meta, img_shape):
    img_height, img_width, _  = img_shape
    rect_params = obj_meta.rect_params
    xmin = float(rect_params.left)
    ymin = float(rect_params.top)
    xmax = float(rect_params.left) + float(rect_params.width)
    ymax = float(rect_params.top) + float(rect_params.height)

    x = (xmin + xmax) / (2 * img_width)
    y = (ymin + ymax) / (2 * img_height)
    width = float(rect_params.width) / img_width
    height = float(rect_params.height) / img_height

    label = CLASS_MAPPING[str(obj_meta.obj_label)]

    yolo_line = "{} {:.6f} {:.6f} {:.6f} {:.6f}"

    return yolo_line.format(label,x,y,width, height)

def create_kitti_annotation(obj_meta):
    rect_params = obj_meta.rect_params
    xmin = float(rect_params.left)
    ymin = float(rect_params.top)
    xmax = float(rect_params.left) + float(rect_params.width)
    ymax = float(rect_params.top) + float(rect_params.height)

    label = pgie_classes_str[obj_meta.class_id]

    kitti_line  = "{} 0.00 0 0.00 {:.2f} {:.2f} {:.2f} {:.2f} 0.00 0.00 0.00 0.00 0.00 0.00 0.00"
    
    return kitti_line.format(label, xmin, ymin, xmax, ymax)

def draw_bounding_boxes(image, obj_meta, confidence):
    confidence = '{0:.2f}'.format(confidence)
    rect_params = obj_meta.rect_params
    top = int(rect_params.top)
    left = int(rect_params.left)
    width = int(rect_params.width)
    height = int(rect_params.height)
    # obj_name = pgie_classes_str[obj_meta.class_id]
    obj_name = str(obj_meta.obj_label)
    image = cv2.rectangle(image, (left, top), (left + width, top + height), (0, 0, 255, 0), 2, cv2.LINE_4)

    # Note that on some systems cv2.putText erroneously draws horizontal lines across the image
    image = cv2.putText(image, obj_name + '--c=' + str(confidence), (left - 10, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 1,
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
        os.mkdir(folder_name + "/stream_" + str(i) + "_crops")
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

    # Adding tracker and secondary classifier
    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    if not tracker:
        sys.stderr.write(" Unable to create tracker \n")

    sgie1 = Gst.ElementFactory.make("nvinfer", "secondary1-nvinference-engine")
    if not sgie1:
        sys.stderr.write(" Unable to make sgie1 \n")

    sgie2 = Gst.ElementFactory.make("nvinfer", "secondary2-nvinference-engine")
    if not sgie2:
        sys.stderr.write(" Unable to make sgie2 \n")
    # -------------
    #Set properties of tracker
    config = configparser.ConfigParser()
    config.read('configs/general_tracker_config.txt')
    config.sections()

    for key in config['tracker']:
        if key == 'tracker-width' :
            tracker_width = config.getint('tracker', key)
            tracker.set_property('tracker-width', tracker_width)
        if key == 'tracker-height' :
            tracker_height = config.getint('tracker', key)
            tracker.set_property('tracker-height', tracker_height)
        if key == 'gpu-id' :
            tracker_gpu_id = config.getint('tracker', key)
            tracker.set_property('gpu_id', tracker_gpu_id)
        if key == 'll-lib-file' :
            tracker_ll_lib_file = config.get('tracker', key)
            tracker.set_property('ll-lib-file', tracker_ll_lib_file)
        if key == 'll-config-file' :
            tracker_ll_config_file = config.get('tracker', key)
            tracker.set_property('ll-config-file', tracker_ll_config_file)
        if key == 'enable-batch-process' :
            tracker_enable_batch_process = config.getint('tracker', key)
            tracker.set_property('enable_batch_process', tracker_enable_batch_process)
        if key == 'enable-past-frame' :
            tracker_enable_past_frame = config.getint('tracker', key)
            tracker.set_property('enable_past_frame', tracker_enable_past_frame)


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
    if SAVING_OUTPUT:
        nvvidconv_postosd = Gst.ElementFactory.make("nvvideoconvert", "convertor_postosd")
        if not nvvidconv_postosd:
            sys.stderr.write(" Unable to create nvvidconv_postosd \n")

        # Create a caps filter
        caps_postosd = Gst.ElementFactory.make("capsfilter", "filter")
        caps_postosd.set_property("caps", Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420"))

        # Make the encoder
        if codec == "H264":
            encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
            print("Creating H264 Encoder")
        elif codec == "H265":
            encoder = Gst.ElementFactory.make("nvv4l2h265enc", "encoder")
            print("Creating H265 Encoder")
        if not encoder:
            sys.stderr.write(" Unable to create encoder")
        encoder.set_property('bitrate', bitrate)
        if is_aarch64():
            encoder.set_property('preset-level', 1)
            encoder.set_property('insert-sps-pps', 1)
            encoder.set_property('bufapi-version', 1)

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

    if not SAVING_OUTPUT:
        print("Creating FakeSink \n")
        sink = Gst.ElementFactory.make("fakesink", "fakesink")
        if not sink:
            sys.stderr.write(" Unable to create fake sink \n")

    if is_live:
        print("Atleast one of the sources is live")
        streammux.set_property('live-source', 1)

    streammux.set_property('width', 1920)
    streammux.set_property('height', 1080)
    streammux.set_property('batch-size', number_sources)
    streammux.set_property('batched-push-timeout', bitrate)
    pgie.set_property('config-file-path', "configs/tcnet_pgie_config.txt")
    pgie_batch_size = pgie.get_property("batch-size")
    if (pgie_batch_size != number_sources):
        print("WARNING: Overriding infer-config batch-size", pgie_batch_size, " with number of sources ",
              number_sources, " \n")
        pgie.set_property("batch-size", number_sources)

    # TODO: add to config file
    sgie1.set_property('config-file-path', "configs/lpdnet_sgie1_config.txt")

    # TODO: add to config file
    sgie2.set_property('config-file-path', "configs/lprnet_sgie2_config.txt")


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
    pipeline.add(tracker) # adding tracker
    pipeline.add(sgie1) # adding second detector
    pipeline.add(sgie2) # adding a third classifier
    pipeline.add(tiler)
    pipeline.add(nvvidconv)
    pipeline.add(filter1)
    pipeline.add(nvvidconv1)
    pipeline.add(nvosd)

    if SAVING_OUTPUT:
        pipeline.add(nvvidconv_postosd)
        pipeline.add(caps_postosd)
        pipeline.add(encoder)
        pipeline.add(codecparse)
        pipeline.add(mux)

    pipeline.add(sink)

    print("Linking elements in the Pipeline \n")

    # TODO: check what is doing a caps
    # Here filter1 is a caps, but here it is used before nvosd
    # why?
    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(sgie1)
    sgie1.link(sgie2)
    sgie2.link(nvvidconv1)
    nvvidconv1.link(filter1)
    filter1.link(tiler)

    # Aqui viene el probe

    tiler.link(nvvidconv)
    nvvidconv.link(nvosd)
    if not SAVING_OUTPUT:
        nvosd.link(sink)

    if SAVING_OUTPUT:
        nvosd.link(nvvidconv_postosd)
        nvvidconv_postosd.link(caps_postosd)
        caps_postosd.link(encoder)
        encoder.link(codecparse)
        codecparse.link(mux)
        mux.link(sink)

    # create an event loop and feed gstreamer bus mesages to it
    loop = GObject.MainLoop()
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, loop)
    
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
    output_path = '/workspace/deepstream-video2data/output/result.mp4'

    sys.exit(main(sys.argv))



