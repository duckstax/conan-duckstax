from conan.tools.gnu import Autotools
from conans import ConanFile, tools

import shutil


class QuickJS(ConanFile):
    name = 'quickjs'
    description = 'QuickJS Javascript Engine'
    homepage = 'https://github.com/bellard/quickjs.git'

    @property
    def url(self):
        return self.homepage

    license = 'MIT'
    author = 'Sergey Sherkunov <me@sanerdsher.xyz>'
    topics = ('js')
    settings = 'os', 'compiler', 'build_type', 'arch'
    generators = 'AutotoolsToolchain'
    _source_subfolder = 'source_subfolder'

    def export_sources(self):
        for patch in self.conan_data.get('patches', {}).get(self.version, []):
            self.copy(patch['patch_file'])

        for file in self.conan_data.get('files', {}).get(self.version, []):
            self.copy(file['src'])

    def layout(self):
        self.folders.source = self._source_subfolder
        self.folders.build = self._source_subfolder

    def source(self):
        tools.get(**self.conan_data['sources'][self.version], strip_root=True)

        with tools.chdir('..'):
            for patch in self.conan_data.get('patches', {}).get(self.version, []):
                tools.patch(**patch)

            for file in self.conan_data.get('files', {}).get(self.version, []):
                shutil.copy(**file)

    def build(self):
        autotools = Autotools(self)

        autotools.make(target=f'libquickjs.a')

    def package(self):
        self.copy('LICENSE')
        self.copy('quickjs.h', dst=f'include')
        self.copy('quickjs-libc.h', dst=f'include')
        self.copy('*.lib', dst='lib', keep_path=False)
        self.copy('*.dll', dst='bin', keep_path=False)
        self.copy('*.a', dst='lib', keep_path=False)
        self.copy('*.lo', dst='lib', keep_path=False)
        self.copy('*.dylib', dst='lib', keep_path=False)
        self.copy('*.so', dst='lib', keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
