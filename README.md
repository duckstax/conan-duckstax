# conan-duckstax

Conan recipes for DuckStax packages. Compatible with [conan-center-index](https://github.com/conan-io/conan-center-index) structure.

## Packages

| Package | Description | Latest Version |
|---------|-------------|----------------|
| **actor-zeta** | C++ virtual actor model implementation | 2.0.0          |
| **otterbrix** | Open-source framework for analytical applications | 1.0.0b2-rc-3   |

## Usage

### Option 1: Local Recipes Index (Recommended)

Use this repository directly as a Conan remote:

```bash
# Clone repository
git clone https://github.com/duckstax/conan-duckstax.git
cd conan-duckstax

# Add as local remote
conan remote add duckstax . --type=local-recipes-index

# List available packages
conan list "*" -r=duckstax

# Install package (builds from source)
conan install --requires="actor-zeta/2.0.0" -r=duckstax --build=missing
```

### Option 2: Remote Server

Use pre-built binaries from the otterbrix server:

```bash
conan remote add otterbrix https://conan.otterbrix.com
conan install --requires="actor-zeta/2.0.0" -r=otterbrix
```

## Building Packages Locally

```bash
# Build actor-zeta
conan create recipes/actor-zeta/all --version=2.0.0 \
  -o "actor-zeta/*:cxx_standard=20" \
  -s build_type=Release \
  --build=missing

# Build otterbrix (depends on actor-zeta)
conan create recipes/otterbrix/1.x --version=1.0.0b2-rc-3 \
  -o "actor-zeta/*:cxx_standard=20" \
  -s build_type=Release \
  --build=missing
```

## Package Options

### actor-zeta

| Option | Values | Default |
|--------|--------|---------|
| `shared` | True/False | False |
| `fPIC` | True/False | False |
| `cxx_standard` | 17, 20 | 20 |
| `exceptions_disable` | True/False | False |
| `rtti_disable` | True/False | False |

## Repository Structure

```
conan-duckstax/
├── recipes/
│   ├── actor-zeta/
│   │   ├── config.yml           # Available versions
│   │   └── all/
│   │       ├── conanfile.py     # Recipe
│   │       ├── conandata.yml    # Sources & patches
│   │       └── test_package/    # Package test
│   └── otterbrix/
│       ├── config.yml
│       └── 1.x/
└── .github/workflows/
    └── conan-upload.yml         # CI/CD
```

## Contributing

1. Fork the repository
2. Add/modify recipe in `recipes/<package>/<folder>/` (folder is set in `config.yml`)
3. Update `config.yml` with new version
4. Update `conandata.yml` with source URL and SHA256
5. Test locally: `conan create recipes/<package>/<folder> --version=X.Y.Z`
6. Submit PR

## Requirements

- Conan 2.0+
- CMake 3.15+
- C++20 compiler

## License

MIT