#!/bin/bash
# update VERSION to lastest arena-py from repository head

WD=$PWD
TMP=$(mktemp -d)
cd $TMP
git clone --depth=1 https://github.com/arenaxr/arena-py.git &>/dev/null
[[ ! $? -eq 0 ]] && echo "Error cloning" && exit 1
cd arena-py
LATEST=$(git rev-parse --short HEAD)

cd $WD

echo "$LATEST"
echo "$LATEST" > VERSION

rm -fr $TMP