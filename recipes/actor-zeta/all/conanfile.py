from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, cmake_layout
from conan.tools.files import apply_conandata_patches, export_conandata_patches, get, copy
import os


class ActorZetaConan(ConanFile):
    name = "actor-zeta"
    description = "actor-zeta is an open source C++ virtual actor model implementation featuring lightweight & fast and more."
    url = "https://github.com/duckstax/actor-zeta"
    homepage = "https://github.com/duckstax/actor-zeta"
    author = "kotbegemot <k0tb9g9m0t@gmail.com>"
    license = "MIT"
    package_type = "library"

    settings = "os", "arch", "compiler", "build_type"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "exceptions_disable": [True, False],
        "rtti_disable": [True, False],
        "cxx_standard": [11, 14, 17]
    }

    default_options = {
        "shared": False,
        "fPIC": False,
        "exceptions_disable": False,
        "rtti_disable": False,
        "cxx_standard": 11
    }

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            self.options.rm_safe("fPIC")

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self)

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        apply_conandata_patches(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

        cmake = CMake(self)
        cmake.configure()

    def build(self):
        cmake = CMake(self)
        cmake.build()

    def package(self):
        copy(self, "LICENSE*", src=self.source_folder, dst=os.path.join(self.package_folder, "licenses"))

        # Copy header files
        include_folder = os.path.join(self.source_folder, "header/actor-zeta")
        copy(self, "actor-zeta.hpp", src=os.path.join(self.source_folder, "header"), dst=os.path.join(self.package_folder, "include"))
        copy(self, "*.hpp", src=include_folder, dst=os.path.join(self.package_folder, "include/actor-zeta"))
        copy(self, "*.ipp", src=include_folder, dst=os.path.join(self.package_folder, "include/actor-zeta"))

        # Copy libraries
        copy(self, "*.dll", src=self.build_folder, dst=os.path.join(self.package_folder, "bin"), keep_path=False)
        copy(self, "*.lib", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.a", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.so*", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)
        copy(self, "*.dylib", src=self.build_folder, dst=os.path.join(self.package_folder, "lib"), keep_path=False)

    def package_info(self):
        self.cpp_info.libs = self.collect_libs()

        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("pthread")
