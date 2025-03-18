from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout
import os


class Otterbrix(ConanFile):
    name = "otterbrix"
    version = "1.0"
    description = "otterbrix is an open-source framework for developing conventional and analytical applications."
    url = "https://github.com/duckstax/otterbrix"
    homepage = "https://github.com/duckstax/otterbrix"
    author = "kotbegemot <k0tb9g9m0t@gmail.com>"
    license = "MIT"
    exports = ["LICENSE.md"]
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

    def list_all_files(self, directory):
        """Показывает все файлы и директории рекурсивно"""
        self.output.info(f"Директория: {directory}")

        try:
            # Получаем списки файлов и директорий
            items = os.listdir(directory)

            files = [f for f in items if os.path.isfile(os.path.join(directory, f))]
            dirs = [d for d in items if os.path.isdir(os.path.join(directory, d))]

            # Печатаем файлы
            if files:
                self.output.info("  Файлы:")
                for file in sorted(files):
                    self.output.info(f"    - {file}")
            else:
                self.output.info("  Файлов нет")

            # Печатаем директории
            if dirs:
                self.output.info("  Директории:")
                for dir_name in sorted(dirs):
                    self.output.info(f"    - {dir_name}")
            else:
                self.output.info("  Директорий нет")

            # Рекурсивно обрабатываем поддиректории
            for dir_name in sorted(dirs):
                if dir_name not in ['.git', 'build', '__pycache__', 'venv']:  # Игнорируем некоторые директории
                    self.output.info("\n")
                    sub_dir = os.path.join(directory, dir_name)
                    self.list_all_files(sub_dir)

        except Exception as e:
            self.output.error(f"Ошибка при чтении директории {directory}: {e}")

    @property
    def _minimum_cpp_standard(self):
        return 17

    def source(self):
        # Вызываем функцию вывода файлов перед началом сборки
        self.output.info("=== СПИСОК ВСЕХ ФАЙЛОВ В ПРОЕКТЕ ===")
        self.list_all_files(os.getcwd())
        self.output.info("=== КОНЕЦ СПИСКА ФАЙЛОВ ===")

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
        self.requires("actor-zeta/1.0.0a11@duckstax/stable")

    def build(self):
        # Проверяем наличие CMakeLists.txt перед началом сборки
        if not os.path.exists("CMakeLists.txt"):
            self.output.error("ОШИБКА: CMakeLists.txt не найден в текущей директории!")
            # Поиск CMakeLists.txt в других директориях
            found_cmakelist = False
            for root, dirs, files in os.walk(os.getcwd()):
                if "CMakeLists.txt" in files:
                    rel_path = os.path.relpath(root, os.getcwd())
                    self.output.info(f"CMakeLists.txt найден в: {rel_path}")
                    found_cmakelist = True

            if not found_cmakelist:
                self.output.error("CMakeLists.txt не найден нигде в проекте!")

        cmake = CMake(self)
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
