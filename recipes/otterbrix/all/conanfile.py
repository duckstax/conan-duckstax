from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout


class Otterbrix(ConanFile):
    name = "otterbrix"
    license = "MIT"
    description = "Otterbrix: computation framework for Semi-structured data processing"
    url = "https://github.com/duckstax/otterbrix"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}  # Enable shared/static options
    generators = "CMakeDeps", "CMakeToolchain"
    exports_sources = "CMakeLists.txt", "components/*", "core/*", "integration/*", "services/*", "LICENSE", "cmake/*"

    default_options = {
        "shared": True,
        "actor-zeta:cxx_standard": 17,
        "actor-zeta:fPIC": True,
        "actor-zeta:exceptions_disable": False,
        "actor-zeta:rtti_disable": False,
    }

    @property
    def _minimum_cpp_standard(self):
        return 17

    def layout(self):
        cmake_layout(self)

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
        self.requires("actor-zeta/1.0.0a11@")

    def build(self):
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        self.copy("*.hpp", dst="include/otterbrix", src="integration/cpp")
        self.copy("*.hpp", dst="include", src=".")
        self.copy("*.dll", dst="bin", keep_path=False)  # Windows shared library
        self.copy("*.so", dst="lib", keep_path=False)  # Linux shared library
        self.copy("*.dylib", dst="lib", keep_path=False)  # macOS shared library
        self.copy("*.a", dst="lib", keep_path=False)  # Static library (if needed)

    def package_info(self):
        self.cpp_info.components["cpp_otterbrix"].libs = ["cpp_otterbrix"]
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_document")
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_cursor")
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_ql")
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_session")
        # self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_expressions")
        self.cpp_info.components["cpp_otterbrix"].requires.append("boost::boost")
        self.cpp_info.components["cpp_otterbrix"].requires.append("abseil::abseil")
        self.cpp_info.components["cpp_otterbrix"].requires.append("actor-zeta::actor-zeta")
        self.cpp_info.components["cpp_otterbrix"].requires.append("magic_enum::magic_enum")
        self.cpp_info.components["cpp_otterbrix"].requires.append("msgpack-cxx::msgpack-cxx")
        self.cpp_info.components["cpp_otterbrix"].requires.append("fmt::fmt")
        self.cpp_info.components["cpp_otterbrix"].requires.append("spdlog::spdlog")
        self.cpp_info.components["cpp_otterbrix"].requires.append("crc32c::crc32c")
        self.cpp_info.components["cpp_otterbrix"].requires.append("zlib::zlib")
        self.cpp_info.components["cpp_otterbrix"].requires.append("bzip2::bzip2")

        self.cpp_info.components["otterbrix_document"].libs = ["otterbrix_document"]
        self.cpp_info.components["otterbrix_cursor"].libs = ["otterbrix_cursor"]
        self.cpp_info.components["otterbrix_ql"].libs = ["otterbrix_ql"]
        self.cpp_info.components["otterbrix_session"].libs = ["otterbrix_session"]
        self.cpp_info.components["otterbrix_expressions"].libs = ["otterbrix_expressions"]

        self.cpp_info.includedirs = ["include"]
