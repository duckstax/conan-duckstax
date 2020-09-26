#!/bin/bash

set -e
set -x

if [[ "$(uname -s)" == 'Darwin' ]]; then
    if which pyenv > /dev/null; then
        eval "$(pyenv init -)"
    fi
    pyenv activate conan
fi

cd ..
for path_name in $(find recipes -type f | grep "build.py")
do
  python ${path_name}
done

