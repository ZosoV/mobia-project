import argparse
import os
import shutil

from PIL import Image

# Configuring path through parser configuration
parser = argparse.ArgumentParser()
parser.add_argument(
    "origin",
    help="Container directory of license plate images",
    type=str
)
parser.add_argument(
    "destination",
    help="Container directory of output/accepted license plate images",
    type=str
)
args = parser.parse_args()

# Setting files, directories and folders
FILES = sorted(os.listdir(args.origin))
cwd = os.getcwd()
# if output folder not exist, create
if not os.path.exists(f"{cwd}/{args.destination}"):
    os.makedirs(f"{cwd}/{args.destination}")

# Dimensions and ratio
channel, height, width = [3,48,96]
e_height, e_width = [5, 5]
ratio = height/width

for lp in FILES:
    img = Image.open(f"img/{lp}")
    
    if ((img.width in range(width - e_width, width + e_width +1) and
        img.height == img.width * ratio) or 
        (img.height in range(height - e_height, height + e_height +1) and
        img.width == img.height / ratio)):
        shutil.copyfile(f"{cwd}/{args.origin}/{lp}",
                        f"{cwd}/{args.destination}/{lp}")
