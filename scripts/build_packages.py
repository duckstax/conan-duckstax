#!/usr/bin/env python3
"""
Build all packages in dependency order.

Features:
- Reads versions from config.yml
- Gets available options from recipes via conan inspect
- Parses local dependencies from conanfile.py
- Performs topological sort based on dependencies
- Validates configurations via conan graph info
- Builds packages stage by stage in correct order
- Optionally uploads to remote after build
"""

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import yaml

# Default parameters
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
    cmd = ["conan", "inspect", str(recipe_path), "--format=json"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
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
        return set(m for m in matches if m in local_packages)
    except Exception as e:
        print(f"Warning: failed to parse dependencies: {e}", file=sys.stderr)
        return set()


def topological_sort(packages: dict[str, set[str]]) -> list[list[str]]:
    """
    Perform topological sort on packages based on dependencies.
    Returns list of stages, where each stage contains packages
    that can be built in parallel (no inter-dependencies).
    """
    in_degree = defaultdict(int)
    dependents = defaultdict(set)
    all_packages = set(packages.keys())

    for pkg, deps in packages.items():
        local_deps = deps & all_packages
        in_degree[pkg] = len(local_deps)
        for dep in local_deps:
            dependents[dep].add(pkg)

    stages = []
    remaining = set(all_packages)

    while remaining:
        ready = [pkg for pkg in remaining if in_degree[pkg] == 0]

        if not ready:
            print(f"Warning: circular dependency detected among: {remaining}", file=sys.stderr)
            stages.append(list(remaining))
            break

        stages.append(sorted(ready))

        for pkg in ready:
            remaining.remove(pkg)
            for dependent in dependents[pkg]:
                if dependent in remaining:
                    in_degree[dependent] -= 1

    return stages


def export_recipe(recipe_path: Path, version: str) -> bool:
    """Export recipe to local conan cache."""
    cmd = ["conan", "export", str(recipe_path), f"--version={version}"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
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

    if cxx_standard is not None:
        cmd.extend(["-o", f"{package_name}/*:cxx_standard={cxx_standard}"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr

        # Check for invalid configuration
        if "Invalid" in output and package_name in output:
            return False

        return result.returncode == 0

    except subprocess.TimeoutExpired:
        print(f"Warning: timeout checking {package_name}/{version}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Warning: error checking {package_name}/{version}: {e}", file=sys.stderr)
        return False


def build_package(
    recipe_path: Path,
    version: str,
    cxx_standard: int | None = None,
    build_type: str = "Release",
) -> bool:
    """Build a single package configuration using conan create."""
    package_name = recipe_path.parent.name

    cmd = [
        "conan", "create",
        str(recipe_path),
        f"--version={version}",
        "--build=missing",
        "-s", f"build_type={build_type}",
    ]

    if cxx_standard is not None:
        cmd.extend(["-o", f"{package_name}/*:cxx_standard={cxx_standard}"])

    std_str = f" C++{cxx_standard}" if cxx_standard else ""
    print(f"\n{'='*60}")
    print(f"Building: {package_name}/{version}{std_str}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)
    return result.returncode == 0


def upload_package(package_name: str, version: str) -> bool:
    """Upload package to remote if CONAN_REMOTE_URL is set."""
    remote_url = os.environ.get("CONAN_REMOTE_URL", "")
    if not remote_url:
        return True

    cmd = [
        "conan", "upload",
        f"{package_name}/{version}:*",
        "-r=otterbrix",
        "--confirm",
    ]

    print(f"Uploading: {package_name}/{version}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def collect_packages(
    recipes_dir: Path,
    package_filter: str | None = None,
    version_filter: str | None = None,
) -> dict:
    """
    Collect information about all packages in recipes directory.
    Returns dict: package_name -> {recipe_path, versions, options, dependencies}
    """
    package_info = {}

    if package_filter:
        package_dirs = [recipes_dir / package_filter]
    else:
        package_dirs = sorted(recipes_dir.iterdir())

    # Get local package names first
    local_packages = set()
    for package_dir in package_dirs:
        if package_dir.is_dir() and not package_dir.name.startswith("."):
            if (package_dir / "config.yml").exists():
                local_packages.add(package_dir.name)

    # Collect info for each package
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

        options = get_recipe_options(recipe_path)
        dependencies = get_local_dependencies(recipe_path, local_packages)

        package_info[package_name] = {
            "recipe_path": recipe_path,
            "versions": versions,
            "options": options,
            "dependencies": dependencies,
        }

    return package_info


def main():
    parser = argparse.ArgumentParser(
        description="Build all packages in dependency order"
    )
    parser.add_argument(
        "recipes_dir",
        type=Path,
        help="Path to recipes directory",
    )
    parser.add_argument(
        "--upload",
        type=str,
        default="false",
        help="Upload after build (true/false)",
    )
    parser.add_argument(
        "--build-type",
        type=str,
        default=DEFAULT_BUILD_TYPE,
        help="Build type (default: Release)",
    )
    parser.add_argument(
        "--cxx-standards",
        type=int,
        nargs="+",
        default=DEFAULT_CXX_STANDARDS,
        help="C++ standards to build (default: 17 20)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        help="Skip conan graph info validation (faster, but may include invalid configs)",
    )

    args = parser.parse_args()
    do_upload = args.upload.lower() == "true"

    # Get filters from environment
    package_filter = os.environ.get("PACKAGE_FILTER", "").strip() or None
    version_filter = os.environ.get("VERSION_FILTER", "").strip() or None

    recipes_dir = args.recipes_dir
    if not recipes_dir.exists():
        print(f"Error: {recipes_dir} not found", file=sys.stderr)
        sys.exit(1)

    # Collect package info
    package_info = collect_packages(recipes_dir, package_filter, version_filter)

    if not package_info:
        print("No packages found")
        sys.exit(0)

    # Topological sort
    dep_graph = {name: info["dependencies"] for name, info in package_info.items()}
    stages = topological_sort(dep_graph)

    print(f"\nBuild order (stages): {stages}\n")

    # Export all recipes first
    print("Exporting all recipes...")
    for package_name, info in package_info.items():
        for version in info["versions"]:
            if export_recipe(info["recipe_path"], version):
                print(f"  Exported {package_name}/{version}")
            else:
                print(f"  Failed to export {package_name}/{version}", file=sys.stderr)

    # Build stage by stage
    failed = []
    succeeded = []
    skipped = []

    for stage_num, stage_packages in enumerate(stages):
        print(f"\n{'#'*60}")
        print(f"# STAGE {stage_num}: {stage_packages}")
        print(f"{'#'*60}")

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
                available = options.get("cxx_standard", [])
                if available:
                    # Options can be strings or ints, normalize to int
                    test_standards = [
                        int(str(s)) for s in available
                        if int(str(s)) in args.cxx_standards
                    ]
                else:
                    test_standards = args.cxx_standards
            else:
                test_standards = [None]

            for version in versions:
                for cxx_std in test_standards:
                    build_id = f"{package_name}/{version}" + \
                               (f" C++{cxx_std}" if cxx_std else "")

                    # Validate configuration
                    if not args.skip_validation:
                        if not check_valid_configuration(
                            package_name, version, cxx_std, args.build_type
                        ):
                            print(f"Skipping {build_id} - invalid configuration")
                            skipped.append(build_id)
                            continue

                    # Build
                    success = build_package(
                        recipe_path, version, cxx_std, args.build_type
                    )

                    if success:
                        succeeded.append(build_id)
                        if do_upload:
                            upload_package(package_name, version)
                    else:
                        failed.append(build_id)

    # Summary
    print(f"\n{'='*60}")
    print("BUILD SUMMARY")
    print(f"{'='*60}")

    print(f"\nSucceeded: {len(succeeded)}")
    for s in succeeded:
        print(f"  + {s}")

    if skipped:
        print(f"\nSkipped (invalid config): {len(skipped)}")
        for s in skipped:
            print(f"  ~ {s}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for f in failed:
            print(f"  - {f}")
        sys.exit(1)

    print(f"\nTotal: {len(succeeded)} succeeded, {len(skipped)} skipped, {len(failed)} failed")


if __name__ == "__main__":
    main()