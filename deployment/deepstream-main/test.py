from ast import literal_eval
import configparser
import sys

import gi
import configparser
gi.require_version('Gst', '1.0')
from gi.repository import Gst
from ctypes import *

tracker = Gst.ElementFactory.make("nvtracker", "tracker")
if not tracker:
    sys.stderr.write(" Unable to create tracker \n")

config = configparser.ConfigParser()
config.read('configs/general_tracker_config.txt')
config.sections()

for key,value in config.items('tracker'):
    print("\nKey:",key)
    print("Type value:",type(value))
    if value[0] == "/":
        print("Type transformer:",type(value))
    else:
        print("Type transformer:",type(literal_eval(value))) 