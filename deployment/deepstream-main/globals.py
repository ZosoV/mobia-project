SINK_TYPES = {"rtsp":0, "mp4":1, "fake":2}

FPS_STREAMS={}

PGIE_CLASS_ID_VEHICLE = 0
PGIE_CLASS_ID_BICYCLE = 1
PGIE_CLASS_ID_PERSON = 2
PGIE_CLASS_ID_ROADSIGN = 3

COUNTER_CARS = {}
LAST_ID_CAR = -1

MAX_TIME_STAMP_LEN = 32

PGIE_CLASS_NAME_CAR = "car"
SGIE_CLASS_NAME_LPD = "lpd"

CLASS_MAPPING = {
    PGIE_CLASS_NAME_CAR: 0, 
    SGIE_CLASS_NAME_LPD: 1
    }
REVERSE_CLASS_MAPPING = {
    0 : PGIE_CLASS_NAME_CAR,
    1 : SGIE_CLASS_NAME_LPD
}

DEFAULT_ATTRIBUTES = {
    "color" : "None",
    "license" : "None",
    "region" : "None",
    "lprnet_confidence" : 0.0,
    "lpdnet_confidence" : 0.0,
    "colornet_confidence" : 0.0,
    "lpd_bbox" : [0, 0, 0, 0]
}