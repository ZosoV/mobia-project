# Custom Nvmsgconv library

Refer to the DeepStream SDK documentation for a description of the plugin.

## Pre-requisites:
- glib-2.0
- json-glib-1.0
- uuid

Install using:
   ``` bash
   sudo apt-get install libglib2.0-dev libjson-glib-dev uuid-dev
   ```
Compiling and installing the plugin:
   
   ``` bash
   make 
   sudo make install
   ```

## Custom Message Extension for a custom object `NvDsCarObject`

In this custom library, we include an extra object `NvDsCarObject`. The object
was defined on [../includes/nvdsmeta_schema](../includes/nvdsmeta_schema) as

``` C
typedef struct NvDsCarObject {
  // Holds the car class tracking ID.
  gchar *color; 
  gchar *region;
  gchar *license;
  gdouble lprnet_confidence;
  gdouble lpdnet_confidence;
  gdouble tcnet_confidence;
  gdouble colornet_confidence;

  NvDsRect car_bbox;
  NvDsRect lpd_bbox;

} NvDsCarObject;

```

Additionally, in [deepstream_schema/custommsg_payload.cpp](./deepstream_schema/custommsg_payload.cpp), we add new functionality to process the new custom object and send a customized JSON message. You can 
explore the functions: `generate_custom_event_message` and `generate_object_object`
to check the changes with respect of [deepstream_schema/eventmsg_payload.cpp](./deepstream_schema/eventmsg_payload.cpp).

Finally, we add our new function `generate_custom_event_message` in [nvmsgconv.cpp](./nvmsgconv.cpp)
at the function `nvds_msg2p_generate` using the custom payload key as follows

``` C
else if (ctx->payloadType == NVDS_PAYLOAD_CUSTOM) {
    message = generate_custom_event_message (ctx->privData, events->metadata);
    if (message) {
      len = strlen (message);
      // Remove '\0' character at the end of string and just copy the content.
      payload->payload = g_memdup (message, len);
      payload->payloadSize = len;
      g_free (message);
    }
```