import argparse
import os

from PIL import Image

# Loading path through parser configuration
parser = argparse.ArgumentParser()
parser.add_argument(
    "path", help="Container directory of license plate images", type=str
)
args = parser.parse_args()

# UNIQUE_LICENSE_PLATES = set()

FILES = sorted(os.listdir(args.path))

# crop_reference_size
channel, height, width = [3,48,96]
# crop acceptable erros
e_height, e_width = [5, 5]

# ratio height/width
ratio = height/width

# If I increase the height by e_height then width must be
# aceptable_height1 = height + e_height
# aceptable_width1 = aceptable_height1/ratio

# If I increase the width by e_width then height must be
# aceptable_width2 = width + e_width
# aceptable_height2 = ratio * aceptable_width2

# TODO: check the crop dims, if the the crop is within the
# aceptable 1 or 2, we can use the crop

f = open("accepted_img.txt", "w")

for lp in FILES:
    img = Image.open(f"img/{lp}")
    
    if (img.width in range(width - e_width, width + e_width) and
        img.height == img.width * ratio):
        f.write(lp+"\n")

f.close()