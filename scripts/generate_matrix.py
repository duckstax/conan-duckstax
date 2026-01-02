#!/usr/bin/env python3
"""
Generate build matrix for CI by checking valid configurations via conan graph info.
Uses validate() from conanfile.py as source of truth.
"""

import argparse
import json
import subprocess
import sys
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
    cxx_standard: int,
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
        "-o", f"{package_name}/*:cxx_standard={cxx_standard}",
        "-s", f"build_type={build_type}",
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = result.stdout + result.stderr

        # Check for invalid configuration
        if "Invalid" in output and package_name in output:
            return False

        return True

    except subprocess.TimeoutExpired:
        print(f"Warning: timeout checking {package_name}/{version} C++{cxx_standard}", file=sys.stderr)
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

    matrix = []
    exported = set()  # Track exported package/version pairs

    # Find all packages
    if package_filter:
        packages = [recipes_dir / package_filter]
    else:
        packages = sorted(recipes_dir.iterdir())

    for package_dir in packages:
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

        for version in versions:
            # Export recipe to cache (needed for graph info validation)
            export_key = f"{package_name}/{version}"
            if not skip_validation and export_key not in exported:
                if not export_recipe(recipe_path, version):
                    print(f"Warning: failed to export {export_key}", file=sys.stderr)
                    continue
                exported.add(export_key)

            for cxx_std in cxx_standards:
                # Check if configuration is valid (only once per version+cxx_standard)
                if skip_validation:
                    is_valid = True
                else:
                    is_valid = check_valid_configuration(
                        package_name, version, cxx_std, build_type
                    )

                if is_valid:
                    # Add entry for each OS
                    for os_name in os_list:
                        matrix.append({
                            "name": package_name,
                            "version": version,
                            "os": os_name,
                            "cxx_standard": cxx_std,
                            "build_type": build_type,
                        })
                else:
                    print(f"Skipping {package_name}/{version} C++{cxx_std} - invalid configuration",
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