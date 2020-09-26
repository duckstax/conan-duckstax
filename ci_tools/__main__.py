#!/usr/bin/env python3

import sys
import tempfile
import os
from subprocess import Popen, PIPE, run

from u import printer


def _flush_output():
    sys.stderr.flush()
    sys.stdout.flush()


class Data:
    def __init__(self, path, file):
        self.path = path
        self.run_file = file


def main():
    printer.print_message("Enabling Conan download cache ...")
    tmpdir = os.path.join(tempfile.gettempdir(), "conan")

    os.makedirs(tmpdir, mode=0o777)
    os.chmod(tmpdir, mode=0o777)

    os.system('conan config set storage.download_cache="{}"'.format(tmpdir))
    os.environ["CONAN_DOCKER_ENTRY_SCRIPT"] = "conan config set storage.download_cache='{}'".format(tmpdir)
    os.environ["CONAN_DOCKER_RUN_OPTIONS"] = "-v '{}':'/tmp/conan'".format(tmpdir)

    os.environ["CONAN_SYSREQUIRES_MODE"] = "enabled"

    path = "recipes"
    filenames = "build.py"

    f = []

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(filenames):
                path = os.path.dirname(os.path.abspath(file))
                f.append(Data(root, path+"/"+os.path.join(root, file)))

    for i in f:
        bashCommand = "python3 " + i.run_file
        print(bashCommand)
        bashCommand = bashCommand.split()
        run(bashCommand, stdout=PIPE, cwd=i.path, check=True)


if __name__ == "__main__":
    main()
