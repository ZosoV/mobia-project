import os
import cv2 
import glob
import argparse

WIDTH   = 1024
HEIGHT  = 512
DIM = (WIDTH,HEIGHT)

def return_parse():
    parser = argparse.ArgumentParser(description='Resize images.')
    parser.add_argument('--img_dir',
                        default = 'data',
                        type    = str,
                        help    = 'image directory')
    parser.add_argument('--output_dir',
                        default = 'resized',
                        type    = str,
                        help    = 'directory of saved images')

    return parser.parse_args()

def create_paths(args):
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

def resize_and_save(args, files_names):
    for img_name in files_names:
        img         = cv2.imread(img_name) 
        resized     = cv2.resize(img, DIM)    
        img_name    = img_name.split('/')[-1]
        cv2.imwrite(os.path.join(args.output_dir,img_name),resized)
        print("Saving reshape image: {}".format(os.path.join(args.output_dir,img_name)))

if __name__ == "__main__":
    # Create command line interaction
    args = return_parse()
    # Check or create folders for save output
    create_paths(args)
    # Load file names
    data_path = os.path.join(args.img_dir,'*.jpg') 
    files_names = glob.glob(data_path)
    
    resize_and_save(args, files_names)
