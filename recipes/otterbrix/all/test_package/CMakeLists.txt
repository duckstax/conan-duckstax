cmake_minimum_required(VERSION 3.15)
project(test_package LANGUAGES CXX)

find_package(Arrow REQUIRED)
find_package(absl REQUIRED)
find_package(BISON REQUIRED)
find_package(FLEX REQUIRED)
find_package(otterbrix REQUIRED)
find_package(Catch2 2.13.7 REQUIRED)
find_package(Boost 1.86.0 REQUIRED)
find_package(Boost REQUIRED COMPONENTS charconv)
find_package(Threads)

add_executable(test_package test.cpp)

target_link_libraries(test_package
    PRIVATE
    arrow::arrow
    Boost::charconv
    Boost::boost
    Threads::Threads
    OpenSSL::Crypto
    OpenSSL::SSL
    otterbrix::otterbrix
    Catch2::Catch2
    absl::flat_hash_map
    absl::node_hash_map
    msgpackc-cxx
)
