#!/bin/bash

function setup_symlink {
    DIR=$(dirname $1)
    mkdir -p "${DIR}"
    rm -f "$1"
    ln -s "${J2OBJC_BASE_PATH}" "$1"
    echo linked "${J2OBJC_BASE_PATH}" to "$1"
}

J2OBJC_BIN_PATH=$(which j2objc)
if [ $? -ne 0 ]; then
    echo "Cannot find j2objc in PATH; download the latest release at https://github.com/google/j2objc/releases"
    exit 1
fi

J2OBJC_BASE_PATH=$(dirname "${J2OBJC_BIN_PATH}")
echo Found j2objc at: ${J2OBJC_BASE_PATH}
J2OBJC_VERSION=$(j2objc 2>&1 -version)
echo Using version: $J2OBJC_VERSION

setup_symlink j2objc
