cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(otterbrix REQUIRED)

add_executable(test_package test.cpp)
target_compile_features(test_package PRIVATE cxx_std_20)
target_link_libraries(test_package PRIVATE otterbrix::otterbrix)

if(NOT COMMAND otterbrix_add_parser_extension)
    message(FATAL_ERROR "otterbrix_add_parser_extension() is not provided by find_package(otterbrix)")
endif()
