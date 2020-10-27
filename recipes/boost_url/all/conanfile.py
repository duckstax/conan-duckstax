from conans import ConanFile, tools, CMake
import os


class BoostUrlConan(ConanFile):
    name = "boost-url"
    version = "alpha"
    description = "Lightweight fast C++ Url parser"
    topics = ("conan", "url", "parser")
    url = "https://github.com/CPPAlliance/url.git"
    homepage = "https://github.com/CPPAlliance/url.git"
    license = "BSL-1.0 License"
    exports = ["LICENSE.md"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    build_policy = "missing"
    _cmake = None

    _source_subfolder = "source_subfolder"

    requires = (
        "boost/1.71.0@conan/stable",
    )

    def source(self):
        git = tools.Git()
        git.clone(self.url, "master")
        tag = "tags/" + self.version
        git.checkout(tag)
        self._source_subfolder = git.folder

    def package_info(self):
        self.cpp_info.defines = []

    def _configure_cmake(self):
        if not self._cmake:
            self._cmake = CMake(self)
            self._cmake.configure(source_dir=self._source_subfolder)
        return self._cmake

    def build(self):
        cmake = self._configure_cmake()
        cmake.build()

    def package(self):
        include_folder = os.path.join(self._source_subfolder, "include")
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        self.copy(pattern="*", dst="include", src=include_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
