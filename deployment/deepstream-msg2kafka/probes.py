

import globals as G


import sys

sys.path.append('../')

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst
from common.utils import long_to_uint64

import pyds
import logging

# Callback function for deep-copying an NvDsEventMsgMeta struct
def meta_copy_func(data, user_data):
    # Cast data to pyds.NvDsUserMeta
    user_meta = pyds.NvDsUserMeta.cast(data)
    src_meta_data = user_meta.user_meta_data
    # Cast src_meta_data to pyds.NvDsEventMsgMeta
    srcmeta = pyds.NvDsEventMsgMeta.cast(src_meta_data)
    # Duplicate the memory contents of srcmeta to dstmeta
    # First use pyds.get_ptr() to get the C address of srcmeta, then
    # use pyds.memdup() to allocate dstmeta and copy srcmeta into it.
    # pyds.memdup returns C address of the allocated duplicate.
    dstmeta_ptr = pyds.memdup(pyds.get_ptr(srcmeta),
                              sys.getsizeof(pyds.NvDsEventMsgMeta))
    # Cast the duplicated memory to pyds.NvDsEventMsgMeta
    dstmeta = pyds.NvDsEventMsgMeta.cast(dstmeta_ptr)

    # Duplicate contents of ts field. Note that reading srcmeat.ts
    # returns its C address. This allows to memory operations to be
    # performed on it.
    dstmeta.ts = pyds.memdup(srcmeta.ts, G.MAX_TIME_STAMP_LEN + 1)

    # Copy the sensorStr. This field is a string property. The getter (read)
    # returns its C address. The setter (write) takes string as input,
    # allocates a string buffer and copies the input string into it.
    # pyds.get_string() takes C address of a string and returns the reference
    # to a string object and the assignment inside the binder copies content.
    dstmeta.sensorStr = pyds.get_string(srcmeta.sensorStr)

    if srcmeta.objSignature.size > 0:
        dstmeta.objSignature.signature = pyds.memdup(
            srcmeta.objSignature.signature, srcmeta.objSignature.size)
        dstmeta.objSignature.size = srcmeta.objSignature.size

    if srcmeta.extMsgSize > 0:
        if srcmeta.objType == pyds.NvDsObjectType.NVDS_OBJECT_TYPE_VEHICLE:
            srcobj = pyds.NvDsVehicleObject.cast(srcmeta.extMsg)
            obj = pyds.alloc_nvds_vehicle_object()
            obj.type = pyds.get_string(srcobj.type)
            obj.make = pyds.get_string(srcobj.make)
            obj.model = pyds.get_string(srcobj.model)
            obj.color = pyds.get_string(srcobj.color)
            obj.license = pyds.get_string(srcobj.license)
            obj.region = pyds.get_string(srcobj.region)
            dstmeta.extMsg = obj
            dstmeta.extMsgSize = sys.getsizeof(pyds.NvDsVehicleObject)
        if srcmeta.objType == pyds.NvDsObjectType.NVDS_OBJECT_TYPE_PERSON:
            srcobj = pyds.NvDsPersonObject.cast(srcmeta.extMsg)
            obj = pyds.alloc_nvds_person_object()
            obj.age = srcobj.age
            obj.gender = pyds.get_string(srcobj.gender)
            obj.cap = pyds.get_string(srcobj.cap)
            obj.hair = pyds.get_string(srcobj.hair)
            obj.apparel = pyds.get_string(srcobj.apparel)
            dstmeta.extMsg = obj
            dstmeta.extMsgSize = sys.getsizeof(pyds.NvDsVehicleObject)

    return dstmeta


# Callback function for freeing an NvDsEventMsgMeta instance
def meta_free_func(data, user_data):
    user_meta = pyds.NvDsUserMeta.cast(data)
    srcmeta = pyds.NvDsEventMsgMeta.cast(user_meta.user_meta_data)

    # pyds.free_buffer takes C address of a buffer and frees the memory
    # It's a NOP if the address is NULL
    pyds.free_buffer(srcmeta.ts)
    pyds.free_buffer(srcmeta.sensorStr)

    if srcmeta.objSignature.size > 0:
        pyds.free_buffer(srcmeta.objSignature.signature)
        srcmeta.objSignature.size = 0

    if srcmeta.extMsgSize > 0:
        if srcmeta.objType == pyds.NvDsObjectType.NVDS_OBJECT_TYPE_VEHICLE:
            obj = pyds.NvDsVehicleObject.cast(srcmeta.extMsg)
            pyds.free_buffer(obj.type)
            pyds.free_buffer(obj.color)
            pyds.free_buffer(obj.make)
            pyds.free_buffer(obj.model)
            pyds.free_buffer(obj.license)
            pyds.free_buffer(obj.region)
        if srcmeta.objType == pyds.NvDsObjectType.NVDS_OBJECT_TYPE_PERSON:
            obj = pyds.NvDsPersonObject.cast(srcmeta.extMsg)
            pyds.free_buffer(obj.gender)
            pyds.free_buffer(obj.cap)
            pyds.free_buffer(obj.hair)
            pyds.free_buffer(obj.apparel)
        pyds.free_gbuffer(srcmeta.extMsg)
        srcmeta.extMsgSize = 0


def generate_vehicle_meta(data):
    obj = pyds.NvDsVehicleObject.cast(data)
    obj.type = "sedan"
    obj.color = "blue"
    obj.make = "Bugatti"
    obj.model = "M"
    obj.license = "XX1234"
    obj.region = "CA"
    return obj


def generate_person_meta(data):
    obj = pyds.NvDsPersonObject.cast(data)
    obj.age = 45
    obj.cap = "none"
    obj.hair = "black"
    obj.gender = "male"
    obj.apparel = "formal"
    return obj


def generate_event_msg_meta(data, obj_meta, frame_number):
    msg_meta = pyds.NvDsEventMsgMeta.cast(data)

    msg_meta.bbox.top = obj_meta.rect_params.top
    msg_meta.bbox.left = obj_meta.rect_params.left
    msg_meta.bbox.width = obj_meta.rect_params.width
    msg_meta.bbox.height = obj_meta.rect_params.height
    msg_meta.frameId = frame_number
    msg_meta.trackingId = long_to_uint64(obj_meta.object_id)
    msg_meta.confidence = obj_meta.confidence

    msg_meta.sensorId = 0
    msg_meta.placeId = 0
    msg_meta.moduleId = 0
    msg_meta.sensorStr = "sensor-0"
    msg_meta.ts = pyds.alloc_buffer(G.MAX_TIME_STAMP_LEN + 1)
    pyds.generate_ts_rfc3339(msg_meta.ts, G.MAX_TIME_STAMP_LEN)

    # This demonstrates how to attach custom objects.
    # Any custom object as per requirement can be generated and attached
    # like NvDsVehicleObject / NvDsPersonObject. Then that object should
    # be handled in payload generator library (nvmsgconv.cpp) accordingly.
    if obj_meta.class_id == G.PGIE_CLASS_ID_VEHICLE:
        msg_meta.type = pyds.NvDsEventType.NVDS_EVENT_MOVING
        msg_meta.objType = pyds.NvDsObjectType.NVDS_OBJECT_TYPE_VEHICLE
        msg_meta.objClassId = G.PGIE_CLASS_ID_VEHICLE
        obj = pyds.alloc_nvds_vehicle_object()
        obj = generate_vehicle_meta(obj)
        msg_meta.extMsg = obj
        msg_meta.extMsgSize = sys.getsizeof(pyds.NvDsVehicleObject)
    if obj_meta.class_id == G.PGIE_CLASS_ID_PERSON:
        msg_meta.type = pyds.NvDsEventType.NVDS_EVENT_ENTRY
        msg_meta.objType = pyds.NvDsObjectType.NVDS_OBJECT_TYPE_PERSON
        msg_meta.objClassId = G.PGIE_CLASS_ID_PERSON
        obj = pyds.alloc_nvds_person_object()
        obj = generate_person_meta(obj)
        msg_meta.extMsg = obj
        msg_meta.extMsgSize = sys.getsizeof(pyds.NvDsPersonObject)
    return msg_meta

def send_msg_to_frame(msg_meta, batch_meta, frame_meta):
    user_event_meta = pyds.nvds_acquire_user_meta_from_pool(batch_meta)
    if user_event_meta:
        user_event_meta.user_meta_data = msg_meta
        user_event_meta.base_meta.meta_type = pyds.NvDsMetaType.NVDS_EVENT_MSG_META
        # Setting callbacks in the event msg meta. The bindings
        # layer will wrap these callables in C functions.
        # Currently only one set of callbacks is supported.
        pyds.user_copyfunc(user_event_meta, meta_copy_func)
        pyds.user_releasefunc(user_event_meta, meta_free_func)
        pyds.nvds_add_user_meta_to_frame(frame_meta,
                                        user_event_meta)
    else:
        logging.error("Error in attaching event meta to buffer\n")

# osd_sink_pad_buffer_probe  will extract metadata received on OSD sink pad
# and update params for drawing rectangle, object information etc.
# IMPORTANT NOTE:
# a) probe() callbacks are synchronous and thus holds the buffer
#    (info.get_buffer()) from traversing the pipeline until user return.
# b) loops inside probe() callback could be costly in python.
#    So users shall optimize according to their use-case.

def osd_sink_pad_buffer_probe(nvmsgconv_attribs):

    # Loading specific attributes for this probe
    period_per_msg = int(nvmsgconv_attribs['period_per_msg'])

    def aux_function(pad, info, u_data):
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            logging.error("Unable to get GstBuffer ")
            return

        # Retrieve batch metadata from the gst_buffer
        # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
        # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        if not batch_meta:
            return Gst.PadProbeReturn.OK
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
                continue

            # Frequency of messages to be send will be based on use case.
            # Sending messages per period
            # One message per object if there is detection
            if (frame_meta.frame_num % period_per_msg) == 0:

                is_first_object = True
                l_obj = frame_meta.obj_meta_list
                while l_obj is not None:
                    try:
                        obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                    except StopIteration:
                        continue

                    # Ideally NVDS_EVENT_MSG_META should be attached to buffer by the
                    # component implementing detection / recognition logic.
                    # Here it demonstrates how to use / attach that meta data.
                    if is_first_object:
                        # Here message is being sent for first object every x frames.

                        # Allocating an NvDsEventMsgMeta instance and getting
                        # reference to it. The underlying memory is not managed by
                        # Python so that downstream plugins can access it. Otherwise
                        # the garbage collector will free it when this probe exits.
                        msg_meta = pyds.alloc_nvds_event_msg_meta()

                        # This step fills the required information into the msg_meta
                        msg_meta = generate_event_msg_meta(msg_meta, obj_meta, frame_meta.frame_num)

                        # This step send the msg at a frame level
                        send_msg_to_frame(msg_meta, batch_meta, frame_meta)

                        is_first_object = False
                    try:
                        l_obj = l_obj.next
                    except StopIteration:
                        break
  
            # Get frame rate through this probe
            G.FPS_STREAMS["stream{0}".format(frame_meta.pad_index)].get_fps()
            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        # print("Frame Number =", frame_number, "Vehicle Count =",
        #       obj_counter[G.PGIE_CLASS_ID_VEHICLE], "Person Count =",
        #       obj_counter[G.PGIE_CLASS_ID_PERSON])
        return Gst.PadProbeReturn.OK
    
    return aux_function



