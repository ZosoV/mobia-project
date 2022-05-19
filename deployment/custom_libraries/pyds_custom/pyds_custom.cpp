#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "nvdsmeta_schema.h"
#include <string>

namespace py = pybind11;


#define STRING_PROPERTY(TYPE, FIELD)                               \
        [](const TYPE &self)->size_t {                             \
            return (size_t)self.FIELD;                             \
        },                                                         \
        [](TYPE &self, std::string str) {                          \
            int strSize = str.size();                              \
            self.FIELD = (char*)calloc(strSize + 1, sizeof(char)); \
            str.copy(self.FIELD, strSize);                         \
        },                                                         \
        py::return_value_policy::reference

PYBIND11_MODULE(pyds_custom, m) {
        m.doc() = "Custom bindings";
	py::class_<NvDsCarObject>(m,"NvDsCarObject",py::module_local())
            .def(py::init<>())
            .def_property("color",STRING_PROPERTY(NvDsCarObject,color))
            .def_property("region",STRING_PROPERTY(NvDsCarObject,region))
            .def_property("license",STRING_PROPERTY(NvDsCarObject,license))
            .def_readwrite("lprnet_confidence",&NvDsCarObject::lprnet_confidence)
            .def_readwrite("lpdnet_confidence",&NvDsCarObject::lpdnet_confidence)
            .def_readwrite("tcnet_confidence",&NvDsCarObject::tcnet_confidence)
            .def_readwrite("colornet_confidence",&NvDsCarObject::colornet_confidence)            
            .def_readwrite("car_bbox",&NvDsCarObject::car_bbox)            
            .def_readwrite("lpd_bbox",&NvDsCarObject::lpd_bbox)            
            
            .def("cast",[](void *data){
	    	return (NvDsCarObject*)data;
            },py::return_value_policy::reference)

            .def("cast",[](size_t data){
	    	return (NvDsCarObject*)data;
            },py::return_value_policy::reference);

        m.def("alloc_nvds_car_object",
              []() {
                  auto *object = (NvDsCarObject *) g_malloc0(
                          sizeof(NvDsCarObject));
                  return object;
              },
              py::return_value_policy::reference);
}
