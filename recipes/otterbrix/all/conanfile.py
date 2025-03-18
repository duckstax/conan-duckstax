from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout


class OtterbrixConan(ConanFile):
    name = "otterbrix"
    version = "1.0"
    description = "otterbrix is an open-source framework for developing conventional and analytical applications."
    url = "https://github.com/duckstax/otterbrix"
    homepage = "https://github.com/duckstax/otterbrix"
    author = "kotbegemot <k0tb9g9m0t@gmail.com>"
    license = "MIT"

    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = {
        "shared": True,
        "actor-zeta:cxx_standard": 17,
        "actor-zeta:fPIC": True,
        "actor-zeta:exceptions_disable": False,
        "actor-zeta:rtti_disable": False,
    }

    generators = "CMakeToolchain", "CMakeDeps"
    exports_sources = "CMakeLists.txt", "components/*", "core/*", "integration/*", "services/*", "LICENSE", "cmake/*"

    def layout(self):
        cmake_layout(self, src_folder=".")

    def requirements(self):
        self.requires("boost/1.86.0")
        self.requires("fmt/10.2.1")
        self.requires("spdlog/1.12.0")
        self.requires("pybind11/2.10.0")
        self.requires("msgpack-cxx/4.1.1")
        self.requires("catch2/2.13.7")
        self.requires("crc32c/1.1.2")
        self.requires("abseil/20230802.1")
        self.requires("benchmark/1.6.1")
        self.requires("zlib/1.2.12")
        self.requires("bzip2/1.0.8")
        self.requires("magic_enum/0.8.1")
        self.requires("actor-zeta/1.0.0a11@duckstax/stable")

    def build(self):
        cmake = CMake(self)
        cmake.configure(source_folder=self.source_folder)
        cmake.build()

    def package(self):
        self.copy("*.hpp", dst="include/otterbrix", src="integration/cpp")
        self.copy("*.h", dst="include/otterbrix", src="integration/cpp")
        self.copy("*.hpp", dst="include", src=".")
        self.copy("*.h", dst="include", src=".")
        self.copy("*.dll", dst="bin", keep_path=False)
        self.copy("*.so", dst="lib", keep_path=False)
        self.copy("*.dylib", dst="lib", keep_path=False)
        self.copy("*.a", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.components["cpp_otterbrix"].libs = ["cpp_otterbrix"]
        self.cpp_info.components["cpp_otterbrix"].requires = [
            "otterbrix_document",
            "otterbrix_types",
            "otterbrix_cursor",
            "otterbrix_session",
            "otterbrix_expressions",
            "otterbrix_logical_plan",
            "otterbrix_sql",
            "boost::boost",
            "abseil::abseil",
            "actor-zeta::actor-zeta",
            "magic_enum::magic_enum",
            "msgpack-cxx::msgpack-cxx",
            "fmt::fmt",
            "spdlog::spdlog",
            "crc32c::crc32c",
            "zlib::zlib",
            "bzip2::bzip2"
        ]

        self.cpp_info.components["otterbrix_document"].libs = ["otterbrix_document"]
        self.cpp_info.components["otterbrix_types"].libs = ["otterbrix_types"]
        self.cpp_info.components["otterbrix_cursor"].libs = ["otterbrix_cursor"]
        self.cpp_info.components["otterbrix_session"].libs = ["otterbrix_session"]
        self.cpp_info.components["otterbrix_expressions"].libs = ["otterbrix_expressions"]
        self.cpp_info.components["otterbrix_logical_plan"].libs = ["otterbrix_logical_plan"]
        self.cpp_info.components["otterbrix_sql"].libs = ["otterbrix_sql"]

        self.cpp_info.includedirs = ["include"]
