/*
 * Copyright (c) 2021, NVIDIA CORPORATION.  All rights reserved.
 *
 * NVIDIA Corporation and its licensors retain all intellectual property
 * and proprietary rights in and to this software, related documentation
 * and any modifications thereto.  Any use, reproduction, disclosure or
 * distribution of this software and related documentation without an express
 * license agreement from NVIDIA Corporation is strictly prohibited.
 *
 */

#include <json-glib/json-glib.h>
#include <uuid.h>
#include <stdlib.h>
#include <fstream>
#include <sstream>
#include <cstring>
#include <vector>
#include "deepstream_schema.h"

static JsonObject*
generate_sensor_object (void *privData, NvDsEventMsgMeta *meta)
{
  NvDsPayloadPriv *privObj = NULL;
  NvDsSensorObject *dsSensorObj = NULL;
  JsonObject *sensorObj;
  JsonObject *jobject;

  privObj = (NvDsPayloadPriv *) privData;
  auto idMap = privObj->sensorObj.find (meta->sensorId);

  if (idMap != privObj->sensorObj.end()) {
    dsSensorObj = &idMap->second;
  } else {
    cout << "No entry for " CONFIG_GROUP_SENSOR << meta->sensorId
         << " in configuration file" << endl;
    return NULL;
  }

  /* sensor object
   * "sensor": {
       "id": "string",
       "type": "Camera/Puck",
       "location": {
         "lat": 45.99,
         "lon": 35.54,
         "alt": 79.03
       },
       "coordinate": {
         "x": 5.2,
         "y": 10.1,
         "z": 11.2
       },
       "description": "Entrance of Endeavor Garage Right Lane"
     }
   */

  // sensor object
  sensorObj = json_object_new ();
  json_object_set_string_member (sensorObj, "id", dsSensorObj->id.c_str());
  json_object_set_string_member (sensorObj, "type", dsSensorObj->type.c_str());
  json_object_set_string_member (sensorObj, "description", dsSensorObj->desc.c_str());

  // location sub object
  jobject = json_object_new ();
  json_object_set_double_member (jobject, "lat", dsSensorObj->location[0]);
  json_object_set_double_member (jobject, "lon", dsSensorObj->location[1]);
  json_object_set_double_member (jobject, "alt", dsSensorObj->location[2]);
  json_object_set_object_member (sensorObj, "location", jobject);


  // coordinate sub object
  // jobject = json_object_new ();
  // json_object_set_double_member (jobject, "x", dsSensorObj->coordinate[0]);
  // json_object_set_double_member (jobject, "y", dsSensorObj->coordinate[1]);
  // json_object_set_double_member (jobject, "z", dsSensorObj->coordinate[2]);
  // json_object_set_object_member (sensorObj, "coordinate", jobject);

  return sensorObj;
}

static JsonObject*
generate_event_object (void *privData, NvDsEventMsgMeta *meta)
{
  JsonObject *eventObj;
  uuid_t uuid;
  gchar uuidStr[37];

  /*
   * "event": {
       "id": "event-id",
       "type": "entry / exit"
     }
   */

  uuid_generate_random (uuid);
  uuid_unparse_lower(uuid, uuidStr);

  eventObj = json_object_new ();
  json_object_set_string_member (eventObj, "id", uuidStr);

  switch (meta->type) {
    case NVDS_EVENT_ENTRY:
      json_object_set_string_member (eventObj, "type", "entry");
      break;
    case NVDS_EVENT_EXIT:
      json_object_set_string_member (eventObj, "type", "exit");
      break;
    case NVDS_EVENT_MOVING:
      json_object_set_string_member (eventObj, "type", "moving");
      break;
    case NVDS_EVENT_STOPPED:
      json_object_set_string_member (eventObj, "type", "stopped");
      break;
    case NVDS_EVENT_PARKED:
      json_object_set_string_member (eventObj, "type", "parked");
      break;
    case NVDS_EVENT_EMPTY:
      json_object_set_string_member (eventObj, "type", "empty");
      break;
    case NVDS_EVENT_RESET:
      json_object_set_string_member (eventObj, "type", "reset");
      break;
    default:
      cout << "Unknown event type " << endl;
      break;
  }

  return eventObj;
}

static JsonObject*
generate_object_object (void *privData, NvDsEventMsgMeta *meta)
{
  JsonObject *objectObj;
  JsonObject *jobject;
  JsonObject *jobject_car_bbox;
  JsonObject *jobject_lpd_bbox;
  guint i;
  gchar tracking_id[64];

  // object object
  objectObj = json_object_new ();
  if (snprintf (tracking_id, sizeof(tracking_id), "%lu", meta->trackingId)
      >= (int) sizeof(tracking_id))
    g_warning("Not enough space to copy trackingId");
  json_object_set_string_member (objectObj, "car_id", tracking_id);

  switch (meta->objType) {
    case NVDS_OBJECT_TYPE_CUSTOM:
      // car sub object
      jobject = json_object_new ();
      jobject_car_bbox = json_object_new ();
      jobject_lpd_bbox = json_object_new ();

      if (meta->extMsgSize) {
        NvDsCarObject *dsObj = (NvDsCarObject *) meta->extMsg;
        if (dsObj) {
          json_object_set_string_member (jobject, "color", dsObj->color);
          json_object_set_string_member (jobject, "region", dsObj->region);
          json_object_set_string_member (jobject, "license", dsObj->license);
          json_object_set_double_member (jobject, "tcnet_confidence", dsObj->tcnet_confidence);
          json_object_set_double_member (jobject, "lpdnet_confidence", dsObj->lpdnet_confidence);
          json_object_set_double_member (jobject, "lprnet_confidence", dsObj->lprnet_confidence);
          json_object_set_double_member (jobject, "colornet_confidence", dsObj->colornet_confidence);

          //car bbox sub object
          json_object_set_int_member (jobject_car_bbox, "topleftx", dsObj->car_bbox.left);
          json_object_set_int_member (jobject_car_bbox, "toplefty", dsObj->car_bbox.top);
          json_object_set_int_member (jobject_car_bbox, "bottomrightx", dsObj->car_bbox.left + dsObj->car_bbox.width);
          json_object_set_int_member (jobject_car_bbox, "bottomrighty", dsObj->car_bbox.top + dsObj->car_bbox.height);
          

          //car bbox sub object
          json_object_set_int_member (jobject_lpd_bbox, "topleftx", dsObj->lpd_bbox.left);
          json_object_set_int_member (jobject_lpd_bbox, "toplefty", dsObj->lpd_bbox.top);
          json_object_set_int_member (jobject_lpd_bbox, "bottomrightx", dsObj->lpd_bbox.left + dsObj->lpd_bbox.width);
          json_object_set_int_member (jobject_lpd_bbox, "bottomrighty", dsObj->lpd_bbox.top + dsObj->lpd_bbox.height);
        }
      } else {
        // No car object in meta data. Attach empty car sub object.
        json_object_set_string_member (jobject, "color", "");
        json_object_set_string_member (jobject, "region", "");
        json_object_set_string_member (jobject, "license", "");
        json_object_set_double_member (jobject, "tcnet_confidence", 0.0);
        json_object_set_double_member (jobject, "lpdnet_confidence", 0.0);
        json_object_set_double_member (jobject, "lprnet_confidence", 0.0);
        json_object_set_double_member (jobject, "colornet_confidence", 0.0);


        //car bbox sub object
        json_object_set_int_member (jobject_car_bbox, "topleftx", 0);
        json_object_set_int_member (jobject_car_bbox, "toplefty", 0);
        json_object_set_int_member (jobject_car_bbox, "bottomrightx", 0);
        json_object_set_int_member (jobject_car_bbox, "bottomrighty", 0);
        

        //car bbox sub object
        json_object_set_int_member (jobject_lpd_bbox, "topleftx", 0);
        json_object_set_int_member (jobject_lpd_bbox, "toplefty", 0);
        json_object_set_int_member (jobject_lpd_bbox, "bottomrightx", 0);
        json_object_set_int_member (jobject_lpd_bbox, "bottomrighty", 0);


      }
      json_object_set_object_member (objectObj, "vehicle", jobject);
      json_object_set_object_member (objectObj, "car_bbox", jobject_car_bbox);
      json_object_set_object_member (objectObj, "lpd_bbox", jobject_lpd_bbox);
      break;
    case NVDS_OBJECT_TYPE_UNKNOWN:
      if(!meta->objectId) {
        break;
      }
      /** No information to add; object type unknown within NvDsEventMsgMeta */
      jobject = json_object_new ();
      json_object_set_object_member (objectObj, meta->objectId, jobject);
      break;
    default:
      cout << "Object type not implemented" << endl;
  }

  // signature sub array
  if (meta->objSignature.size) {
    JsonArray *jArray = json_array_sized_new (meta->objSignature.size);

    for (i = 0; i < meta->objSignature.size; i++) {
      json_array_add_double_element (jArray, meta->objSignature.signature[i]);
    }
    json_object_set_array_member (objectObj, "signature", jArray);
  }

  return objectObj;
}

gchar* generate_custom_event_message (void *privData, NvDsEventMsgMeta *meta)
{
  // Create custom function generate a custom JSON message
  JsonNode *rootNode;
  JsonObject *rootObj;
  JsonObject *sensorObj;
  JsonObject *eventObj;
  JsonObject *objectObj;
  gchar *message;

  uuid_t msgId;
  gchar msgIdStr[37];

  uuid_generate_random (msgId);
  uuid_unparse_lower(msgId, msgIdStr);

  // sensor object
  // Data about the camera
  sensorObj = generate_sensor_object (privData, meta);

  // object object
  objectObj = generate_object_object (privData, meta);

  // event object
  // TODO: a method to detect if the car is stopped or moving
  eventObj = generate_event_object (privData, meta);

  // root object
  rootObj = json_object_new ();
  json_object_set_string_member (rootObj, "messageid", msgIdStr);
  json_object_set_string_member (rootObj, "mdsversion", "1.0");
  json_object_set_string_member (rootObj, "@timestamp", meta->ts);
  json_object_set_object_member (rootObj, "sensor", sensorObj);
  json_object_set_object_member (rootObj, "object", objectObj);
  json_object_set_object_member (rootObj, "event", eventObj);

  if (meta->videoPath)
    json_object_set_string_member (rootObj, "videoPath", meta->videoPath);
  else
    json_object_set_string_member (rootObj, "videoPath", "");

  rootNode = json_node_new (JSON_NODE_OBJECT);
  json_node_set_object (rootNode, rootObj);

  message = json_to_string (rootNode, TRUE);
  json_node_free (rootNode);
  json_object_unref (rootObj);

  return message;
}

// static const gchar*
// object_enum_to_str (NvDsObjectType type, gchar* objectId)
// {
//   switch (type) {
//     case NVDS_OBJECT_TYPE_VEHICLE:
//       return "Vehicle";
//     case NVDS_OBJECT_TYPE_FACE:
//       return "Face";
//     case NVDS_OBJECT_TYPE_PERSON:
//       return "Person";
//     case NVDS_OBJECT_TYPE_BAG:
//       return "Bag";
//     case NVDS_OBJECT_TYPE_BICYCLE:
//       return "Bicycle";
//     case NVDS_OBJECT_TYPE_ROADSIGN:
//       return "RoadSign";
//     case NVDS_OBJECT_TYPE_CUSTOM:
//       return "Custom";
//     case NVDS_OBJECT_TYPE_UNKNOWN:
//       return objectId ? objectId : "Unknown";
//     default:
//       return "Unknown";
//   }
// }

// static const gchar*
// to_str (gchar* cstr)
// {
//     return reinterpret_cast<const gchar*>(cstr) ? cstr : "";
// }

// static const gchar *
// sensor_id_to_str (void *privData, gint sensorId)
// {
//   NvDsPayloadPriv *privObj = NULL;
//   NvDsSensorObject *dsObj = NULL;

//   g_return_val_if_fail (privData, NULL);

//   privObj = (NvDsPayloadPriv *) privData;

//   auto idMap = privObj->sensorObj.find (sensorId);
//   if (idMap != privObj->sensorObj.end()) {
//     dsObj = &idMap->second;
//     return dsObj->id.c_str();
//   } else {
//     cout << "No entry for " CONFIG_GROUP_SENSOR << sensorId
//         << " in configuration file" << endl;
//     return NULL;
//   }
// }

// gchar* generate_custom_event_message_minimal (void *privData, NvDsEvent *events, guint size)
// {
//   /*
//   The JSON structure of the frame
//   {
//    "version": "4.0",
//    "id": "frame-id",
//    "@timestamp": "2018-04-11T04:59:59.828Z",
//    "sensorId": "sensor-id",
//    "objects": [
//       ".......object-1 attributes...........",
//       ".......object-2 attributes...........",
//       ".......object-3 attributes..........."
//     ]
//   }
//   */

//   /*
//   An example object with Vehicle object-type
//   {
//     "version": "4.0",
//     "id": "frame-id",
//     "@timestamp": "2018-04-11T04:59:59.828Z",
//     "sensorId": "sensor-id",
//     "objects": [
//         "957|1834|150|1918|215|Vehicle|#|sedan|Bugatti|M|blue|CA 444|California|0.8",
//         "..........."
//     ]
//   }
//    */

//   JsonNode *rootNode;
//   JsonObject *jobject;
//   JsonArray *jArray;
//   guint i;
//   stringstream ss;
//   gchar *message = NULL;

//   jArray = json_array_new ();

//   for (i = 0; i < size; i++) {

//     ss.str("");
//     ss.clear();

//     NvDsEventMsgMeta *meta = events[i].metadata;
//     ss << meta->trackingId << "|" << meta->bbox.left << "|" << meta->bbox.top
//         << "|" << meta->bbox.left + meta->bbox.width << "|" << meta->bbox.top + meta->bbox.height
//         << "|" << object_enum_to_str (meta->objType, meta->objectId);

//     if (meta->extMsg && meta->extMsgSize) {
//       // Attach secondary inference attributes.
//       switch (meta->objType) {
//         case NVDS_OBJECT_TYPE_VEHICLE: {
//           NvDsVehicleObject *dsObj = (NvDsVehicleObject *) meta->extMsg;
//           if (dsObj) {
//             ss << "|#|" << to_str(dsObj->type) << "|" << to_str(dsObj->make) << "|"
//                << to_str(dsObj->model) << "|" << to_str(dsObj->color) << "|" << to_str(dsObj->license)
//                << "|" << to_str(dsObj->region) << "|" << meta->confidence;
//           }
//         }
//           break;
//         default:
//           cout << "Object type (" << meta->objType << ") not implemented" << endl;
//           break;
//       }
//     }

//     json_array_add_string_element (jArray, ss.str().c_str());
//   }

//   // It is assumed that all events / objects are associated with same frame.
//   // Therefore ts / sensorId / frameId of first object can be used.

//   jobject = json_object_new ();
//   json_object_set_string_member (jobject, "version", "4.0");
//   json_object_set_int_member (jobject, "id", events[0].metadata->frameId);
//   json_object_set_string_member (jobject, "@timestamp", events[0].metadata->ts);
//   if (events[0].metadata->sensorStr) {
//     json_object_set_string_member (jobject, "cameraId", events[0].metadata->sensorStr);
//   } else if ((NvDsPayloadPriv *) privData) {
//     json_object_set_string_member (jobject, "cameraId",
//         to_str((gchar *) sensor_id_to_str (privData, events[0].metadata->sensorId)));
//   } else {
//     json_object_set_string_member (jobject, "cameraId", "0");
//   }

//   json_object_set_array_member (jobject, "objects", jArray);

//   rootNode = json_node_new (JSON_NODE_OBJECT);
//   json_node_set_object (rootNode, jobject);

//   message = json_to_string (rootNode, TRUE);
//   json_node_free (rootNode);
//   json_object_unref (jobject);

//   return message;
// }
