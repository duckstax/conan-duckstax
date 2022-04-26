from conan.tools.google import Bazel
from conans import ConanFile, tools


class ProxyWASMCPPHost(ConanFile):
    name = 'proxy-wasm-cpp-host'
    description = 'WebAssembly for Proxies (C++ host implementation)'
    homepage = 'https://github.com/proxy-wasm/proxy-wasm-cpp-host.git'

    @property
    def url(self):
        return self.homepage

    license = 'Apache-2.0'
    author = 'Sergey Sherkunov <leinlawun@leinlawun.org>'
    topics = ('wasm')
    settings = 'os', 'compiler', 'build_type', 'arch'
    options = {'shared': [True, False],
               'null_vm': [True, False],
               'wamr_vm': [True, False],
               'wavm_vm': [True, False],
               'v8_vm': [True, False],
               'wasmedge_vm': [True, False],
               'wasmtime_vm': [True, False]}
    default_options = {'shared': False,
                       'null_vm': True,
                       'wamr_vm': True,
                       'wavm_vm': False,
                       'v8_vm': True,
                       'wasmedge_vm': False,
                       'wasmtime_vm': True}
    generators = 'BazelToolchain'

    _source_subfolder = 'source_subfolder'

    def export_sources(self):
        for patch in self.conan_data.get('patches', {}).get(self.version, []):
            self.copy(patch['patch_file'])

    def configure(self):
        self.settings.compiler['gcc'].cppstd = 17

    def layout(self):
        self.folders.source = self._source_subfolder
        self.folders.build = self._source_subfolder

    def source(self):
        tools.get(**self.conan_data['sources'][self.version], strip_root=True)

        for patch in self.conan_data.get('patches', {}).get(self.version, []):
            tools.patch(**patch)

    def build(self):
        bazel = Bazel(self)

        bazel.configure()
        bazel.build(label='@proxy_wasm_cpp_host//:base_lib ' \
                          '--define=engine=multi')

        if self.options.null_vm:
            bazel.build(label='@proxy_wasm_cpp_host//:null_lib ' \
                              '--define=engine=multi')

        if self.options.wamr_vm:
            bazel.build(label='@proxy_wasm_cpp_host//:wamr_lib '\
                              '--define=engine=multi')

        if self.options.wavm_vm:
            bazel.build(label='@proxy_wasm_cpp_host//:wavm_lib '\
                              '--define=engine=multi')

        if self.options.v8_vm:
            bazel.build(label='@proxy_wasm_cpp_host//:v8_lib ' \
                              '--define=engine=multi')

        if self.options.wasmedge_vm:
            bazel.build(label='@proxy_wasm_cpp_host//:wasmedge_lib ' \
                              '--define=engine=multi')

        if self.options.wasmtime_vm:
            bazel.build(label='@proxy_wasm_cpp_host//:wasmtime_lib ' \
                              '--define=engine=multi')

    def package(self):
        self.copy('LICENSE')
        self.copy('*.h', dst=f'include', src='include')
        self.copy('proxy_wasm_*.h', dst=f'include',
                  src='bazel-source_subfolder/external/proxy_wasm_cpp_sdk')
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
        self.copy('*.lib', dst='lib',
                  src='bazel-bin/external/com_github_bytecodealliance_wasm_micro_runtime/copy_wamr_lib',
                  keep_path=False)
        self.copy('*.dll', dst='bin', 
                  src='bazel-bin/external/com_github_bytecodealliance_wasm_micro_runtime/copy_wamr_lib',
                  keep_path=False)
        self.copy('*.a', dst='lib', 
                  src='bazel-bin/external/com_github_bytecodealliance_wasm_micro_runtime/copy_wamr_lib',
                  keep_path=False)
        self.copy('*.lo', dst='lib', 
                  src='bazel-bin/external/com_github_bytecodealliance_wasm_micro_runtime/copy_wamr_lib',
                  keep_path=False)
        self.copy('*.dylib', dst='lib', 
                  src='bazel-bin/external/com_github_bytecodealliance_wasm_micro_runtime/copy_wamr_lib',
                  keep_path=False)
        self.copy('*.so', dst='lib', 
                  src='bazel-bin/external/com_github_bytecodealliance_wasm_micro_runtime/copy_wamr_lib',
                  keep_path=False)

    def package_info(self):
        #self.cpp_info.libs = ['base_lib', 'null_lib', 'wamr_lib', 'v8_lib', 'wasmtime_lib', 'iwasm', 'vmlib']
        self.cpp_info.libs = ['base_lib', 'null_lib', 'wamr_lib', 'iwasm', 'vmlib']
        self.cpp_info.includedirs = ['.', 'include']
