#!/bin/bash

set -e
set -x


cd ..
for path_name in $(find recipes -type f | grep "build.py")
do
  echo ${path_name}
done
