from conan.tools.google import Bazel
from conans import ConanFile, tools

import shutil


class ProxyWASMCPPSDK(ConanFile):
    name = 'proxy-wasm-cpp-sdk'
    description = 'WebAssembly for Proxies (C++ SDK)'
    homepage = 'https://github.com/proxy-wasm/proxy-wasm-cpp-sdk.git'

    @property
    def url(self):
        return self.homepage

    license = 'Apache-2.0'
    author = 'Sergey Sherkunov <me@sanerdsher.xyz>'
    topics = ('wasm')
    settings = 'os', 'compiler', 'build_type', 'arch'
    generators = 'BazelToolchain'
    _source_subfolder = 'source_subfolder'

    def export_sources(self):
        for patch in self.conan_data.get('patches', {}).get(self.version, []):
            self.copy(patch['patch_file'])

        for file in self.conan_data.get('files', {}).get(self.version, []):
            self.copy(file['src'])

    def configure(self):
        self.settings.compiler.cppstd = 17

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
        bazel = Bazel(self)

        bazel.configure()
        bazel.build(label='@proxy_wasm_cpp_sdk//:api_lib --config=wasm')
        bazel.build(label='@proxy_wasm_cpp_sdk//:proxy_wasm_intrinsics ' \
                          '--config=wasm')

    def package(self):
        self.copy('LICENSE')
        self.copy('proxy_wasm_api.h',
                  excludes=('bazel-bin', 'bazel-out', 'bazel-source_subfolder',
                            'bazel-testlogs'), dst=f'include')
        self.copy('proxy_wasm_common.h',
                  excludes=('bazel-bin', 'bazel-out', 'bazel-source_subfolder',
                            'bazel-testlogs'), dst=f'include')
        self.copy('proxy_wasm_enums.h',
                  excludes=('bazel-bin', 'bazel-out', 'bazel-source_subfolder',
                            'bazel-testlogs'), dst=f'include')
        self.copy('proxy_wasm_externs.h',
                  excludes=('bazel-bin', 'bazel-out', 'bazel-source_subfolder',
                            'bazel-testlogs'), dst=f'include')
        self.copy('proxy_wasm_intrinsics.h',
                  excludes=('bazel-bin', 'bazel-out', 'bazel-source_subfolder',
                            'bazel-testlogs'), dst=f'include')
        self.copy('*.lib', dst='lib', src='bazel-bin',
                  excludes=('external', '_objs', 'src'), keep_path=False)
        self.copy('*.dll', dst='bin', src='bazel-bin',
                  excludes=('external', '_objs', 'src'), keep_path=False)
        self.copy('*.a', dst='lib', src='bazel-bin',
                  excludes=('external', '_objs', 'src'), keep_path=False)
        self.copy('*.lo', dst='lib', src='bazel-bin',
                  excludes=('external', '_objs', 'src'), keep_path=False)
        self.copy('*.dylib', dst='lib', src='bazel-bin',
                  excludes=('external', '_objs', 'src'), keep_path=False)
        self.copy('*.so', dst='lib', src='bazel-bin',
                  excludes=('external', '_objs', 'src'), keep_path=False)

    def package_info(self):
        self.cpp_info.libs = tools.collect_libs(self)
