from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout, CMakeDeps, CMakeToolchain
from conan.tools.files import copy, get, rmdir, save, load


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
        self.requires("boost/1.86.0", override=True)
        self.requires("fmt/11.1.3@", override=True)
        self.requires("spdlog/1.15.1@", override=True)
        self.requires("pybind11/2.10.0@", override=True)
        self.requires("msgpack-cxx/4.1.1@", override=True)
        self.requires("catch2/2.13.7@", override=True)
        self.requires("abseil/20230802.1@", override=True)
        self.requires("benchmark/1.6.1@", override=True)
        self.requires("zlib/1.2.12@", override=True)
        self.requires("bzip2/1.0.8@", override=True)
        self.requires("magic_enum/0.8.1@", override=True)
        self.requires("actor-zeta/1.0.0a12@", override=True)

    def layout(self):
        cmake_layout(self, src_folder="src")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)

    def generate(self):
        # Создаем и генерируем зависимости CMake
        deps = CMakeDeps(self)
        # Общие настройки для всех зависимостей
        for dep in self.dependencies.values():
            # Устанавливаем режим поиска both для всех зависимостей
            deps.set_property(dep.ref.name, "cmake_find_mode", "both")
        deps.generate()

        # Создаем и генерируем CMake toolchain
        tc = CMakeToolchain(self)
        # Предпочитаем CONFIG режим поиска пакетов
        tc.variables["CMAKE_FIND_PACKAGE_PREFER_CONFIG"] = "ON"
        # Включаем поиск в папке build
        tc.variables["CMAKE_FIND_USE_PACKAGE_ROOT_PATH"] = "ON"
        tc.variables["CMAKE_FIND_USE_CMAKE_PATH"] = "ON"
        tc.variables["CMAKE_FIND_USE_CMAKE_ENVIRONMENT_PATH"] = "ON"
        tc.generate()

    def build(self):
        cmake = CMake(self)
        # Добавляем переменную, указывающую на пакеты Conan
        cmake.definitions["CMAKE_PREFIX_PATH"] = self.build_folder
        cmake.configure()
        cmake.build()

    def package(self):
        self.copy("*.hpp", dst="include/otterbrix", src="integration/cpp")
        self.copy("*.h", dst="include/otterbrix", src="integration/cpp")
        self.copy("*.hpp", dst="include", src=".")
        self.copy("*.h", dst="include", src=".")
        self.copy("*.dll", dst="bin", keep_path=False)  # Windows shared library
        self.copy("*.so", dst="lib", keep_path=False)  # Linux shared library
        self.copy("*.dylib", dst="lib", keep_path=False)  # macOS shared library
        self.copy("*.a", dst="lib", keep_path=False)  # Static library (if needed)

    def package_info(self):
        self.cpp_info.components["cpp_otterbrix"].libs = ["cpp_otterbrix"]
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_document")
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_types")
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_cursor")
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_session")
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_expressions")
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_logical_plan")
        self.cpp_info.components["cpp_otterbrix"].requires.append("otterbrix_sql")
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
        self.cpp_info.components["otterbrix_types"].libs = ["otterbrix_types"]
        self.cpp_info.components["otterbrix_cursor"].libs = ["otterbrix_cursor"]
        self.cpp_info.components["otterbrix_session"].libs = ["otterbrix_session"]
        self.cpp_info.components["otterbrix_expressions"].libs = ["otterbrix_expressions"]
        self.cpp_info.components["otterbrix_logical_plan"].libs = ["otterbrix_logical_plan"]
        self.cpp_info.components["otterbrix_sql"].libs = ["otterbrix_sql"]

        self.cpp_info.includedirs = ["include"]
