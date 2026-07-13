from conan import ConanFile
from conan.tools.cmake import CMake, CMakeToolchain, CMakeDeps, cmake_layout
import os


class OtterbrixTestConan(ConanFile):
    settings = "os", "arch", "compiler", "build_type"
    test_type = "explicit"

    exports_sources = "CMakeLists.txt", "src/*", "include/*"

    def requirements(self):
        self.requires(self.tested_reference_str)
        self.requires("boost/1.88.0")
        self.requires("fmt/11.1.3")
        self.requires("spdlog/1.15.1")
        self.requires("catch2/3.15.2")
        self.requires("abseil/20260107.1")
        self.requires("benchmark/1.6.1")
        self.requires("zlib/1.3.1")
        self.requires("bzip2/1.0.8")
        self.requires("actor-zeta/1.2.0")
        self.requires("fast_float/8.1.0")

    def layout(self):
        cmake_layout(self)

    def generate(self):
        tc = CMakeToolchain(self)
        tc.generate()

        deps = CMakeDeps(self)
        deps.generate()

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def test(self):
        if not self.conf.get("tools.build:skip_test", default=False):
            self.run(os.path.join(self.cpp.build.bindir, "test_package"), env="conanrun")
