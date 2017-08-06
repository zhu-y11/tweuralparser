CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

ADD_EXECUTABLE(dp-parser dp-parser.cc dict_map.hpp conll_reader.hpp)
target_link_libraries(dp-parser dynet ${LIBS})
if(UNIX AND NOT APPLE)
  target_link_libraries(dp-parser rt)
endif()
