#!/usr/bin/env python3

import os
import tempfile
from subprocess import PIPE, run

from cpt.printer import Printer

printer = Printer()

import u

class Data:
    def __init__(self, path, file,ap):
        self.path = path
        self.run_file = file
        self.absolut_path=ap


def main():
    printer.print_message("Enabling Conan download cache ...")
    tmpdir = os.path.join(tempfile.gettempdir(), "conan")
    #print(-5)
    os.makedirs(tmpdir, mode=0o777)
    os.chmod(tmpdir, mode=0o777)
    #print(-4)
    os.system('conan config set storage.download_cache="{}"'.format(tmpdir))
    os.environ["CONAN_DOCKER_ENTRY_SCRIPT"] = "conan config set storage.download_cache='{}'".format(tmpdir)
    os.environ["CONAN_DOCKER_RUN_OPTIONS"] = "-v '{}':'/tmp/conan'".format(tmpdir)

    os.environ["CONAN_SYSREQUIRES_MODE"] = "enabled"
    #print(-3)
    path = "recipes"
    #filenames = "build.py"
    filenames = "conanfile.py"
    f = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(filenames):
                path = os.path.dirname(os.path.abspath(file))
                f.append(Data(root, path + "/" + os.path.join(root, file),path+"/"+root))
    #print(-2)
    #print(f)
    for i in f:
    #    print(1)
        #recipe_is_pure_c = u.is_pure_c()
    #    print(2)
        builder = u.get_builder_default( cwd=i.absolut_path)
        builder.run()


if __name__ == "__main__":
    main()
