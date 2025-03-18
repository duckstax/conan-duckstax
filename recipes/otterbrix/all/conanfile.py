from conans import ConanFile, tools
import os


class OtterbrixRecipe(ConanFile):
    name = "otterbrix"
    version = "1.0.0a10-rc"
    license = "MIT"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = {"shared": True}
    generators = "CMakeToolchain", "cmake", "cmake_find_package", "cmake_paths"
    exports_sources = "CMakeLists.txt", "components/*", "core/*", "integration/*", "services/*", "LICENSE", "cmake/*"

    def requirements(self):
        self.requires("boost/1.86.0@")
        self.requires("fmt/10.2.1@")
        self.requires("spdlog/1.12.0@")
        self.requires("pybind11/2.10.0@")
        self.requires("msgpack-cxx/4.1.1@")
        self.requires("catch2/2.13.7@")
        self.requires("crc32c/1.1.2@")
        self.requires("abseil/20230802.1@")
        self.requires("benchmark/1.6.1@")
        self.requires("zlib/1.2.12@")
        self.requires("bzip2/1.0.8@")
        self.requires("magic_enum/0.8.1@")
        self.requires("actor-zeta/1.0.0a11@duckstax/stable")

    def build(self):
        toolchain_path = os.path.join(self.build_folder, "conan_toolchain.cmake")
        if not os.path.exists(toolchain_path):
            raise Exception("conan_toolchain.cmake not found")

        cmake = tools.CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        cmake = tools.CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["otterbrix_document", "otterbrix_types", "otterbrix_cursor",
                              "otterbrix_session", "otterbrix_expressions", "otterbrix_logical_plan",
                              "cpp_otterbrix"]
