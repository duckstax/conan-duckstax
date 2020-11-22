from conans import ConanFile, tools, CMake
import os


class HiredisConan(ConanFile):
    name = "hiredis"
    version = "v1.0.0"
    description = "Hiredis is a minimalistic C client library for the Redis database"
    topics = ("conan", "url", "parser")
    url = "https://github.com/redis/hiredis/tree/v1.0.0"
    homepage = "https://github.com/redis/hiredis/tree/v1.0.0"
    license = "BSD 3-clause New or Revised License"
    exports = ["LICENSE"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    build_policy = "missing"
    _cmake = None

    _source_subfolder = "source_subfolder"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + "1.0.0"
        os.rename(extracted_dir, self._source_subfolder)

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
        adapters_folder = os.path.join(self._source_subfolder, "adapters")
        include_folder = self._source_subfolder
        self.copy(pattern="COPYING", dst="licenses", src=self._source_subfolder)
        self.copy(pattern="*.h", dst="include/hiredis", src=include_folder)
        self.copy(pattern="*.h", dst="include/hiredis/adapters", src=adapters_folder)
        self.copy(pattern="*.dll", dst="bin", keep_path=False)
        self.copy(pattern="*.lib", dst="lib", keep_path=False)
        self.copy(pattern="*.a", dst="lib", keep_path=False)
        self.copy(pattern="*.so*", dst="lib", keep_path=False)
        self.copy(pattern="*.dylib", dst="lib", keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
