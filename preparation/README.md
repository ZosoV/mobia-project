# Labeling

## LabelImg

* Follow the [installation and usage steps](https://github.com/tzutalin/labelImg) according to the characteristics of the machine.
* The general approach:
  * Define the list of classes that will be used in `data/predefined_classes.txt`.
  * Choose the directory `Open Dir` with your images.
  * Choose the output folder `Change Save Dir`.
  * Select the annotation format.
* Features:
  * Auto-save mode: `View > Auto Save Mode`
  * Default label: `Box Labels > Use default label`

# Coversion

## kitti2yolo.py

Convert from KITTI to YOLO annotation format.

`python3 kitti2yolo.py --source_dir <annotations and images directory> --output_dir <YOLO annotations directory>`

## yolo2kitti.py

Convert from YOLO to KITTI annotation format.

`python3 yolo2kitti.py --source_dir <annotations and images directory> --output_dir <KITTI annotations directory>`

# Image resize

## resize.py

The width and height are assigned inside the script.

`python3 resize.py --img_dir <image directory> --output_dir <directory of resized images>`
