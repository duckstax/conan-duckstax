from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout, CMakeDeps, CMakeToolchain
from conan.tools.files import copy, get, rmdir, save, load, collect_libs
import os
from glob import glob


class Otterbrix(ConanFile):
    name = "otterbrix"
    description = "otterbrix is an open-source framework for developing conventional and analytical applications."
    url = "https://github.com/duckstax/otterbrix"
    homepage = "https://github.com/duckstax/otterbrix"
    author = "kotbegemot <k0tb9g9m0t@gmail.com>"
    license = "MIT"
    exports = ["LICENSE.md"]
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}  # Enable shared/static options

    default_options = {
        "shared": True,
        "actor-zeta/*:cxx_standard": 17,
        "actor-zeta/*:fPIC": True,
        "actor-zeta/*:exceptions_disable": False,
        "actor-zeta/*:rtti_disable": False,
    }

    def requirements(self):
        self.requires("boost/1.87.0", force=True)
        self.requires("fmt/11.1.3")
        self.requires("spdlog/1.15.1")
        self.requires("pybind11/2.10.0")
        self.requires("msgpack-cxx/4.1.1")
        self.requires("catch2/2.13.7")
        self.requires("abseil/20230802.1")
        self.requires("benchmark/1.6.1")
        self.requires("zlib/1.3.1")
        self.requires("bzip2/1.0.8")
        self.requires("magic_enum/0.8.1")
        self.requires("actor-zeta/1.0.0a12")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "*.hpp", dst=os.path.join(self.package_folder, "include/otterbrix"),
             src=os.path.join(self.source_folder, "integration/cpp"))
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include/otterbrix"),
             src=os.path.join(self.source_folder, "integration/cpp"))
        copy(self, "*.hpp", dst=os.path.join(self.package_folder,
                                             "include"), src=self.source_folder)
        copy(self, "*.h", dst=os.path.join(self.package_folder,
                                           "include"), src=self.source_folder)

        copy(self, "*.dll", src=self.build_folder,
             dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        copy(self, "*.lib", src=self.build_folder,
             dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.a", src=self.build_folder,
             dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.so*", src=self.build_folder,
             dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.dylib", src=self.build_folder,
             dst=os.path.join(self.package_folder, "lib"), keep_path=False)

        for f in glob(os.path.join(self.package_folder, "lib", "otterbrix.cpython-*.so")):
            os.remove(f)

    def package_info(self):
        # General properties
        self.cpp_info.set_property("cmake_file_name", "otterbrix")
        self.cpp_info.set_property("cmake_target_name", "otterbrix::otterbrix")
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libdirs = ["lib"]

        # External dependencies
        common_deps = [
            "boost::boost", "abseil::abseil", "actor-zeta::actor-zeta",
            "magic_enum::magic_enum", "msgpack-cxx::msgpack-cxx",
            "fmt::fmt", "spdlog::spdlog", "zlib::zlib", "bzip2::bzip2",
            "pybind11::pybind11", "catch2::catch2", "benchmark::benchmark",
        ]

        # Core C++ API library
        core = self.cpp_info.components["otterbrix_core"]
        core.libs = ["otterbrix"]
        core.requires = common_deps
        core.set_property("cmake_target_name", "otterbrix::core")

        # C++ wrapper library (this was missing!!!)
        wrapper = self.cpp_info.components["otterbrix_cpp"]
        wrapper.libs = ["cpp_otterbrix"]
        wrapper.requires = ["otterbrix_core"] + common_deps
        wrapper.set_property("cmake_target_name", "otterbrix::cpp_otterbrix")

        # Sub-libraries
        for comp in [
            "otterbrix_document", "otterbrix_types", "otterbrix_vector",
            "otterbrix_cursor", "otterbrix_session",  "otterbrix_expressions",
            "otterbrix_logical_plan", "otterbrix_sql", "otterbrix_serialization",
            "otterbrix_table", "otterbrix_catalog"
        ]:
            c = self.cpp_info.components[comp]
            c.libs = [comp]
            c.requires = ["otterbrix_cpp"] + common_deps
            c.set_property("cmake_target_name", f"otterbrix::{comp}")

        # Aggregate (meta) component
        alias = self.cpp_info.components["otterbrix"]
        alias.libs = []
        alias.requires = [
            "otterbrix_core", "otterbrix_cpp",
            "otterbrix_document", "otterbrix_types", "otterbrix_vector",
            "otterbrix_cursor", "otterbrix_session", "otterbrix_expressions",
            "otterbrix_logical_plan", "otterbrix_sql", "otterbrix_serialization",
            "otterbrix_table", "otterbrix_catalog"
        ]
        alias.set_property("cmake_target_name", "otterbrix::otterbrix")