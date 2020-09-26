#!/bin/bash

set -e
set -x



for path_name in $(find ../recipes -type f | grep "build.py")
do
  cat ${path_name}
done
