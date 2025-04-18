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
        self.requires("boost/1.86.0", force=True)
        self.requires("fmt/11.1.3")
        self.requires("spdlog/1.15.1")
        self.requires("pybind11/2.10.0")
        self.requires("msgpack-cxx/4.1.1")
        self.requires("catch2/2.13.7")
        self.requires("abseil/20230802.1")
        self.requires("benchmark/1.6.1")
        self.requires("zlib/1.2.12")
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
        copy(self,"*.hpp", dst=os.path.join(self.package_folder, "include/otterbrix"), src=os.path.join(self.source_folder, "integration/cpp"))
        copy(self,"*.h", dst=os.path.join(self.package_folder, "include/otterbrix"), src=os.path.join(self.source_folder, "integration/cpp"))
        copy(self, "*.hpp", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include"), src=self.source_folder)

        copy(self, "*.dll", src=self.build_folder, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        copy(self, "*.lib", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.a", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.so*", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.dylib", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)

        for f in glob(os.path.join(self.package_folder, "lib", "otterbrix.cpython-*.so")):
            os.remove(f)

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "otterbrix")
        self.cpp_info.set_property("cmake_target_name", "otterbrix::otterbrix")

        self.cpp_info.libs = collect_libs(self)
        self.cpp_info.includedirs = ["include"]
        self.cpp_info.libdirs = ["lib"]
        self.cpp_info.requires = []
        self.cpp_info.requires.append("boost::boost")
        self.cpp_info.requires.append("abseil::abseil")
        self.cpp_info.requires.append("actor-zeta::actor-zeta")
        self.cpp_info.requires.append("magic_enum::magic_enum")
        self.cpp_info.requires.append("msgpack-cxx::msgpack-cxx")
        self.cpp_info.requires.append("fmt::fmt")
        self.cpp_info.requires.append("spdlog::spdlog")
        self.cpp_info.requires.append("zlib::zlib")
        self.cpp_info.requires.append("bzip2::bzip2")
        # TODO: recheck usage by the component
        self.cpp_info.requires.append("pybind11::pybind11")
        self.cpp_info.requires.append("catch2::catch2")
        self.cpp_info.requires.append("benchmark::benchmark")
        self.cpp_info.includedirs = ["include"]

        #self.cpp_info.components["otterbrix"].requires.append("otterbrix_document")
        #self.cpp_info.components["otterbrix"].requires.append("otterbrix_types")
        #self.cpp_info.components["otterbrix"].requires.append("otterbrix_cursor")
        #self.cpp_info.components["otterbrix"].requires.append("otterbrix_session")
        #self.cpp_info.components["otterbrix"].requires.append("otterbrix_expressions")
        #self.cpp_info.components["otterbrix"].requires.append("otterbrix_sql")
        #self.cpp_info.components["otterbrix"].requires.append("otterbrix_logical_plan")
        #self.cpp_info.components["otterbrix"].requires.append("boost::boost")
        #self.cpp_info.components["otterbrix"].requires.append("abseil::abseil")
        #self.cpp_info.components["otterbrix"].requires.append("actor-zeta::actor-zeta")
        #self.cpp_info.components["otterbrix"].requires.append("magic_enum::magic_enum")
        #self.cpp_info.components["otterbrix"].requires.append("msgpack-cxx::msgpack-cxx")
        #self.cpp_info.components["otterbrix"].requires.append("fmt::fmt")
        #self.cpp_info.components["otterbrix"].requires.append("spdlog::spdlog")
        #self.cpp_info.components["otterbrix"].requires.append("zlib::zlib")
        #self.cpp_info.components["otterbrix"].requires.append("bzip2::bzip2")
        # TODO: recheck usage by the component
        #self.cpp_info.components["otterbrix"].requires.append("pybind11::pybind11")
        #self.cpp_info.components["otterbrix"].requires.append("catch2::catch2")
        #self.cpp_info.components["otterbrix"].requires.append("benchmark::benchmark")

        #self.cpp_info.components["otterbrix_document"].libs = ["otterbrix_document"]
        #self.cpp_info.components["otterbrix_types"].libs = ["otterbrix_types"]
        #self.cpp_info.components["otterbrix_cursor"].libs = ["otterbrix_cursor"]
        #self.cpp_info.components["otterbrix_session"].libs = ["otterbrix_session"]
        #self.cpp_info.components["otterbrix_expressions"].libs = ["otterbrix_expressions"]
        #self.cpp_info.components["otterbrix_sql"].libs = ["otterbrix_sql"]
        #self.cpp_info.components["otterbrix_logical_plan"].libs = ["otterbrix_logical_plan"]

        #self.cpp_info.includedirs = ["include"]
