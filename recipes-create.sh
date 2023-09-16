#!/bin/bash

# -- variables --

conan_remote="duckstax"
result="result.txt"
tmp="tmp.txt"
file="req-seq.txt"
uploaded_packages="uploaded_packages.txt"
error_lib="error.txt"

# -- functions --

# preparation of the "result.txt" file with the packages required for upload

function prepare-result-file() {
        conan search -r=$conan_remote "*" > $tmp
        sed -i 1d $tmp

        for str in $(cat $tmp)
        do
                if grep -q "/" <<< $str; then
                        echo $str >> $uploaded_packages
                fi
        done

        if test -f $uploaded_packages; then
                grep -F -x -v -f $uploaded_packages $file > $result
                rm $uploaded_packages
        else
              cat $file > $result
        fi
        rm $tmp
        sed -i '/^$/d' $result
}

# package name and version as an arg package_name/version --

function create-package() {
    if ! [[ "$1" ]]
    then
        echo " empty package_name/version was passed "
        return
    else
            lib=$1
            delimeter="/"
            package_name=${lib%$delimeter*}
            package_version=${lib#*$delimeter}
            #conan create recipes/"$package_name"/*/ --name $package_name --version $package_version # conan 2.0
            conan create recipes/"$package_name"/*/ lib
    fi
}

function check-result() {
        conan list "*" > $tmp
        sed -i 1d $tmp

        for str in $(cat $tmp)
        do
                if grep -q "/" <<< $str; then
                        echo $str >> $uploaded_packages
                fi
        done

        echo "recipes_create_result=phbc" > .create_result_tmp
        echo -e "\033[31m \nError packages: \033[0m"
        if test -f $uploaded_packages; then
                grep -F -x -v -f $uploaded_packages $result > $error_lib
                rm $uploaded_packages
                sed -i '/^$/d' $error_lib
                cat $error_lib
                if [ -s $error_lib ]
                then
                        echo "recipes_create_result=err" > .create_result_tmp
                fi
        else
                cat $result
                if [ -s $result ]
                then
                        echo "recipes_create_result=err" > .create_result_tmp
                fi

        fi
        rm $tmp
}

# -- main execution --

prepare-result-file

if ! [[ -s ${result} ]]
then
        echo -e "\033[32m -> There were nothing to upload, all the required packages are already uploaded. \033[0m"
        echo "recipes_create_result=ntu" > .create_result_tmp
else
        echo -e "\033[32m Packages would be uploaded: \033[0m"
        cat $result
        echo -e "\033[32m --------------------------- \033[0m"

        for dir in $(cat $result)
        do
                create-package $dir
        done


        echo -e "\033[32m Created packages: \033[0m"
        conan list "*"
        check-result
        echo -e "\033[32m Script finished. \033[0m"
fi
