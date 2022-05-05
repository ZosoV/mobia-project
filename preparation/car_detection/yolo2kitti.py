import os
import cv2 
import glob
import argparse

EXTENSION=".jpg"
CLASS_MAPPING = {"0":"car", "1":"plate"}

# Parser for command-line options
def return_parse():
    description = 'Convert format label from YOLO to KITTI.'
    parser = argparse.ArgumentParser(description)
    
    parser.add_argument('--source_dir',
                        default = 'frames',
                        type    = str,
                        help    = 'directory of annotations and images')
    parser.add_argument('--output_dir',
                        default = 'labels',
                        type    = str,
                        help    = 'directory of KITTI annotations')

    return parser.parse_args()

# Ensure the existence of directories
def create_paths(args):
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

# Converter
def yolo2kitti(args, file_annotation, full_name):
    # Load image and save width and height
    base_name   = full_name.split(".")[0]
    path_image  = os.path.join(args.source_dir, base_name+EXTENSION)
    h,w,_       = cv2.imread(path_image).shape
    kitti_line  = "{} 0.00 0 0.00 {} {} {} {} 0.00 0.00 0.00 0.00 0.00 0.00 0.00"
    file_kitti  = open(os.path.join(args.output_dir, full_name), "w+")

    print("Saving annotation: {}".format(os.path.join(args.output_dir, full_name)))

    for line in file_annotation:
        line_s = line.split(" ")

        label = CLASS_MAPPING[line_s[0]]

        xmin = (float(line_s[1]) - 0.5 * float(line_s[3])) * w
        ymin = (float(line_s[2]) - 0.5 * float(line_s[4])) * h
        xmax = (float(line_s[1]) + 0.5 * float(line_s[3])) * w
        ymax = (float(line_s[2]) + 0.5 * float(line_s[4])) * h

        xmin = 0 if (xmin < 0) else xmin
        ymin = 0 if (ymin < 0) else ymin
        xmax = w if (xmax > w) else xmax
        ymax = h if (ymax > h) else ymax

        tmp_line = kitti_line.format(label, xmin, ymin, xmax, ymax)
        file_kitti.write(tmp_line + "\n")

    file_kitti.close()

def load_save_annotation(args):
    annotation_path = os.path.join(args.source_dir,'*.txt')
    annotations = glob.glob(annotation_path)
    #print("Annotation_path:",annotation_path)

    for paths_annot in annotations:
        full_name       = paths_annot.split('/')[-1]
        file_annotation = open(paths_annot, "r")

        yolo2kitti(args, file_annotation, full_name)

        file_annotation.close() 

if __name__ == "__main__":
    # Create command line interaction
    args = return_parse()
    # Check or create directories for save output
    create_paths(args)
    # Generate and save conversion
    load_save_annotation(args)



#os.remove