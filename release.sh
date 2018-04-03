#!/usr/bin/env bash

if [ $# != 1 ]
then
    echo "Usage:"
    echo "$0 <version>"
    exit 1
fi

VERSION=$1

find . -type f \( -iname \*.py -o -iname \*.md \) -exec sed -i 's/${GAMIFY_BOT_VERSION}/'$VERSION'/g' {} \;

if [ $? -ne 0 ]
then
    echo "Error while changing version."
    exit 1
else
    echo "Successfully set version to $VERSION"
    exit 0
fi
