from conans import ConanFile, tools
import os


class CxxOptsConan(ConanFile):
    name = "cxxopts"
    version = "2.2.0"
    description = "Lightweight C++ command line option parser"
    topics = ("conan", "cxxopts", "command line")
    url = "https://github.com/cyberduckninja/conan-cxxopts"
    homepage = "https://github.com/jarro2783/cxxopts/"
    license = "MIT"
    no_copy_source = True
    options = {
        "cxxopts_use_unicode": [True, False],
        "cxxopts_has_optional": [True, False],
        "cxxopts_no_rtti": [True, False],
        "cxxopts_no_exceptions": [True, False],
        "cxxopts_vector_delimiter": [True, False]
    }

    default_options = {
        "cxxopts_use_unicode": False,
        "cxxopts_has_optional": False,
        "cxxopts_no_rtti": False,
        "cxxopts_no_exceptions": True,
        "cxxopts_vector_delimiter": True
    }

    _source_subfolder = "source_subfolder"

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        extracted_dir = self.name + "-" + self.version
        os.rename(extracted_dir, self._source_subfolder)

    def package_info(self):
        self.cpp_info.defines = []

        if self.options.cxxopts_use_unicode:
            self.cpp_info.defines.append("CXXOPTS_USE_UNICODE")

        if self.options.cxxopts_has_optional:
            self.cpp_info.defines.append("CXXOPTS_HAS_OPTIONAL")

        if self.options.cxxopts_no_rtti:
            self.cpp_info.defines.append("CXXOPTS_NO_RTTI")

        if not self.options.cxxopts_no_exceptions:
            self.cpp_info.defines.append("CXXOPTS_NO_EXCEPTIONS")

        if not self.options.cxxopts_vector_delimiter:
            self.cpp_info.defines.append("CXXOPTS_VECTOR_DELIMITER")

    def package(self):
        include_folder = os.path.join(self._source_subfolder, "include")
        self.copy(pattern="LICENSE", dst="licenses", src=self._source_subfolder)
        self.copy(pattern="*", dst="include", src=include_folder)

    def package_id(self):
        self.info.header_only()
