# NvDsCarObject and alloc_nvds_car_object

Python bindings for a custom object named `NvDsCarObject` to send an extended msg via `NvDsEventMsgMeta`.

This repository was developed followed these references: 
- [pyds_tracker_meta](https://github.com/mrtj/pyds_tracker_meta)
- [pyds_analytics_meta](https://github.com/7633/pyds_analytics_meta) 
- NVidia developers forum topic [developer_zone](https://forums.developer.nvidia.com/t/deepstream-5-0-python-bindings-for-gst-nvdsanalytics-access-meta-data/147670/11)
- The example binding for `NvDsVehicleObject` from [bindschema.cpp](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/blob/master/bindings/src/bindschema.cpp).
- [pybind11](https://github.com/pybind/pybind11) wrapper to access Nvidia [DeepStream](https://developer.nvidia.com/deepstream-sdk).

## Introduction
This library provides utility functions to access, allocate, and create a custom object `NvDsCarObject`. See [DeepStream Python API](https://docs.nvidia.com/metropolis/deepstream/6.0/python-api/PYTHON_API/NvDsMetaSchema/NvDsVehicleObject.html?highlight=vehicle) NvDsVehicleObject for reference.

## Installation

### Prerequisites

1. Install [pybind11](https://github.com/pybind/pybind11). The recommended way is to [build it from source](https://pybind11.readthedocs.io/en/stable/basics.html?highlight=install#compiling-the-test-cases). Alternatively you might try simply `pip3 install pybind11`.
2. You should have `gstreamer-1.0` and `gstreamer-video-1.0` packages installed in your system. If you are using DeepStream, you most likely installed these packages.
3. You will need also the standard `c++` compiler you usually find in Linux distributions. `c++11` standard is used.

### Compile the source

1. The source should be compiled on your target platform (Jetson or x86).
2. Set your the correct paths in `build.sh` 
3. Launch `build.sh`
4. Install the compiled module with `python setup.py install` (use `sudo` or `python3` if needed).

## Usage

`NvDsCarObject` is meant to be used together with the standard [Python bindings for DeepStream](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps). Make sure you have `pyds` available.

Most likely you will use this library for sending a custom msg via `NvDsEventMsgMeta`, when your are using the plugins `nvmsgconv` and `nvmsgbroker` to send msg to a broker (like Kafka). The [deepstream-test4](https://github.com/NVIDIA-AI-IOT/deepstream_python_apps/tree/master/apps/deepstream-test4) python app shows you how to set up a custom message.
 

The example snippet provided bellow shows how to allocate a custom car object, edit its attributes and save into the extended message.
Note that you can edit the attributes with the metadata you will need.

```python
import pyds_custom

# msg_meta is an NvDsEventMsgMeta

obj = pyds_custom.alloc_nvds_car_object()
obj.color = "default blue"
obj.license = "default XYZ"
obj.region = "default CA"
obj.lprnet_confidence = 0.9
obj.lpdnet_confidence = 0.8
obj.tcnet_confidence = 0.5
obj.colornet_confidence = 0.6

obj.car_bbox.top = 10
obj.car_bbox.left = 10
obj.car_bbox.width = 200
obj.car_bbox.height = 50


obj.lpd_bbox.top = 20
obj.lpd_bbox.left = 30
obj.lpd_bbox.width = 100
obj.lpd_bbox.height = 500

msg_meta.extMsg = obj
msg_meta.extMsgSize = sys.getsizeof(pyds_custom.NvDsCarObject)

```

**Note** that you also need to set the copy and free function for the new custom object.

```python
import pyds_custom

# copy function
def meta_copy_func(data, user_data):
    # Cast data to pyds.NvDsUserMeta
    user_meta = pyds.NvDsUserMeta.cast(data)
    src_meta_data = user_meta.user_meta_data
    # Cast src_meta_data to pyds.NvDsEventMsgMeta
    srcmeta = pyds.NvDsEventMsgMeta.cast(src_meta_data)
    # Duplicate the memory contents of srcmeta to dstmeta
    # First use pyds.get_ptr() to get the C address of srcmeta, then
    # use pyds.memdup() to allocate dstmeta and copy srcmeta into it.
    # pyds.memdup returns C address of the allocated duplicate.
    dstmeta_ptr = pyds.memdup(pyds.get_ptr(srcmeta),
                              sys.getsizeof(pyds.NvDsEventMsgMeta))
    # Cast the duplicated memory to pyds.NvDsEventMsgMeta
    dstmeta = pyds.NvDsEventMsgMeta.cast(dstmeta_ptr)

    # Duplicate contents of ts field. Note that reading srcmeat.ts
    # returns its C address. This allows to memory operations to be
    # performed on it.
    dstmeta.ts = pyds.memdup(srcmeta.ts, G.MAX_TIME_STAMP_LEN + 1)

    # Copy the sensorStr. This field is a string property. The getter (read)
    # returns its C address. The setter (write) takes string as input,
    # allocates a string buffer and copies the input string into it.
    # pyds.get_string() takes C address of a string and returns the reference
    # to a string object and the assignment inside the binder copies content.
    dstmeta.sensorStr = pyds.get_string(srcmeta.sensorStr)

    if srcmeta.objSignature.size > 0:
        dstmeta.objSignature.signature = pyds.memdup(
            srcmeta.objSignature.signature, srcmeta.objSignature.size)
        dstmeta.objSignature.size = srcmeta.objSignature.size

    if srcmeta.extMsgSize > 0:
        if srcmeta.objType == pyds.NvDsObjectType.NVDS_OBJECT_TYPE_CUSTOM:
            srcobj = pyds_custom.NvDsCarObject.cast(srcmeta.extMsg)
            
            obj = pyds_custom.alloc_nvds_car_object()
            obj.color = pyds.get_string(srcobj.color)
            obj.license = pyds.get_string(srcobj.license)
            obj.region = pyds.get_string(srcobj.region)
            obj.lprnet_confidence = srcobj.lprnet_confidence
            obj.lpdnet_confidence = srcobj.lpdnet_confidence
            obj.tcnet_confidence = srcobj.tcnet_confidence
            obj.colornet_confidence = srcobj.colornet_confidence
            
            obj.car_bbox.top = srcobj.car_bbox.top
            obj.car_bbox.left = srcobj.car_bbox.left
            obj.car_bbox.width = srcobj.car_bbox.width
            obj.car_bbox.height = srcobj.car_bbox.height

            obj.lpd_bbox.top = srcobj.lpd_bbox.top
            obj.lpd_bbox.left = srcobj.lpd_bbox.left
            obj.lpd_bbox.width = srcobj.lpd_bbox.width
            obj.lpd_bbox.height = srcobj.lpd_bbox.height 

            dstmeta.extMsg = obj
            dstmeta.extMsgSize = sys.getsizeof(pyds_custom.NvDsCarObject)
    return dstmeta
```
```python
import pyds_custom

# free function
def meta_free_func(data, user_data):
    user_meta = pyds.NvDsUserMeta.cast(data)
    srcmeta = pyds.NvDsEventMsgMeta.cast(user_meta.user_meta_data)

    # pyds.free_buffer takes C address of a buffer and frees the memory
    # It's a NOP if the address is NULL
    pyds.free_buffer(srcmeta.ts)
    pyds.free_buffer(srcmeta.sensorStr)

    if srcmeta.objSignature.size > 0:
        pyds.free_buffer(srcmeta.objSignature.signature)
        srcmeta.objSignature.size = 0

    if srcmeta.extMsgSize > 0:
        if srcmeta.objType == pyds.NvDsObjectType.NVDS_OBJECT_TYPE_CUSTOM:
            obj = pyds_custom.NvDsCarObject.cast(srcmeta.extMsg)

            # Note: You just need to free the string components
            # The rest values are free with pyds.free_gbuffer(srcmeta.extMsg)
            pyds.free_buffer(obj.color)
            pyds.free_buffer(obj.license)
            pyds.free_buffer(obj.region)
        pyds.free_gbuffer(srcmeta.extMsg)
        srcmeta.extMsgSize = 0
```