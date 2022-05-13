
import globals as G
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

import pyds
import logging

# tiler_sink_pad_buffer_probe  will extract metadata received on OSD sink pad
# and update params for drawing rectangle, object information etc.
def tiler_src_pad_buffer_probe(pad, info, u_data):
    frame_number = 0
    num_rects = 0
    gst_buffer = info.get_buffer()
    if not gst_buffer:
        logging.error("Unable to get GstBuffer ")
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

        l_obj = frame_meta.obj_meta_list
        obj_counter = {
            G.PGIE_CLASS_ID_VEHICLE: 0,
            G.PGIE_CLASS_ID_PERSON: 0,
            G.PGIE_CLASS_ID_BICYCLE: 0,
            G.PGIE_CLASS_ID_ROADSIGN: 0,
        }
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            obj_counter[obj_meta.class_id] += 1
            try:
                l_obj = l_obj.next
            except StopIteration:
                break
        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]
        # py_nvosd_text_params.display_text = "Frame Number={}
        # Number of Objects={} Vehicle_count={} Person_count={}".
        # format(frame_number,num_rects, obj_counter[PGIE_CLASS_ID_VEHICLE],
        # obj_counter[PGIE_CLASS_ID_PERSON])
        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12

        # Font , font-color and font-size
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 10
        # set(red, green, blue, alpha); set to White
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        py_nvosd_text_params.set_bg_clr = 1
        # set(red, green, blue, alpha); set to Black
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)

        # send the display overlay to the screen
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)

        # print("Frame Number=", frame_number, "Number of Objects=",num_rects,
        # "Vehicle_count=",obj_counter[PGIE_CLASS_ID_VEHICLE],
        # "Person_count=",obj_counter[PGIE_CLASS_ID_PERSON])

        # Get frame rate through this probe
        G.FPS_STREAMS["stream{0}".format(frame_meta.pad_index)].get_fps()
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK


# # Probe to display FPS on screen
# def tiler_sink_pad_buffer_probe(pad, info, u_data):
#     gst_buffer = info.get_buffer()
#     if not gst_buffer:
#         logging.error("Unable to get GstBuffer ")
#         return

#     # Retrieve batch metadata from the gst_buffer
#     # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
#     # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
#     batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
#     if not batch_meta:
#         return Gst.PadProbeReturn.OK
#     l_frame = batch_meta.frame_meta_list
#     while l_frame is not None:
#         try:
#             # Note that l_frame.data needs a cast to pyds.NvDsFrameMeta
#             # The casting is done by pyds.NvDsFrameMeta.cast()
#             # The casting also keeps ownership of the underlying memory
#             # in the C code, so the Python garbage collector will leave
#             # it alone.
#             frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
#         except StopIteration:
#             break
        
#         frame_number = frame_meta.frame_num

#         # Get frame rate through this probe
#         current_fps = G.FPS_STREAMS["stream{0}".format(frame_meta.pad_index)].get_fps()

#         display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
#         display_meta.num_labels = 1
#         py_nvosd_text_params = display_meta.text_params[0]
        
#         py_nvosd_text_params.display_text = "FPS {:.2f}".format(current_fps)

#         py_nvosd_text_params.x_offset = 10
#         py_nvosd_text_params.y_offset = 12

#         # Font , font-color and font-size
#         py_nvosd_text_params.font_params.font_name = "Serif"
#         py_nvosd_text_params.font_params.font_size = 10
#         # set(red, green, blue, alpha); set to White
#         py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

#         # Text background color
#         py_nvosd_text_params.set_bg_clr = 1
#         # set(red, green, blue, alpha); set to Black
#         py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)

#         # send the display overlay to the screen
#         pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        
#         try:
#             l_frame = l_frame.next
#         except StopIteration:
#             break

#     return Gst.PadProbeReturn.OK


# Probe to display FPS on screen
def tiler_sink_pad_buffer_probe(pad, info, u_data):
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

    obj_counter = 0

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

        l_obj=frame_meta.obj_meta_list
        while l_obj is not None:
            try:
                # Casting l_obj.data to pyds.NvDsObjectMeta
                obj_meta=pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
            obj_counter = obj_meta.class_id
            try: 
                l_obj=l_obj.next
            except StopIteration:
                break

        frame_number = frame_meta.frame_num

        # Get frame rate through this probe
        current_fps = G.FPS_STREAMS["stream{0}".format(frame_meta.pad_index)].get_fps()

        display_meta = pyds.nvds_acquire_display_meta_from_pool(batch_meta)
        display_meta.num_labels = 1
        py_nvosd_text_params = display_meta.text_params[0]
        
        py_nvosd_text_params.display_text = "FPS {:.2f}".format(current_fps)

        py_nvosd_text_params.x_offset = 10
        py_nvosd_text_params.y_offset = 12

        # Font , font-color and font-size
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 10
        # set(red, green, blue, alpha); set to White
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        py_nvosd_text_params.set_bg_clr = 1
        # set(red, green, blue, alpha); set to Black
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)

        #----------

        py_nvosd_text_params.display_text = "Total cars {:.2f}".format(obj_counter)

        py_nvosd_text_params.x_offset = 100
        py_nvosd_text_params.y_offset = 12

        # Font , font-color and font-size
        py_nvosd_text_params.font_params.font_name = "Serif"
        py_nvosd_text_params.font_params.font_size = 10
        # set(red, green, blue, alpha); set to White
        py_nvosd_text_params.font_params.font_color.set(1.0, 1.0, 1.0, 1.0)

        # Text background color
        py_nvosd_text_params.set_bg_clr = 1
        # set(red, green, blue, alpha); set to Black
        py_nvosd_text_params.text_bg_clr.set(0.0, 0.0, 0.0, 1.0)

        # send the display overlay to the screen
        pyds.nvds_add_display_meta_to_frame(frame_meta, display_meta)
        
        try:
            l_frame = l_frame.next
        except StopIteration:
            break

    return Gst.PadProbeReturn.OK