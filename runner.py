#!/usr/bin/env python3

import argparse
import tempfile

import yaml
from cpt.printer import Printer

printer = Printer()

from ci_tools_gha.utils import get_builder_default

gha_hack = True

import os
import shutil


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def gha_hack_copy(src):
    dst = os.path.abspath(os.getcwd())
    symlinks = False
    ignore = None
    test_package_src = os.path.join(src, "test_package")
    test_package_dst = os.path.join(dst, "test_package")
    conandata_src = os.path.join(src, "conandata.yml")
    conandata_dst = os.path.join(dst, "conandata.yml")
    conanfile_src = os.path.join(src, "conanfile.py")
    conanfile_dst = os.path.join(dst, "conanfile.py")

    shutil.copytree(test_package_src, test_package_dst, symlinks, ignore)
    shutil.copy2(conandata_src, conandata_dst)
    shutil.copy2(conanfile_src, conanfile_dst)


def gha_hack_removed():
    dst = os.path.abspath(os.getcwd())
    test_package_dst = os.path.join(dst, "test_package")
    conandata_dst = os.path.join(dst, "conandata.yml")
    conanfile_dst = os.path.join(dst, "conanfile.py")

    shutil.rmtree(test_package_dst, ignore_errors=True)
    os.remove(conandata_dst)
    os.remove(conanfile_dst)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', action='store', type=str, required=True)
    args = parser.parse_args()
    with open(args.config) as f:
        configuration = yaml.load(f, Loader=yaml.FullLoader)

    printer.print_message("Enabling Conan download cache ...")
    tmpdir = os.path.join(tempfile.gettempdir(), "conan")
    os.makedirs(tmpdir, mode=0o777)
    os.chmod(tmpdir, mode=0o777)
    os.system('conan config set storage.download_cache="{}"'.format(tmpdir))
    os.environ["CONAN_DOCKER_ENTRY_SCRIPT"] = "conan config set storage.download_cache='{}'".format(tmpdir)
    os.environ["CONAN_DOCKER_RUN_OPTIONS"] = "-v '{}':'/tmp/conan'".format(tmpdir)
    os.environ["CONAN_SYSREQUIRES_MODE"] = "enabled"

    path = "recipes"
    filenames = "conanfile.py"
    f = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(filenames):
                path = os.path.dirname(os.path.abspath(file))
                if not "test_package" in root:
                    f.append(path + "/" + root)
    try:
        for i in f:
            gha_hack_copy(i)
            builder = get_builder_default(configuration)
            builder.run()
    except Exception as e:
        gha_hack_removed()
        raise e
    finally:
        gha_hack_removed()


if __name__ == "__main__":
    main()
