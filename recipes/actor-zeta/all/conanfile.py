from conans import ConanFile, CMake, tools
import os


class ActorZetaConan(ConanFile):
    name = "actor-zeta"
    version = "1.0.0a5"
    description = "actor-zeta is an open source C++ virtual actor model implementation featuring lightweight & fast and more."
    url = "https://github.com/cyberduckninja/actor-zeta"
    homepage = "https://github.com/cyberduckninja/actor-zeta"
    author = "kotbegemot <aa.borgardt@yandex.ru>"
    license = "MIT"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    build_policy = "missing"
    _cmake = None

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "exceptions_disable": [True, False],
        "rtti_disable": [True, False],
        "cxx_standard": [11, 14, 17]
    }

    default_options = {
        "exceptions_disable": False,
        "rtti_disable": False,
        "shared": False,
        "fPIC": False,
        "cxx_standard": 11
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

    def _configure_cmake(self):
        if not self._cmake:
            self._cmake = CMake(self)
            self._cmake.definitions["EXCEPTIONS_DISABLE"] = self.options.exceptions_disable
            self._cmake.definitions["RTTI_DISABLE"] = self.options.rtti_disable
            self._cmake.definitions["SHARED"] = self.options.shared
            self._cmake.definitions["CMAKE_CXX_STANDARD"] = self.options.cxx_standard
            self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        include_folder = os.path.join(self._source_subfolder, "header/actor-zeta")
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        self.copy('*.hpp', dst='include/actor-zeta', src=include_folder)
        self.copy('*.ipp', dst='include/actor-zeta', src=include_folder)
        self.copy('*.hpp', dst='include/actor-zeta', src=os.path.join(self._source_subfolder, "header"))
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("pthread")
        self.cpp_info.libs = tools.collect_libs(self)
