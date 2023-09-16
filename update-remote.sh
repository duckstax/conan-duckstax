#!/bin/bash

# -- variables --
value_to_compare="phbc"
tmp_file=".create_result_tmp"
conan_remote="conan_streamlabs_20"

# -- functions --

function update-remote-conan-server() {
    if [ "$recipes_create_result" == "$value_to_compare" ]
    then
        echo -e "\033[32m remote conan server would be updated \033[0m"
        conan upload "*" --confirm -r $conan_remote
    else
        echo "There are no successfully created packages to update the remote conan."
    fi
}

# -- main execution --

if test -f $tmp_file
then
    source $tmp_file
    update-remote-conan-server
fi
