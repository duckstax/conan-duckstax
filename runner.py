from os import listdir, walk
from os.path import isfile, join
from subprocess import Popen,PIPE

path = "recipes"
filenames = "build.py"

f = []
# for (dirpath, dirnames, filenames) in walk(path):
#    f.extend(filenames)


for root, dirs, files in walk(path):
    for file in files:
        if file.endswith(filenames):
            f.append(join(root, file))

for i in f:
    bashCommand = "python " + i
    process = Popen(bashCommand.split(), stdout=PIPE)
    output, error = process.communicate()
