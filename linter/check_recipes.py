#!/usr/bin/env python3
"""
Recipe validation script for conan-duckstax repository.
Validates config.yml, conandata.yml, and conanfile.py files.
"""

import argparse
import ast
import hashlib
import re
import sys
import urllib.request
from pathlib import Path
from typing import Optional

import yaml

# Exit codes
EXIT_SUCCESS = 0
EXIT_FAILURE = 1

# Colors for output
class Colors:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        cls.RED = cls.GREEN = cls.YELLOW = cls.BLUE = cls.RESET = ""


def log_error(file: str, message: str, line: Optional[int] = None):
    """Print error message in GitHub Actions format."""
    loc = f":{line}" if line else ""
    print(f"::error file={file}{loc}::{message}")
    print(f"{Colors.RED}ERROR{Colors.RESET} [{file}{loc}]: {message}")


def log_warning(file: str, message: str, line: Optional[int] = None):
    """Print warning message in GitHub Actions format."""
    loc = f":{line}" if line else ""
    print(f"::warning file={file}{loc}::{message}")
    print(f"{Colors.YELLOW}WARNING{Colors.RESET} [{file}{loc}]: {message}")


def log_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}OK{Colors.RESET} {message}")


def validate_config_yml(config_path: Path) -> list[str]:
    """Validate config.yml structure and content."""
    errors = []

    if not config_path.exists():
        errors.append(f"Missing config.yml")
        return errors

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors

    if not config:
        errors.append("Empty config.yml")
        return errors

    if "versions" not in config:
        errors.append("Missing 'versions' key in config.yml")
        return errors

    versions = config["versions"]
    if not isinstance(versions, dict):
        errors.append("'versions' must be a mapping")
        return errors

    for version, data in versions.items():
        # Version must be a string (quoted in YAML)
        if not isinstance(version, str):
            errors.append(f"Version '{version}' must be a string (add quotes)")

        if not isinstance(data, dict):
            errors.append(f"Version '{version}' entry must be a mapping")
            continue

        if "folder" not in data:
            errors.append(f"Version '{version}' missing 'folder' key")
        elif not isinstance(data["folder"], str):
            errors.append(f"Version '{version}' folder must be a string")

    return errors


def validate_conandata_yml(conandata_path: Path, config_path: Path) -> list[str]:
    """Validate conandata.yml structure and cross-reference with config.yml."""
    errors = []

    if not conandata_path.exists():
        errors.append("Missing conandata.yml")
        return errors

    try:
        with open(conandata_path) as f:
            conandata = yaml.safe_load(f)
    except yaml.YAMLError as e:
        errors.append(f"Invalid YAML: {e}")
        return errors

    if not conandata:
        errors.append("Empty conandata.yml")
        return errors

    # Load config.yml versions for cross-reference
    config_versions = set()
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
                if config and "versions" in config:
                    config_versions = set(config["versions"].keys())
        except yaml.YAMLError:
            pass

    # Validate sources
    if "sources" not in conandata:
        errors.append("Missing 'sources' key in conandata.yml")
    else:
        sources = conandata["sources"]
        if not isinstance(sources, dict):
            errors.append("'sources' must be a mapping")
        else:
            for version, source in sources.items():
                if not isinstance(version, str):
                    errors.append(f"Source version '{version}' must be a string (add quotes)")

                if not isinstance(source, dict):
                    errors.append(f"Source for version '{version}' must be a mapping")
                    continue

                if "url" not in source:
                    errors.append(f"Version '{version}' missing 'url'")

                if "sha256" not in source:
                    errors.append(f"Version '{version}' missing 'sha256'")
                elif len(source.get("sha256", "")) != 64:
                    errors.append(f"Version '{version}' sha256 must be 64 characters")

                # Check if version exists in config.yml
                if config_versions and str(version) not in config_versions:
                    errors.append(f"Version '{version}' in conandata.yml but not in config.yml")

    # Validate patches (optional)
    if "patches" in conandata:
        patches = conandata["patches"]
        if patches and not isinstance(patches, dict):
            errors.append("'patches' must be a mapping")
        elif patches:
            for version, patch_list in patches.items():
                if not isinstance(patch_list, list):
                    errors.append(f"Patches for version '{version}' must be a list")
                    continue

                for i, patch in enumerate(patch_list):
                    if not isinstance(patch, dict):
                        errors.append(f"Patch {i} for version '{version}' must be a mapping")
                        continue

                    if "patch_file" not in patch:
                        errors.append(f"Patch {i} for version '{version}' missing 'patch_file'")

    return errors


def validate_conanfile_py(conanfile_path: Path) -> list[str]:
    """Validate conanfile.py has required attributes."""
    errors = []

    if not conanfile_path.exists():
        errors.append("Missing conanfile.py")
        return errors

    try:
        with open(conanfile_path) as f:
            content = f.read()
    except IOError as e:
        errors.append(f"Cannot read conanfile.py: {e}")
        return errors

    # Parse AST to check for required attributes
    try:
        tree = ast.parse(content)
    except SyntaxError as e:
        errors.append(f"Python syntax error: {e}")
        return errors

    # Find ConanFile class
    conan_class = None
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, ast.Name) and base.id == "ConanFile":
                    conan_class = node
                    break

    if not conan_class:
        errors.append("No class inheriting from ConanFile found")
        return errors

    # Check required attributes
    required_attrs = ["name", "description", "license", "url"]
    found_attrs = set()

    for node in conan_class.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found_attrs.add(target.id)

    for attr in required_attrs:
        if attr not in found_attrs:
            errors.append(f"Missing required attribute: {attr}")

    # Check for common typos
    typo_check = {
        "export_source": "export_sources",
        "requirement": "requirements",
        "option": "options",
        "default_option": "default_options",
    }

    for typo, correct in typo_check.items():
        if typo in found_attrs:
            errors.append(f"Possible typo: '{typo}' should be '{correct}'")

    return errors


def validate_test_package(test_package_path: Path) -> list[str]:
    """Validate test_package directory exists and has required files."""
    errors = []

    if not test_package_path.exists():
        errors.append("Missing test_package directory")
        return errors

    required_files = ["conanfile.py", "CMakeLists.txt"]
    for filename in required_files:
        if not (test_package_path / filename).exists():
            errors.append(f"Missing test_package/{filename}")

    return errors


def validate_recipe(recipe_path: Path) -> tuple[int, int]:
    """Validate a single recipe. Returns (errors, warnings) count."""
    errors = 0
    warnings = 0

    package_name = recipe_path.parent.name
    print(f"\n{Colors.BLUE}Validating{Colors.RESET} {package_name}/{recipe_path.name}")

    config_path = recipe_path.parent / "config.yml"
    conandata_path = recipe_path / "conandata.yml"
    conanfile_path = recipe_path / "conanfile.py"
    test_package_path = recipe_path / "test_package"

    # Validate config.yml
    for error in validate_config_yml(config_path):
        log_error(str(config_path), error)
        errors += 1

    # Validate conandata.yml
    for error in validate_conandata_yml(conandata_path, config_path):
        log_error(str(conandata_path), error)
        errors += 1

    # Validate conanfile.py
    for error in validate_conanfile_py(conanfile_path):
        log_error(str(conanfile_path), error)
        errors += 1

    # Validate test_package
    for error in validate_test_package(test_package_path):
        log_warning(str(test_package_path), error)
        warnings += 1

    if errors == 0:
        log_success(f"{package_name} passed validation")

    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description="Validate Conan recipes")
    parser.add_argument(
        "recipes_dir",
        type=Path,
        nargs="?",
        default=Path("recipes"),
        help="Path to recipes directory (default: recipes)",
    )
    parser.add_argument(
        "--package",
        "-p",
        type=str,
        help="Validate specific package only",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors",
    )

    args = parser.parse_args()

    if args.no_color:
        Colors.disable()

    recipes_dir = args.recipes_dir
    if not recipes_dir.exists():
        print(f"Error: recipes directory '{recipes_dir}' not found")
        return EXIT_FAILURE

    total_errors = 0
    total_warnings = 0

    print(f"{Colors.BLUE}=== Conan Recipe Validator ==={Colors.RESET}")

    # Find all recipe folders
    if args.package:
        packages = [recipes_dir / args.package]
    else:
        packages = sorted(recipes_dir.iterdir())

    for package_dir in packages:
        if not package_dir.is_dir() or package_dir.name.startswith("."):
            continue

        # Find recipe folders (e.g., 'all')
        for recipe_dir in package_dir.iterdir():
            if not recipe_dir.is_dir() or recipe_dir.name.startswith("."):
                continue

            if (recipe_dir / "conanfile.py").exists():
                errors, warnings = validate_recipe(recipe_dir)
                total_errors += errors
                total_warnings += warnings

    # Summary
    print(f"\n{Colors.BLUE}=== Summary ==={Colors.RESET}")
    print(f"Errors: {total_errors}")
    print(f"Warnings: {total_warnings}")

    if total_errors > 0:
        print(f"\n{Colors.RED}Validation failed with {total_errors} error(s){Colors.RESET}")
        return EXIT_FAILURE

    if args.strict and total_warnings > 0:
        print(f"\n{Colors.YELLOW}Validation failed (strict mode) with {total_warnings} warning(s){Colors.RESET}")
        return EXIT_FAILURE

    print(f"\n{Colors.GREEN}All recipes passed validation{Colors.RESET}")
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())