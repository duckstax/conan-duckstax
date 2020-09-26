#!/usr/bin/env python3

import json


def generate_ci_jobs() -> str:
    matrix = {"config": [
        {"name": "GCC 4.9 Debug", "compiler": "GCC", "version": "4.9", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "GCC 4.9 Release", "compiler": "GCC", "version": "4.9", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "GCC 5 Debug", "compiler": "GCC", "version": "5", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "GCC 5 Release", "compiler": "GCC", "version": "5", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "GCC 6 Debug", "compiler": "GCC", "version": "6", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "GCC 6 Release", "compiler": "GCC", "version": "6", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "GCC 7 Debug", "compiler": "GCC", "version": "7", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "GCC 7 Release", "compiler": "GCC", "version": "7", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "GCC 8 Debug", "compiler": "GCC", "version": "8", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "GCC 8 Release", "compiler": "GCC", "version": "8", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "GCC 9 Debug", "compiler": "GCC", "version": "9", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "GCC 9 Release", "compiler": "GCC", "version": "9", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "CLANG 3.9 Debug", "compiler": "CLANG", "version": "3.9", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "CLANG 3.9 Release", "compiler": "CLANG", "version": "3.9", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "CLANG 4.0 Debug", "compiler": "CLANG", "version": "4.0", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "CLANG 4.0 Release", "compiler": "CLANG", "version": "4.0", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "CLANG 5.0 Debug", "compiler": "CLANG", "version": "5.0", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "CLANG 5.0 Release", "compiler": "CLANG", "version": "5.0", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "CLANG 6.0 Debug", "compiler": "CLANG", "version": "6.0", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "CLANG 6.0 Release", "compiler": "CLANG", "version": "6.0", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "CLANG 7.0 Debug", "compiler": "CLANG", "version": "7.0", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "CLANG 7.0 Release", "compiler": "CLANG", "version": "7.0", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "CLANG 8 Debug", "compiler": "CLANG", "version": "8", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "CLANG 8 Release", "compiler": "CLANG", "version": "8", "os": "ubuntu-18.04", "buildType": "Release"},
        {"name": "CLANG 9 Debug", "compiler": "CLANG", "version": "9", "os": "ubuntu-18.04", "buildType": "Debug"},
        {"name": "CLANG 9 Release", "compiler": "CLANG", "version": "9", "os": "ubuntu-18.04", "buildType": "Release"}
    ]}

    matrix_string = json.dumps(matrix)
    return matrix_string


def main():
    print(generate_ci_jobs())


if __name__ == '__main__':
    main()
