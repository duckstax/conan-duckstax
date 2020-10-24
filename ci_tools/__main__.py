#!/usr/bin/env python3

import tempfile

from cpt.printer import Printer

printer = Printer()

import u

gha_hack = True

import os, shutil


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


class Data:
    def __init__(self, path, file, ap):
        self.path = path
        self.run_file = file
        self.absolut_path = ap


def main():
    printer.print_message("Enabling Conan download cache ...")
    tmpdir = os.path.join(tempfile.gettempdir(), "conan")
    # print(-5)
    os.makedirs(tmpdir, mode=0o777)
    os.chmod(tmpdir, mode=0o777)
    # print(-4)
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
                if not "/test_package" in root:
                    f.append(path + "/" + root)

    for i in f:
        # recipe_is_pure_c = u.is_pure_c()
        gha_hack_copy(i)
        builder = u.get_builder_default()
        builder.run()
        gha_hack_removed()


if __name__ == "__main__":
    main()
