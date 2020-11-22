from conans import ConanFile, tools, CMake
import os


class RedisPlusPlusConan(ConanFile):
    name = "redis-plus-plus"
    version = "1.2.1"
    description = "This is a C++ client for Redis. It's based on hiredis, and written in C++ 11 / C++ 17."
    topics = ("conan", "url", "parser")
    url = "https://github.com/sewenew/redis-plus-plus"
    homepage = "https://github.com/sewenew/redis-plus-plus"
    license = "Apache-2.0 License"
    exports = ["LICENSE"]
    exports_sources = ["CMakeLists.txt"]
    generators = "cmake"
    build_policy = "missing"
    _cmake = None

    _source_subfolder = "source_subfolder"

    requires = (
        "hiredis/v1.0.0@cyberduckninja/stable"
    )

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)
        tools.replace_in_file(self._source_subfolder + "/CMakeLists.txt", "find_path(HIREDIS_HEADER hiredis)", "")
        tools.replace_in_file(self._source_subfolder + "/CMakeLists.txt", "find_library(HIREDIS_LIB hiredis)", "")
        tools.replace_in_file(
            self._source_subfolder + "/CMakeLists.txt",
            "option(REDIS_PLUS_PLUS_BUILD_TEST \"Build tests for redis++\" ON)",
            "option(REDIS_PLUS_PLUS_BUILD_TEST \"Build tests for redis++\" OFF)"
        )

        #tools.replace_in_file(
        #    self._source_subfolder + "/CMakeLists.txt",
        #    "target_include_directories(${STATIC_LIB} PUBLIC ${HIREDIS_HEADER})",
        #    "target_include_directories(${STATIC_LIB} PUBLIC ${CONAN_INCLUDE_DIRS})"
        #)

        tools.replace_in_file(
            self._source_subfolder + "/CMakeLists.txt",
            "option(REDIS_PLUS_PLUS_BUILD_SHARED \"Build shared library\" ON)",
            "option(REDIS_PLUS_PLUS_BUILD_SHARED \"Build shared library\" OFF)"
        )

        tools.replace_in_file(
            self._source_subfolder + "/CMakeLists.txt",
            "target_include_directories(${STATIC_LIB} PUBLIC ${HIREDIS_HEADER})",
            "target_link_libraries(${STATIC_LIB} PUBLIC ${CONAN_LIBS})"
        )

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
        if self.settings.os == "Linux":
            self.cpp_info.libs.append("pthread")

        self.cpp_info.libs = tools.collect_libs(self)
