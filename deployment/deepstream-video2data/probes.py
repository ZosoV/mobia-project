
import globals as G
import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

import numpy as np
import cv2

import pyds

# tiler_sink_pad_buffer_probe  will extract metadata received on tiler src pad
# and update params for drawing rectangle, object information etc.
def tiler_sink_pad_buffer_probe(video2data_attribs):
    # Note: this function was create with a wrapper and auxiliar function because 
    # we have to provide the video2data attributes from a configuration file in
    # this scope.

    output_folder = video2data_attribs['output_folder']
    period_per_save = int(video2data_attribs['period_per_save'])
    min_confidence_car = float(video2data_attribs['min_confidence_car'])
    min_confidence_plate = float(video2data_attribs['min_confidence_plate'])
    min_confidence_characters = float(video2data_attribs['min_confidence_characters'])
    save_labeled_copy = bool(video2data_attribs['save_labeled_copy'])


    def auxiliar_func(pad, info, u_data):
        # pad – the GstPad that is blocked
        # info – GstPadProbeInfo
        # user_data – the gpointer to optional user data.
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            print("Unable to get GstBuffer ")
            return

        # Retrieve batch metadata from the gst_buffer
        # Note that pyds.gst_buffer_get_nvds_batch_meta() expects the
        # C address of gst_buffer as input, which is obtained with hash(gst_buffer)
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        
        # A batch_meta is composed of a list of frame_meta
        # Here, we iterate throught list of frame_meta
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
            
            # Get frame rate through this probe
            G.FPS_STREAMS["stream{0}".format(frame_meta.pad_index)].get_fps()

            # Saving data and annotation per period
            if frame_meta.frame_num % period_per_save == 0:
                extract_save_data(frame_meta, 
                        gst_buffer, 
                        save_labeled_copy, 
                        output_folder,
                        min_confidence_car, 
                        min_confidence_plate, 
                        min_confidence_characters)          
            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        return Gst.PadProbeReturn.OK

    return auxiliar_func

def extract_save_data(frame_meta, gst_buffer, save_labeled_copy, output_folder,
                min_confidence_car, min_confidence_plate, min_confidence_characters):

    # Getting Image data using nvbufsurface
    # the input should be address of buffer and batch_id
    n_frame = pyds.get_nvds_buf_surface(hash(gst_buffer), frame_meta.batch_id)
    # convert python array into numpy array format in the copy mode.
    frame_copy = np.array(n_frame, copy=True, order='C')
    # convert the array into cv2 default color format
    frame_copy = cv2.cvtColor(frame_copy, cv2.COLOR_RGBA2BGRA)
    # copy to draw bboxes and check detections
    if save_labeled_copy:
        labeled_copy = frame_copy.copy()
        
    save_image = False

    # Variables to same temporal anotations and crops
    annotations_per_frame = []
    crops_plates_per_frame = {}

    # Each frame_meta is composed of a list of obj_meta
    # We iterate through this list
    l_obj = frame_meta.obj_meta_list
    while l_obj is not None:
        try:
            # Casting l_obj.data to pyds.NvDsObjectMeta
            obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
        except StopIteration:
            break

        # If the object is a CAR and higher that the threshold,
        # we save the anotation with respect to the current frame to a file
        # OR
        # If the object is a PLATE and higher that the threshold,
        # we save the anotation with respect to the current frame to a file
        if (obj_meta.obj_label == G.PGIE_CLASS_NAME_CAR \
            and  min_confidence_car < obj_meta.confidence) \
            or (obj_meta.obj_label == G.SGIE_CLASS_NAME_LPD \
            and  min_confidence_plate < obj_meta.confidence):

            # Draw bounding box of an object. Use just to check the label
            if save_labeled_copy:
                labeled_copy = draw_bounding_boxes(labeled_copy, obj_meta, obj_meta.confidence)
            
            # Create and append annotations for car and plate detection
            annotation_line = create_yolo_annotation(obj_meta, frame_copy.shape)
            annotations_per_frame.append(annotation_line)

            save_image = True

        # Additionally, if the object is a PLATE, we check the
        # classification of this object.
        # If the confidence/prob of classification is higher than 
        # the minimum, then we save the crop of the plate and 
        # its label (characters)
        if (obj_meta.obj_label == G.SGIE_CLASS_NAME_LPD \
            and  min_confidence_plate < obj_meta.confidence):
            
            # TODO: loop through classifier meta and save that annotations
            # Here I access the label information whitout while loops
            # because I'm sure that there is just one label
            class_obj=obj_meta.classifier_meta_list
            if class_obj:
                try:
                    class_meta=pyds.NvDsClassifierMeta.cast(class_obj.data)
                except StopIteration:
                    break
                c_obj=class_meta.label_info_list
                try:
                    c_meta=pyds.NvDsLabelInfo.cast(c_obj.data)
                except StopIteration:
                    break
                
                # Include the crop if the prob is greater that the min confidence
                if min_confidence_characters < c_meta.result_prob :                            
                    # Creating a crop of the plate
                    crop_plate = crop_an_image(frame_copy, obj_meta)
                    # Including a crop for later saving
                    crops_plates_per_frame[str(c_meta.result_label)] = crop_plate

        try:
            l_obj = l_obj.next
        except StopIteration:
            break


    # We save information of the current frame 
    # (frame_img, crops and annotations)
    # from the previous collected information
    if save_image:
        
        if save_labeled_copy:
            # Saving Labeled Image Frame
            img_path = "{}/stream_{}/frame_{}_labeled.jpg".format(
                                            output_folder, 
                                            frame_meta.pad_index, 
                                            frame_meta.frame_num)
            cv2.imwrite(img_path, labeled_copy)


        # Saving Image Frame
        img_path = "{}/stream_{}/frame_{}.jpg".format(
                                        output_folder, 
                                        frame_meta.pad_index, 
                                        frame_meta.frame_num)
        cv2.imwrite(img_path, frame_copy)

        # Saving Plate and Cars Detection Annotations
        annotation_path = "{}/stream_{}/frame_{}.txt".format(
                                        output_folder, 
                                        frame_meta.pad_index, 
                                        frame_meta.frame_num)
        print("Saving annotation: {}".format(annotation_path))
        with open(annotation_path, "w+") as file:
            for idx, line in enumerate(annotations_per_frame):
                if idx != len(annotations_per_frame) - 1:
                    line += "\n"
                file.write(line)


        # Saving the crops and character annotations
        # if there are crops.
        crop_number = 0
        for label, crop in crops_plates_per_frame.items():
            # Saving Crops Plate
            img_path = "{}/stream_{}_crops/frame_{}_crop_{}.jpg".format(
                output_folder, 
                frame_meta.pad_index, 
                frame_meta.frame_num,
                crop_number)
            cv2.imwrite(img_path, crop)
            

            # Saving characters annotations
            label_path = "{}/stream_{}_crops/frame_{}_crop_{}.txt".format(
                output_folder, 
                frame_meta.pad_index, 
                frame_meta.frame_num,
                crop_number)
            with open(label_path, "w+") as file:
                file.write(label)
            crop_number += 1

# FROM THIS POINT
# Utils functiond to edit image with OpenCV or create annotations

def crop_an_image(img, obj_meta):
    rect_params = obj_meta.rect_params
    xmin = int(rect_params.left)
    ymin = int(rect_params.top)
    xmax = int(rect_params.left) + int(rect_params.width)
    ymax = int(rect_params.top) + int(rect_params.height)

    # Creating a crop
    crop = img[ymin:ymax, xmin:xmax]

    return crop

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

    label = G.CLASS_MAPPING[str(obj_meta.obj_label)]

    yolo_line = "{} {:.6f} {:.6f} {:.6f} {:.6f}"

    return yolo_line.format(label,x,y,width, height)

def create_kitti_annotation(obj_meta):
    rect_params = obj_meta.rect_params
    xmin = float(rect_params.left)
    ymin = float(rect_params.top)
    xmax = float(rect_params.left) + float(rect_params.width)
    ymax = float(rect_params.top) + float(rect_params.height)

    label = G.REVERSE_CLASS_MAPPING[obj_meta.class_id]

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
