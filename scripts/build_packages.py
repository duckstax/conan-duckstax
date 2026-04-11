#!/usr/bin/env python3
"""
Build all packages in dependency order.

Features:
- Reads versions from config.yml
- Gets available options from recipes via conan inspect
- Parses local dependencies from conanfile.py
- Performs topological sort based on dependencies
- Uses Conan profiles for C++ standard configuration
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
DEFAULT_BUILD_TYPE = "Release"


def get_package_versions(config_path: Path) -> dict[str, str]:
    """Extract versions and their folder mappings from config.yml."""
    with open(config_path) as f:
        config = yaml.safe_load(f)

    if not config or "versions" not in config:
        return {}

    return {
        version: info["folder"]
        for version, info in config["versions"].items()
    }


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


def discover_profiles(profiles_dir: Path) -> list[dict]:
    """
    Discover conan profiles and extract cppstd setting.
    Returns list of dicts with 'path', 'name', 'cppstd' keys.
    """
    profiles = []
    if not profiles_dir.is_dir():
        return profiles

    for profile_file in sorted(profiles_dir.iterdir()):
        if not profile_file.is_file():
            continue

        cppstd = None
        content = profile_file.read_text()
        m = re.search(r"compiler\.cppstd\s*=\s*(\S+)", content)
        if m:
            cppstd_val = m.group(1)
            std_num = re.sub(r"^gnu", "", cppstd_val)
            try:
                cppstd = int(std_num)
            except ValueError:
                pass

        profiles.append({
            "path": profile_file,
            "name": profile_file.name,
            "cppstd": cppstd,
        })

    return profiles


def check_valid_configuration(
    package_name: str,
    version: str,
    cxx_standard: int | None,
    build_type: str = "Release",
    profile_path: Path | None = None,
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

    if profile_path is not None:
        cmd.extend(["-pr:h", str(profile_path)])

    if cxx_standard is not None:
        cmd.extend(["-o", f"{package_name}/*:cxx_standard={cxx_standard}"])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr

        # Check for invalid configuration
        if "Invalid" in output and package_name in output:
            return False

        if result.returncode != 0:
            print(f"  validate {package_name}/{version}: returncode={result.returncode}",
                  file=sys.stderr)
            # Print last few lines of output for diagnostics
            lines = output.strip().splitlines()
            for line in lines[-5:]:
                print(f"    {line}", file=sys.stderr)

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
    profile_path: Path | None = None,
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

    if profile_path is not None:
        cmd.extend(["-pr:h", str(profile_path)])

    if cxx_standard is not None:
        cmd.extend(["-o", f"{package_name}/*:cxx_standard={cxx_standard}"])

    std_str = f" C++{cxx_standard}" if cxx_standard else ""
    profile_str = f" [{profile_path.name}]" if profile_path else ""
    print(f"\n{'='*60}")
    print(f"Building: {package_name}/{version}{std_str}{profile_str}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}\n")

    result = subprocess.run(cmd)
    return result.returncode == 0


def upload_package(package_name: str, version: str) -> bool:
    """Upload package to remote if CONAN_REMOTE_URL is set."""
    remote_url = os.environ.get("CONAN_REMOTE_URL", "")
    if not remote_url:
        print(f"  Skipping upload {package_name}/{version}: CONAN_REMOTE_URL not set")
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

        # Get version -> folder mapping
        version_folders = get_package_versions(config_path)
        if not version_folders:
            continue

        if version_filter:
            version_folders = {
                v: f for v, f in version_folders.items() if v == version_filter
            }

        # Build per-version info with correct recipe path
        version_info = {}
        for version, folder in version_folders.items():
            recipe_path = package_dir / folder
            if not (recipe_path / "conanfile.py").exists():
                print(f"Warning: {recipe_path}/conanfile.py not found for "
                      f"{package_name}/{version}", file=sys.stderr)
                continue
            version_info[version] = recipe_path

        if not version_info:
            continue

        # Collect options and dependencies from all recipe folders
        all_dependencies = set()
        options = {}
        for recipe_path in version_info.values():
            opts = get_recipe_options(recipe_path)
            if not options:
                options = opts
            all_dependencies |= get_local_dependencies(recipe_path, local_packages)
        dependencies = all_dependencies

        package_info[package_name] = {
            "version_info": version_info,
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
        "--profiles-dir",
        type=Path,
        default=None,
        help="Path to directory with Conan profiles",
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
        "--skip-validation",
        action="store_true",
        help="Skip conan graph info validation (faster, but may include invalid configs)",
    )

    args = parser.parse_args()
    do_upload = args.upload.lower() == "true"

    # Discover profiles
    profiles_dir = args.profiles_dir
    if profiles_dir is None:
        # Auto-detect: look for profiles/ next to recipes_dir
        candidate = args.recipes_dir.parent / "profiles"
        if candidate.is_dir():
            profiles_dir = candidate

    profiles = discover_profiles(profiles_dir) if profiles_dir else []

    if not profiles:
        # Fallback: single build with default profile
        profiles = [{"path": None, "name": "default", "cppstd": None}]

    # Diagnostics
    remote_url = os.environ.get("CONAN_REMOTE_URL", "")
    print(f"\n{'='*60}")
    print("CONFIGURATION")
    print(f"{'='*60}")
    print(f"  --upload flag: {args.upload}")
    print(f"  do_upload: {do_upload}")
    print(f"  CONAN_REMOTE_URL set: {bool(remote_url)}")
    if remote_url:
        print(f"  CONAN_REMOTE_URL: {remote_url[:20]}...")
    print(f"  profiles: {[p['name'] for p in profiles]}")
    print(f"{'='*60}\n")

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
        for version, recipe_path in info["version_info"].items():
            if export_recipe(recipe_path, version):
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
            version_info = info["version_info"]
            options = info["options"]
            has_cxx_standard = "cxx_standard" in options

            for profile in profiles:
                profile_path = profile["path"]
                profile_cppstd = profile["cppstd"]

                # Determine cxx_standard option value for this profile
                if has_cxx_standard:
                    available = options.get("cxx_standard", [])
                    if profile_cppstd is not None and available:
                        cppstd_str = str(profile_cppstd)
                        if cppstd_str not in [str(s) for s in available]:
                            for version in version_info:
                                build_id = f"{package_name}/{version} [{profile['name']}]"
                                print(f"Skipping {build_id} - cxx_standard={profile_cppstd} not available")
                                skipped.append(build_id)
                            continue
                        cxx_std = profile_cppstd
                    else:
                        cxx_std = None
                else:
                    cxx_std = None

                for version, recipe_path in version_info.items():
                    build_id = f"{package_name}/{version}" + \
                               (f" C++{cxx_std}" if cxx_std else "") + \
                               f" [{profile['name']}]"

                    # Validate configuration
                    if not args.skip_validation:
                        if not check_valid_configuration(
                            package_name, version, cxx_std,
                            args.build_type, profile_path,
                        ):
                            print(f"Skipping {build_id} - invalid configuration")
                            skipped.append(build_id)
                            continue

                    # Build
                    success = build_package(
                        recipe_path, version, cxx_std,
                        args.build_type, profile_path,
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
