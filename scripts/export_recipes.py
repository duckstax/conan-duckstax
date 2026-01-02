#!/usr/bin/env python3
"""
Export all recipes to local conan cache.
This enables building packages with local dependencies.
"""

import subprocess
import sys
from pathlib import Path

import yaml


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
        if result.returncode == 0:
            package_name = recipe_path.parent.name
            print(f"Exported {package_name}/{version}")
            return True
        else:
            print(f"Failed to export {recipe_path.parent.parent.name}/{version}: {result.stderr}",
                  file=sys.stderr)
            return False
    except Exception as e:
        print(f"Error exporting {recipe_path}: {e}", file=sys.stderr)
        return False


def main():
    if len(sys.argv) < 2:
        print("Usage: export_recipes.py <recipes_dir>", file=sys.stderr)
        sys.exit(1)

    recipes_dir = Path(sys.argv[1])
    if not recipes_dir.exists():
        print(f"Error: directory '{recipes_dir}' not found", file=sys.stderr)
        sys.exit(1)

    exported = 0
    failed = 0

    for package_dir in sorted(recipes_dir.iterdir()):
        if not package_dir.is_dir() or package_dir.name.startswith("."):
            continue

        config_path = package_dir / "config.yml"
        if not config_path.exists():
            continue

        # Find recipe folder
        recipe_path = None
        for subdir in package_dir.iterdir():
            if subdir.is_dir() and (subdir / "conanfile.py").exists():
                recipe_path = subdir
                break

        if not recipe_path:
            continue

        versions = get_package_versions(config_path)
        for version in versions:
            if export_recipe(recipe_path, version):
                exported += 1
            else:
                failed += 1

    print(f"Exported {exported} recipes, {failed} failed", file=sys.stderr)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
