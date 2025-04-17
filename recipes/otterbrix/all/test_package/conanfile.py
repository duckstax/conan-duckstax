from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
import os

class OtterbrixTestConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    generators = "CMakeToolchain", "CMakeDeps"
    test_type = "explicit"

    def requirements(self):
        self.requires(self.tested_reference_str)

    def layout(self):
        cmake_layout(self)

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not self.conf.get("tools.build:skip_test", default=False):
            self.run(os.path.join(self.cpp.build.bindir, "test_package"), env="conanrun")
