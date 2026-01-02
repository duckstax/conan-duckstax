#!/usr/bin/env python3
"""
Build all packages in dependency order.
Performs topological sort and builds packages stage by stage.
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
    """Extract local package dependencies from conanfile.py."""
    conanfile = recipe_path / "conanfile.py"
    if not conanfile.exists():
        return set()

    try:
        content = conanfile.read_text()
        requires_pattern = r'self\.requires\s*\(\s*["\']([^/"\']+)/[^"\']+["\']\s*'
        matches = re.findall(requires_pattern, content)
        return set(m for m in matches if m in local_packages)
    except Exception as e:
        print(f"Warning: failed to parse dependencies: {e}", file=sys.stderr)
        return set()


def topological_sort(packages: dict[str, set[str]]) -> list[list[str]]:
    """Perform topological sort. Returns list of stages."""
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
            print(f"Warning: circular dependency among: {remaining}", file=sys.stderr)
            stages.append(list(remaining))
            break

        stages.append(sorted(ready))

        for pkg in ready:
            remaining.remove(pkg)
            for dependent in dependents[pkg]:
                if dependent in remaining:
                    in_degree[dependent] -= 1

    return stages


def build_package(
    recipe_path: Path,
    version: str,
    cxx_standard: int | None = None,
    build_type: str = "Release",
) -> bool:
    """Build a single package configuration."""
    cmd = [
        "conan", "create",
        str(recipe_path),
        f"--version={version}",
        "--build=missing",
        f"-s", f"build_type={build_type}",
    ]

    if cxx_standard is not None:
        package_name = recipe_path.parent.name
        cmd.extend(["-o", f"{package_name}/*:cxx_standard={cxx_standard}"])

    print(f"\n{'='*60}")
    print(f"Building: {recipe_path.parent.name}/{version}" +
          (f" C++{cxx_standard}" if cxx_standard else ""))
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)
    return result.returncode == 0


def upload_package(package_name: str, version: str) -> bool:
    """Upload package to remote."""
    remote_url = os.environ.get("CONAN_REMOTE_URL", "")
    if not remote_url:
        return True

    cmd = [
        "conan", "upload",
        f"{package_name}/{version}:*",
        "-r=upload",
        "--confirm",
    ]

    print(f"Uploading: {package_name}/{version}")
    result = subprocess.run(cmd)
    return result.returncode == 0


def check_valid_configuration(
    package_name: str,
    version: str,
    cxx_standard: int | None,
    build_type: str = "Release",
) -> bool:
    """Check if configuration is valid using conan graph info."""
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
        if "Invalid" in output and package_name in output:
            return False
        return result.returncode == 0
    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser(description="Build packages in dependency order")
    parser.add_argument("recipes_dir", type=Path, help="Path to recipes directory")
    parser.add_argument("--upload", type=str, default="false",
                        help="Upload after build (true/false)")
    parser.add_argument("--build-type", type=str, default="Release")
    parser.add_argument("--cxx-standards", type=int, nargs="+", default=[17, 20])

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
    package_info = {}

    if package_filter:
        package_dirs = [recipes_dir / package_filter]
    else:
        package_dirs = sorted(recipes_dir.iterdir())

    # Get local package names
    local_packages = set()
    for package_dir in package_dirs:
        if package_dir.is_dir() and not package_dir.name.startswith("."):
            if (package_dir / "config.yml").exists():
                local_packages.add(package_dir.name)

    # Collect info
    for package_dir in package_dirs:
        if not package_dir.is_dir() or package_dir.name.startswith("."):
            continue

        config_path = package_dir / "config.yml"
        if not config_path.exists():
            continue

        package_name = package_dir.name

        if version_filter:
            versions = [version_filter]
        else:
            versions = get_package_versions(config_path)

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

    # Topological sort
    dep_graph = {name: info["dependencies"] for name, info in package_info.items()}
    stages = topological_sort(dep_graph)

    print(f"\nBuild order (stages): {stages}\n")

    # Export all recipes first
    print("Exporting all recipes...")
    for package_name, info in package_info.items():
        for version in info["versions"]:
            cmd = ["conan", "export", str(info["recipe_path"]), f"--version={version}"]
            subprocess.run(cmd, capture_output=True)
            print(f"  Exported {package_name}/{version}")

    # Build stage by stage
    failed = []
    succeeded = []

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

            # Determine cxx_standard values
            if has_cxx_standard:
                available = options.get("cxx_standard", [])
                if available:
                    test_standards = [int(str(s)) for s in available
                                      if int(str(s)) in args.cxx_standards]
                else:
                    test_standards = args.cxx_standards
            else:
                test_standards = [None]

            for version in versions:
                for cxx_std in test_standards:
                    # Validate configuration
                    if not check_valid_configuration(
                        package_name, version, cxx_std, args.build_type
                    ):
                        std_str = f" C++{cxx_std}" if cxx_std else ""
                        print(f"Skipping {package_name}/{version}{std_str} - invalid config")
                        continue

                    # Build
                    success = build_package(
                        recipe_path, version, cxx_std, args.build_type
                    )

                    build_id = f"{package_name}/{version}" + \
                               (f" C++{cxx_std}" if cxx_std else "")

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
    print(f"Succeeded: {len(succeeded)}")
    for s in succeeded:
        print(f"  ✓ {s}")

    if failed:
        print(f"\nFailed: {len(failed)}")
        for f in failed:
            print(f"  ✗ {f}")
        sys.exit(1)


if __name__ == "__main__":
    main()