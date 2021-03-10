from conans import ConanFile, CMake, tools
import os


class GoblinEngineerConan(ConanFile):
    name = "goblin-engineer"
    version = "1.0.0a4"
    description = "Keep it short"
    topics = ("conan", "libname", "logging")
    url = "https://github.com/cyberduckninja/goblin-engineer"
    homepage = "https://github.com/cyberduckninja/goblin-engineer"
    author = "kotbegemot <aa.borgardt@yandex.ru>"
    license = "MIT"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    build_policy = "missing"
    _cmake = None

    settings = "os", "arch", "compiler", "build_type"

    options = {
        "boost_no_deprecated": [True, False],
        # "shared": [True, False],
        # "fPIC": [True, False],
        "http_component": [True, False],
        "cxx_standard": [14, 17]
    }

    default_options = {
        "boost_no_deprecated": False,
        # "shared": False,
        # "fPIC": False,
        "http_component": False,
        "cxx_standard": 14
    }

    _source_subfolder = "source_subfolder"
    _build_subfolder = "build_subfolder"

    requires = (
        "boost/1.75.0",
        "actor-zeta/1.0.0a5@cyberduckninja/stable"
    )

    def config_options(self):
        if self.settings.os == 'Windows':
            del self.options.fPIC

        if self.options.boost_no_deprecated:
            self.options["boost"].error_code_header_only = True
            self.options["boost"].system_no_deprecated = True
            self.options["boost"].asio_no_deprecated = True
            self.options["boost"].filesystem_no_deprecated = True

        self.options["actor-zeta"].exceptions_disable = False
        self.options["actor-zeta"].rtti_disable = False

        if self.options.cxx_standard == 17:
            self.options["actor-zeta"].cxx_standard = self.options.cxx_standard

        # if self.options.shared:
        #    self.options["actor-zeta"].SHARED = True

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def _configure_cmake(self):
        if not self._cmake:
            self._cmake = CMake(self)
            self._cmake.configure(source_dir=self._source_subfolder)
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        self.copy(pattern="LICENSE.md", dst="licenses", src=self._source_subfolder)
        include_folder = os.path.join(self._source_subfolder, "header")
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
