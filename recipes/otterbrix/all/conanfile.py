from conans import ConanFile, CMake, tools
import os


class OtterbrixRecipe(ConanFile):
    name = "otterbrix"
    version = "1.0.0a10-rc"
    description = "otterbrix is an open-source framework for developing conventional and analytical applications."
    license = "MIT"
    settings = "os", "compiler", "build_type", "arch"
    options = {"shared": [True, False]}
    default_options = {"shared": True}
    # Используем все возможные генераторы для Conan v1
    generators = "cmake", "cmake_find_package", "cmake_paths", "cmake_multi"
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
        # Ищем готовый conan_toolchain.cmake
        toolchain_path = None
        possible_paths = [
            os.path.join(self.build_folder, "conan_toolchain.cmake"),
            os.path.join(self.build_folder, "generators", "conan_toolchain.cmake"),
            os.path.join(self.source_folder, "conan_toolchain.cmake"),
            "conan_toolchain.cmake"
        ]

        for path in possible_paths:
            if os.path.exists(path):
                toolchain_path = path
                self.output.info(f"Found toolchain file at: {path}")
                break

        # Если toolchain не найден, ищем другие подходящие файлы
        if not toolchain_path:
            alternative_files = [
                os.path.join(self.build_folder, "conanbuildinfo.cmake"),
                os.path.join(self.build_folder, "conan_paths.cmake")
            ]

            for alt_file in alternative_files:
                if os.path.exists(alt_file):
                    self.output.info(f"Found alternative cmake file: {alt_file}")
                    toolchain_path = alt_file
                    break

        # Если ни один файл не найден, завершаем с ошибкой
        if not toolchain_path:
            self.output.error("No suitable CMake configuration file found!")
            raise Exception("A CMake configuration file is required for building otterbrix")

        # Запускаем CMake с указанием найденного файла
        cmake = CMake(self)

        if "toolchain" in toolchain_path:
            cmake.definitions["CMAKE_TOOLCHAIN_FILE"] = toolchain_path
        elif "buildinfo" in toolchain_path:
            # Для файла conanbuildinfo.cmake используем другой подход
            self.output.info("Using conanbuildinfo.cmake approach")
            cmake.definitions["CMAKE_PROJECT_otterbrix_INCLUDE"] = toolchain_path
        elif "paths" in toolchain_path:
            # Для файла conan_paths.cmake используем другой подход
            self.output.info("Using conan_paths.cmake approach")
            cmake.definitions["CMAKE_PREFIX_PATH"] = os.path.dirname(toolchain_path)

        cmake.configure()
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.components["cpp_otterbrix"].libs = ["cpp_otterbrix"]
        # Добавляем компоненты
        components = ["otterbrix_document", "otterbrix_types", "otterbrix_cursor",
                      "otterbrix_session", "otterbrix_expressions", "otterbrix_logical_plan"]

        for comp in components:
            self.cpp_info.components["cpp_otterbrix"].requires.append(comp)
            self.cpp_info.components[comp].libs = [comp]

        # Добавляем внешние зависимости
        ext_deps = ["boost::boost", "abseil::abseil", "actor-zeta::actor-zeta",
                    "magic_enum::magic_enum", "msgpack-cxx::msgpack-cxx", "fmt::fmt",
                    "spdlog::spdlog", "crc32c::crc32c", "zlib::zlib", "bzip2::bzip2"]

        for dep in ext_deps:
            self.cpp_info.components["cpp_otterbrix"].requires.append(dep)

        self.cpp_info.includedirs = ["include"]
