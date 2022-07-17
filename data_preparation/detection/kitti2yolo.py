import os
import cv2 
import glob
import argparse

EXTENSION=".jpg"
CLASS_MAPPING = {"car":"0", "plate":"1"}

# Parser for command-line options
def return_parse():
    description = 'Convert format label from KITTI to YOLO.'
    parser = argparse.ArgumentParser(description)
    
    parser.add_argument('--source_dir',
                        default = 'frames',
                        type    = str,
                        help    = 'directory of annotations and images')
    parser.add_argument('--output_dir',
                        default = 'labels',
                        type    = str,
                        help    = 'directory of YOLO annotations')

    return parser.parse_args()

# Ensure folders exist
def create_paths(args):
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

# Converter
def kitti2yolo(args, file_annotation, full_name):
    # Load image and save width and height
    base_name   = full_name.split(".")[0]
    path_image  = os.path.join(args.source_dir, base_name+EXTENSION)
    #print(path_image)
    h,w,_       = cv2.imread(path_image).shape
    yolo_line   = "{} {} {} {} {}"
    file_yolo   = open(os.path.join(args.output_dir, full_name), "w+")
    print("Saving annotation: {}".format(os.path.join(args.output_dir, full_name)))

    for line in file_annotation:
        line_s = line.split(" ")

        label = CLASS_MAPPING[line_s[0]]

        x       = (float(line_s[4]) + float(line_s[6])) / (2 * w)
        y       = (float(line_s[5]) + float(line_s[7])) / (2 * h)
        width   = (float(line_s[6]) - float(line_s[4])) / w
        height  = (float(line_s[7]) - float(line_s[5])) / h

        x = 0 if (x < 0) else x
        y = 0 if (y < 0) else y
        width = w if (width > w) else width
        height = h if (height > h) else height

        tmp_line = yolo_line.format(label, round(x, 6), round(y, 6),
                                    round(width, 6), round(height, 6))
        file_yolo.write(tmp_line + "\n")

    file_yolo.close()

def load_save_annotation(args):
    annotation_path = os.path.join(args.source_dir,'*.txt')
    annotations = glob.glob(annotation_path)
    #print("Annotation_path:",annotation_path)

    for paths_annot in annotations:
        full_name       = paths_annot.split('/')[-1]
        file_annotation = open(paths_annot, "r")

        kitti2yolo(args, file_annotation, full_name)

        file_annotation.close() 

if __name__ == "__main__":
    # Create command line interaction
    args = return_parse()
    # Check or create folders for save output
    create_paths(args)
    # Generate and save conversion
    load_save_annotation(args)



#os.remove