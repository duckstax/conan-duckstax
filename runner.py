import sys
import subprocess
import tempfile
import os
from subprocess import Popen, PIPE

from cpt import printer


import utils

def _flush_output():
    sys.stderr.flush()
    sys.stdout.flush()


def main():
    printer.print_message("Enabling Conan download cache ...")

    tmpdir = os.path.join(tempfile.gettempdir(), "conan")

    os.makedirs(tmpdir, mode=0o777)
    os.chmod(tmpdir, mode=0o777)

    os.system('conan config set storage.download_cache="{}"'.format(tmpdir))
    os.environ["CONAN_DOCKER_ENTRY_SCRIPT"] = "conan config set storage.download_cache='{}'".format(tmpdir)
    os.environ["CONAN_DOCKER_RUN_OPTIONS"] = "-v '{}':'/tmp/conan'".format(tmpdir)

    os.environ["CONAN_SYSREQUIRES_MODE"] = "enabled"

    has_custom_build_py, custom_build_py_path =  utils.is_custom_build_py_existing()

    if has_custom_build_py:
        printer.print_message("Custom build.py detected. Executing ...")
        _flush_output()
        subprocess.run(["python", "{}".format(custom_build_py_path)], check=True)
        return

    _flush_output()
    path = "recipes"
    filenames = "build.py"

    f = []

    class Data:
        def __init__(self, path, file):
            self.path = path
            self.run_file = file

    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith(filenames):
                f.append(Data(root, file))

    for i in f:
        bashCommand = "python3 " + i.run_file
        bashCommand = bashCommand.split()
        process = Popen(bashCommand, stdout=PIPE, cwd=i.path)
        output, error = process.communicate()
        print(output)


if __name__ == "__main__":
    main()
