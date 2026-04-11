from conan import ConanFile
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, cmake_layout, CMakeDeps, CMakeToolchain
from conan.tools.files import apply_conandata_patches, export_conandata_patches, copy, get, rmdir, save, load, collect_libs
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
    options = {
        "shared": [True, False],
        "build_python": [True, False],
    }

    default_options = {
        "shared": True,
        "build_python": False,
        "actor-zeta/*:cxx_standard": 20,
        "actor-zeta/*:fPIC": True,
        "actor-zeta/*:exceptions_disable": False,
        "actor-zeta/*:rtti_disable": False,
        "boost/*:header_only": True,
    }

    def export_sources(self):
        export_conandata_patches(self)

    def validate(self):
        check_min_cppstd(self, 20)

    def requirements(self):
        self.requires("boost/1.87.0", force=True)
        self.requires("fmt/11.1.3")
        self.requires("spdlog/1.15.1")
        if self.options.build_python:
            self.requires("pybind11/2.13.6")
        self.requires("msgpack-cxx/4.1.1")
        self.requires("catch2/2.13.7")
        self.requires("abseil/20230802.1")
        self.requires("benchmark/1.6.1")
        self.requires("zlib/1.3.1")
        self.requires("bzip2/1.0.8")
        self.requires("actor-zeta/1.1.1")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["CMAKE_CXX_STANDARD"] = "20"
        tc.variables["BUILD_PYTHON"] = bool(self.options.build_python)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        # C++ integration headers
        copy(self, "*.hpp", dst=os.path.join(self.package_folder, "include/otterbrix"),
             src=os.path.join(self.source_folder, "integration/cpp"))
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include/otterbrix"),
             src=os.path.join(self.source_folder, "integration/cpp"))
        # C integration headers
        copy(self, "*.h", dst=os.path.join(self.package_folder, "include/otterbrix/c"),
             src=os.path.join(self.source_folder, "integration/c"))
        # All project headers
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
            "msgpack-cxx::msgpack-cxx",
            "fmt::fmt", "spdlog::spdlog", "zlib::zlib", "bzip2::bzip2",
            "catch2::catch2", "benchmark::benchmark",
        ]

        if self.options.build_python:
            common_deps.append("pybind11::pybind11")

        # Core libraries
        for comp in [
            "otterbrix_assert", "otterbrix_b_plus_tree", "otterbrix_file",
            "otterbrix_locks", "otterbrix_string_heap",
        ]:
            c = self.cpp_info.components[comp]
            c.libs = [comp]
            c.requires = common_deps
            c.set_property("cmake_target_name", f"otterbrix::{comp}")

        # Component libraries
        for comp in [
            "otterbrix_catalog", "otterbrix_compute", "otterbrix_context",
            "otterbrix_cursor", "otterbrix_expressions", "otterbrix_index",
            "otterbrix_log", "otterbrix_logical_plan",
            "otterbrix_physical_plan", "otterbrix_physical_plan_generator",
            "otterbrix_planner", "otterbrix_serialization",
            "otterbrix_session", "otterbrix_sql", "otterbrix_table",
            "otterbrix_types", "otterbrix_vector",
        ]:
            c = self.cpp_info.components[comp]
            c.libs = [comp]
            c.requires = common_deps
            c.set_property("cmake_target_name", f"otterbrix::{comp}")

        # Interface-only components (no libs)
        for comp in ["otterbrix_configuration", "otterbrix_storage"]:
            c = self.cpp_info.components[comp]
            c.libs = []
            c.requires = common_deps
            c.set_property("cmake_target_name", f"otterbrix::{comp}")

        # Services library
        services = self.cpp_info.components["otterbrix_services"]
        services.libs = ["otterbrix_services"]
        services.requires = common_deps
        services.set_property("cmake_target_name", "otterbrix::services")

        # C++ wrapper library
        wrapper = self.cpp_info.components["otterbrix_cpp"]
        wrapper.libs = ["cpp_otterbrix"]
        wrapper.requires = ["otterbrix_services"] + common_deps
        wrapper.set_property("cmake_target_name", "otterbrix::cpp_otterbrix")

        # Aggregate (meta) component
        alias = self.cpp_info.components["otterbrix"]
        alias.libs = []
        alias.requires = [
            # core
            "otterbrix_assert", "otterbrix_b_plus_tree", "otterbrix_file",
            "otterbrix_locks", "otterbrix_string_heap",
            # components
            "otterbrix_catalog", "otterbrix_compute", "otterbrix_context",
            "otterbrix_cursor", "otterbrix_expressions", "otterbrix_index",
            "otterbrix_log", "otterbrix_logical_plan",
            "otterbrix_physical_plan", "otterbrix_physical_plan_generator",
            "otterbrix_planner", "otterbrix_serialization",
            "otterbrix_session", "otterbrix_sql", "otterbrix_table",
            "otterbrix_types", "otterbrix_vector",
            "otterbrix_configuration", "otterbrix_storage",
            # services & wrapper
            "otterbrix_services", "otterbrix_cpp",
        ]
        alias.set_property("cmake_target_name", "otterbrix::otterbrix")
