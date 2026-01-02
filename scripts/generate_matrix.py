#!/usr/bin/env python3
"""
Generate build matrix for CI by checking valid configurations via conan graph info.
Uses validate() from conanfile.py as source of truth.
Reads available options from each recipe via conan inspect.
Performs topological sort based on package dependencies.
"""

import argparse
import json
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

# Default matrix parameters
DEFAULT_OS_LIST = ["ubuntu-22.04", "macos-13", "macos-14"]
DEFAULT_CXX_STANDARDS = [17, 20]
DEFAULT_BUILD_TYPE = "Release"


def get_package_versions(config_path: Path) -> list[str]:
    """Extract versions from config.yml."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    if not config or "versions" not in config:
        return []

    return list(config["versions"].keys())


def get_recipe_options(recipe_path: Path) -> dict:
    """Get available options from recipe via conan inspect."""
    cmd = [
        "conan", "inspect",
        str(recipe_path),
        "--format=json",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode == 0:
            data = json.loads(result.stdout)
            return data.get("options_definitions", {})

    except Exception as e:
        print(f"Warning: failed to inspect recipe: {e}", file=sys.stderr)

    return {}


def get_local_dependencies(recipe_path: Path, local_packages: set[str]) -> set[str]:
    """
    Extract local package dependencies from conanfile.py.
    Only returns dependencies that are in local_packages set.
    """
    conanfile = recipe_path / "conanfile.py"
    if not conanfile.exists():
        return set()

    try:
        content = conanfile.read_text()

        # Find self.requires("package/version") patterns
        requires_pattern = r'self\.requires\s*\(\s*["\']([^/"\']+)/[^"\']+["\']\s*'
        matches = re.findall(requires_pattern, content)

        # Filter to only local packages
        return set(m for m in matches if m in local_packages)

    except Exception as e:
        print(f"Warning: failed to parse dependencies: {e}", file=sys.stderr)
        return set()


def topological_sort(packages: dict[str, set[str]]) -> list[list[str]]:
    """
    Perform topological sort on packages based on dependencies.
    Returns list of stages, where each stage contains packages that can be built in parallel.
    """
    # Build reverse dependency graph (who depends on me)
    in_degree = defaultdict(int)
    dependents = defaultdict(set)

    all_packages = set(packages.keys())

    for pkg, deps in packages.items():
        # Filter deps to only include packages we're building
        local_deps = deps & all_packages
        in_degree[pkg] = len(local_deps)
        for dep in local_deps:
            dependents[dep].add(pkg)

    # Initialize with packages that have no dependencies
    stages = []
    remaining = set(all_packages)

    while remaining:
        # Find all packages with no remaining dependencies
        ready = [pkg for pkg in remaining if in_degree[pkg] == 0]

        if not ready:
            # Circular dependency detected
            print(f"Warning: circular dependency detected among: {remaining}", file=sys.stderr)
            stages.append(list(remaining))
            break

        stages.append(sorted(ready))

        # Remove ready packages and update in_degree
        for pkg in ready:
            remaining.remove(pkg)
            for dependent in dependents[pkg]:
                if dependent in remaining:
                    in_degree[dependent] -= 1

    return stages


def export_recipe(recipe_path: Path, version: str) -> bool:
    """Export recipe to local cache."""
    cmd = [
        "conan", "export",
        str(recipe_path),
        f"--version={version}",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.returncode == 0
    except Exception as e:
        print(f"Warning: export failed: {e}", file=sys.stderr)
        return False


def check_valid_configuration(
    package_name: str,
    version: str,
    cxx_standard: int | None,
    build_type: str = "Release",
) -> bool:
    """
    Check if configuration is valid using conan graph info.
    Requires recipe to be exported first.
    Returns True if valid, False if ConanInvalidConfiguration.
    """
    cmd = [
        "conan", "graph", "info",
        f"--requires={package_name}/{version}",
        "-s", f"build_type={build_type}",
    ]

    # Only add cxx_standard option if provided
    if cxx_standard is not None:
        cmd.extend(["-o", f"{package_name}/*:cxx_standard={cxx_standard}"])

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = result.stdout + result.stderr

        # Check for invalid configuration
        if "Invalid" in output and package_name in output:
            return False

        return True

    except subprocess.TimeoutExpired:
        print(f"Warning: timeout checking {package_name}/{version}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Warning: error checking {package_name}/{version}: {e}", file=sys.stderr)
        return False


def generate_matrix(
    recipes_dir: Path,
    package_filter: str | None = None,
    version_filter: str | None = None,
    os_list: list[str] | None = None,
    cxx_standards: list[int] | None = None,
    build_type: str = DEFAULT_BUILD_TYPE,
    skip_validation: bool = False,
) -> list[dict]:
    """Generate build matrix with only valid configurations."""

    if os_list is None:
        os_list = DEFAULT_OS_LIST
    if cxx_standards is None:
        cxx_standards = DEFAULT_CXX_STANDARDS

    # First pass: collect all packages and their dependencies
    package_info = {}  # name -> {recipe_path, versions, options, dependencies}

    # Find all packages
    if package_filter:
        package_dirs = [recipes_dir / package_filter]
    else:
        package_dirs = sorted(recipes_dir.iterdir())

    # Get list of local package names
    local_packages = set()
    for package_dir in package_dirs:
        if package_dir.is_dir() and not package_dir.name.startswith("."):
            config_path = package_dir / "config.yml"
            if config_path.exists():
                local_packages.add(package_dir.name)

    # Collect package info
    for package_dir in package_dirs:
        if not package_dir.is_dir() or package_dir.name.startswith("."):
            continue

        config_path = package_dir / "config.yml"
        if not config_path.exists():
            continue

        package_name = package_dir.name

        # Get versions
        if version_filter:
            versions = [version_filter]
        else:
            versions = get_package_versions(config_path)

        # Find recipe folder
        recipe_path = None
        for subdir in package_dir.iterdir():
            if subdir.is_dir() and (subdir / "conanfile.py").exists():
                recipe_path = subdir
                break

        if not recipe_path:
            continue

        # Get available options from recipe
        options = get_recipe_options(recipe_path)

        # Get dependencies
        dependencies = get_local_dependencies(recipe_path, local_packages)

        package_info[package_name] = {
            "recipe_path": recipe_path,
            "versions": versions,
            "options": options,
            "dependencies": dependencies,
        }

    # Perform topological sort
    dep_graph = {name: info["dependencies"] for name, info in package_info.items()}
    stages = topological_sort(dep_graph)

    print(f"Build stages: {stages}", file=sys.stderr)

    # Generate matrix with stage information
    matrix = []
    exported = set()

    for stage_num, stage_packages in enumerate(stages):
        for package_name in stage_packages:
            if package_name not in package_info:
                continue

            info = package_info[package_name]
            recipe_path = info["recipe_path"]
            versions = info["versions"]
            options = info["options"]
            has_cxx_standard = "cxx_standard" in options

            # Determine cxx_standard values to test
            if has_cxx_standard:
                available_standards = options.get("cxx_standard", [])
                if available_standards:
                    test_standards = [int(s) for s in available_standards if int(s) in cxx_standards]
                else:
                    test_standards = cxx_standards
            else:
                test_standards = [None]

            for version in versions:
                # Export recipe to cache
                export_key = f"{package_name}/{version}"
                if not skip_validation and export_key not in exported:
                    if not export_recipe(recipe_path, version):
                        print(f"Warning: failed to export {export_key}", file=sys.stderr)
                        continue
                    exported.add(export_key)

                for cxx_std in test_standards:
                    # Check if configuration is valid
                    if skip_validation:
                        is_valid = True
                    else:
                        is_valid = check_valid_configuration(
                            package_name, version, cxx_std, build_type
                        )

                    if is_valid:
                        for os_name in os_list:
                            entry = {
                                "name": package_name,
                                "version": version,
                                "os": os_name,
                                "build_type": build_type,
                            }
                            if cxx_std is not None:
                                entry["cxx_standard"] = cxx_std
                            matrix.append(entry)
                    else:
                        std_str = f" C++{cxx_std}" if cxx_std else ""
                        print(f"Skipping {package_name}/{version}{std_str} - invalid configuration",
                              file=sys.stderr)

    return matrix


def main():
    parser = argparse.ArgumentParser(description="Generate CI build matrix")
    parser.add_argument(
        "recipes_dir",
        type=Path,
        nargs="?",
        default=Path("recipes"),
        help="Path to recipes directory",
    )
    parser.add_argument(
        "--package", "-p",
        type=str,
        help="Build specific package only",
    )
    parser.add_argument(
        "--version", "-v",
        type=str,
        help="Build specific version only",
    )
    parser.add_argument(
        "--os",
        type=str,
        nargs="+",
        default=DEFAULT_OS_LIST,
        help="OS list for matrix",
    )
    parser.add_argument(
        "--cxx-standard",
        type=int,
        nargs="+",
        default=DEFAULT_CXX_STANDARDS,
        help="C++ standards for matrix",
    )
    parser.add_argument(
        "--build-type",
        type=str,
        default=DEFAULT_BUILD_TYPE,
        help="Build type",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip conan graph info validation (faster, but includes invalid configs)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        choices=["json", "github"],
        default="json",
        help="Output format",
    )

    args = parser.parse_args()

    if not args.recipes_dir.exists():
        print(f"Error: recipes directory '{args.recipes_dir}' not found", file=sys.stderr)
        sys.exit(1)

    matrix = generate_matrix(
        recipes_dir=args.recipes_dir,
        package_filter=args.package,
        version_filter=args.version,
        os_list=args.os,
        cxx_standards=args.cxx_standard,
        build_type=args.build_type,
        skip_validation=args.skip_validation,
    )

    if args.output == "github":
        # GitHub Actions output format
        print(f"matrix={json.dumps(matrix)}")
    else:
        # Pretty JSON
        print(json.dumps(matrix, indent=2))

    # Print summary to stderr
    print(f"Generated {len(matrix)} build jobs", file=sys.stderr)


if __name__ == "__main__":
    main()