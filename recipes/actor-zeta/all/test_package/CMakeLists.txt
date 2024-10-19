cmake_minimum_required(VERSION 3.15)
project(test_package)

set(CMAKE_VERBOSE_MAKEFILE TRUE)
set(CMAKE_CXX_STANDARD 11 CACHE STRING "The C++ standard whose features are requested.")

#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-rtti")
#set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -fno-exceptions")

include(${CMAKE_BINARY_DIR}/conanbuildinfo.cmake)
conan_basic_setup()

add_executable(${PROJECT_NAME} test_package.cpp)

target_link_libraries(
    ${PROJECT_NAME}
    PRIVATE
    ${CONAN_LIBS}
)
